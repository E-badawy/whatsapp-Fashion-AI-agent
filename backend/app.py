from email.mime import message
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from flask import (
    Flask,
    jsonify,
    request,
    send_from_directory,
)

from werkzeug.utils import secure_filename
import uuid


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"

PRODUCT_UPLOADS = UPLOAD_FOLDER / "products"

STORY_UPLOADS = UPLOAD_FOLDER / "stories"

CUSTOMER_UPLOADS = UPLOAD_FOLDER / "customers"

PRODUCT_UPLOADS.mkdir(parents=True, exist_ok=True)
STORY_UPLOADS.mkdir(parents=True, exist_ok=True)
CUSTOMER_UPLOADS.mkdir(parents=True, exist_ok=True)


FRONTEND_DIR = BASE_DIR.parent / "frontend"
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from services import agent, db, invoice, whatsapp  # noqa: E402

app = Flask(__name__, static_folder=None)

app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
db.init_db()


@app.get("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/<path:path>")
def frontend_assets(path):
    target = FRONTEND_DIR / path
    if target.exists():
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.get("/uploads/<path:filename>")
def uploaded_file(filename):

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename,
    )
    
ALLOWED_IMAGE_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp",
}

def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".",1)[1].lower()
        in ALLOWED_IMAGE_EXTENSIONS
    )

@app.post("/api/upload/product")
def upload_product_image():

    if "image" not in request.files:

        return jsonify(
            {"error":"No image supplied"}
        ),400

    file=request.files["image"]

    if file.filename=="":

        return jsonify(
            {"error":"No image selected"}
        ),400

    if not allowed_file(file.filename):

        return jsonify(
            {"error":"Unsupported file"}
        ),400

    extension=file.filename.rsplit(".",1)[1].lower()

    filename=f"{uuid.uuid4()}.{extension}"

    filepath=PRODUCT_UPLOADS/filename

    file.save(filepath)

    return jsonify({

        "ok":True,

        "filename":filename,

        "url":f"/uploads/products/{filename}"

    })

@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "whatsapp-fashion-agent"})

@app.get("/test-image")
def test_image():

    from services import whatsapp

    whatsapp.send_image(

        "2348069002561",

        "https://borough-plunder-angrily.ngrok-free.dev/uploads/products/d8b6f4b4-2f13-4352-b5bb-ee515be315aa.jpg",

        "Testing image"

    )

    return {"ok": True}

@app.get("/webhook/whatsapp")
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    expected = os.getenv("WHATSAPP_VERIFY_TOKEN", "fashion-agent-verify")

    if mode == "subscribe" and token == expected:
        return challenge or "", 200
    return "Forbidden", 403

def wants_image(message):
    """Return True only for explicit image requests."""

    text = re.sub(r"[^a-z0-9\s]", " ", (message or "").lower()).strip()
    if not text:
        return False

    explicit_phrases = [
        "send image",
        "send picture",
        "send photo",
        "show image",
        "show picture",
        "show photo",
        "show me the image",
        "show me the picture",
        "show me the photo",
        "another image",
        "another picture",
        "another photo",
        "product image",
        "product picture",
        "product photo",
    ]

    if any(phrase in text for phrase in explicit_phrases):
        return True

    if re.search(r"\b(image|picture|photo|pic)\b", text):
        return bool(re.search(r"\b(send|show|see|view|display|open)\b", text))

    return False

@app.post("/webhook/whatsapp")
def whatsapp_webhook():

    payload = request.get_json(silent=True) or {}

    messages = _extract_whatsapp_messages(payload)

    if not messages:
        return jsonify({"ok": True}), 200

    for incoming in messages:

        phone = incoming["from"]
        message = incoming["text"]

        # -----------------------------
        # AI paused?
        # -----------------------------
        if db.is_ai_paused(phone):
            db.log_message(phone, "customer", message)
            continue

        # -----------------------------
        # Send image ONLY for explicit requests
        # -----------------------------
        if wants_image(message):
            products = db.search_products(message)

            if not products:
                history = db.recent_conversation(phone, limit=10)
                for item in reversed(history):
                    if item["role"] != "assistant":
                        continue
                    possible_products = db.search_products(item["message"])
                    if possible_products:
                        products = possible_products
                        break

            if products:
                product = products[0]
                image_urls = product.get("image_urls", [])
                if image_urls:
                    image_url = image_urls[0]
                    if image_url.startswith("/"):
                        image_url = os.getenv("PUBLIC_BASE_URL", "") + image_url
                    whatsapp.send_image(
                        phone,
                        image_url,
                        f"{product['name']} - ₦{product['price']:,}",
                    )

        # -----------------------------
        # Generate AI reply
        # -----------------------------
        reply = agent.generate_reply(
            phone,
            message
        )

        # -----------------------------
        # Send text
        # -----------------------------
        whatsapp.send_text(
            phone,
            reply
        )

    return jsonify({"ok": True}), 200


@app.get("/api/products")
def list_products():
    query = request.args.get("q", "").strip().lower()
    products = db.list_products()
    if query:
        filtered = [
            product
            for product in products
            if query in (product.get("sku", "") + " " + product.get("name", "") + " " + product.get("category", "") + " " + product.get("description", "") + " " + " ".join(product.get("colors", [])) + " " + " ".join(product.get("sizes", []))).lower()
        ]
        return jsonify(filtered)
    return jsonify(products)


@app.put("/api/products/<sku>")
def update_product(sku):
    data = request.get_json(silent=True) or {}
    updated = db.update_product(sku, data)
    if not updated:
        return jsonify({"error": "No valid fields provided"}), 400
    return jsonify({"ok": True, "product": db.get_product(sku)})


@app.delete("/api/products/<sku>")
def delete_product(sku):

    if not db.get_product(sku):
        return jsonify({"error": "Product not found"}), 404

    db.delete_product(sku)

    return jsonify(
        {
            "ok": True,
            "message": "Product deleted",
        }
    )

@app.patch("/api/products/<sku>/stock")
def update_stock(sku):

    data = request.get_json(silent=True) or {}

    if "stock" not in data:
        return jsonify(
            {"error": "stock is required"}
        ), 400

    db.update_stock(sku, int(data["stock"]))

    return jsonify(
        {
            "ok": True,
            "product": db.get_product(sku),
        }
    )
    
@app.patch("/api/products/<sku>/featured")
def feature_product(sku):

    data = request.get_json(silent=True) or {}

    featured = bool(data.get("featured", True))

    db.feature_product(sku, featured)

    return jsonify(
        {
            "ok": True,
            "product": db.get_product(sku),
        }
    )


@app.post("/api/products")
def add_product():
    data = request.get_json(silent=True) or {}
    required = ["sku", "name", "category", "price"]
    missing = [field for field in required if not data.get(field)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    db.create_product(data)
    return jsonify({"ok": True}), 201


@app.get("/api/stories")
def stories():
    return jsonify(db.list_story_items())


@app.post("/api/stories")
def add_story():
    data = request.get_json(silent=True) or {}
    if not data.get("title"):
        return jsonify({"error": "title is required"}), 400
    story_id = db.create_story_item(data)
    return jsonify({"ok": True, "id": story_id}), 201


@app.get("/api/orders")
def orders():
    query = request.args.get("q", "").strip().lower()
    orders = db.list_orders()
    if query:
        filtered = [
            order
            for order in orders
            if query in (order.get("customer_name", "") + " " + order.get("customer_phone", "") + " " + order.get("status", "") + " " + order.get("payment_status", "") + " " + str(order.get("id", ""))).lower()
        ]
        return jsonify(filtered)
    return jsonify(orders)


@app.patch("/api/orders/<int:order_id>")
def update_order(order_id):
    data = request.get_json(silent=True) or {}
    order = db.update_order_status(
        order_id,
        data.get("status"),
        payment_status=data.get("payment_status"),
        notes=data.get("notes"),
    )
    if not order:
        return jsonify({"error": "order not found"}), 404
    return jsonify({"ok": True, "order": order})


@app.get("/api/conversations")
def conversations():
    return jsonify(db.list_conversation_threads())


@app.get("/api/conversations/<phone>")
def conversation_messages(phone):
    return jsonify(db.list_conversation_messages(phone))


@app.post("/api/conversations/<phone>/pause")
def pause_conversation(phone):
    customer = db.set_ai_paused(phone, True)
    return jsonify({"ok": True, "customer": customer})


@app.post("/api/conversations/<phone>/resume")
def resume_conversation(phone):
    customer = db.set_ai_paused(phone, False)
    return jsonify({"ok": True, "customer": customer})


@app.post("/api/conversations/<phone>/reply")
def manual_reply(phone):
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "message is required"}), 400
    db.set_ai_paused(phone, True)
    db.log_message(phone, "staff", message)
    result = whatsapp.send_text(phone, message)
    return jsonify({"ok": True, "delivery": result})


@app.post("/api/orders")
def add_order():
    data = request.get_json(silent=True) or {}
    if not data.get("customer_phone") or not data.get("items"):
        return jsonify({"error": "customer_phone and items are required"}), 400
    subtotal = sum(int(item.get("price", 0)) * int(item.get("quantity", 1)) for item in data["items"])
    delivery_fee = int(data.get("delivery_fee", 0))
    order_id = db.create_order({**data, "subtotal": subtotal, "total": subtotal + delivery_fee})
    order = db.get_order(order_id)
    return jsonify({"ok": True, "id": order_id, "invoice": invoice.generate_invoice(order)}), 201


@app.post("/api/simulate-chat")
def simulate_chat():
    data = request.get_json(silent=True) or {}
    phone = data.get("phone") or "unknown"
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "message is required"}), 400

    if wants_image(message):
        products = db.search_products(message)
        if not products:
            history = db.recent_conversation(phone, limit=10)
            for item in reversed(history):
                if item["role"] != "assistant":
                    continue
                possible_products = db.search_products(item["message"])
                if possible_products:
                    products = possible_products
                    break

        if products:
            product = products[0]
            image_urls = product.get("image_urls", [])
            if image_urls:
                image_url = image_urls[0]
                if image_url.startswith("/"):
                    image_url = os.getenv("PUBLIC_BASE_URL", "") + image_url
                return jsonify(
                    {
                        "ok": True,
                        "reply": f"{product['name']} - ₦{product['price']:,}",
                        "image_url": image_url,
                        "caption": f"{product['name']} - ₦{product['price']:,}",
                    }
                )

    reply = agent.generate_reply(phone, message)
    return jsonify({"ok": True, "reply": reply})


@app.get("/api/orders/<int:order_id>/invoice")
def order_invoice(order_id):
    order = db.get_order(order_id)
    if not order:
        return jsonify({"error": "order not found"}), 404
    return jsonify({"invoice": invoice.generate_invoice(order)})


def _extract_whatsapp_messages(payload):
    parsed = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                text = ""
                if message.get("type") == "text":
                    text = message.get("text", {}).get("body", "")
                elif message.get("type") == "interactive":
                    interactive = message.get("interactive", {})
                    text = (
                        interactive.get("button_reply", {}).get("title")
                        or interactive.get("list_reply", {}).get("title")
                        or ""
                    )
                if text:
                    parsed.append({"from": message.get("from", ""), "text": text})
    return parsed


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG") == "1")

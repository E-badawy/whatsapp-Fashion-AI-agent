import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from services import agent, db, whatsapp  # noqa: E402

app = Flask(__name__, static_folder=None)
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


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "whatsapp-fashion-agent"})


@app.get("/webhook/whatsapp")
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    expected = os.getenv("WHATSAPP_VERIFY_TOKEN", "fashion-agent-verify")

    if mode == "subscribe" and token == expected:
        return challenge or "", 200
    return "Forbidden", 403


@app.post("/webhook/whatsapp")
def whatsapp_webhook():
    payload = request.get_json(silent=True) or {}
    messages = _extract_whatsapp_messages(payload)

    for incoming in messages:
        reply = agent.generate_reply(incoming["from"], incoming["text"])
        whatsapp.send_text(incoming["from"], reply)

    return jsonify({"ok": True, "processed": len(messages)})


@app.post("/api/simulate-chat")
def simulate_chat():
    data = request.get_json(silent=True) or {}
    phone = data.get("phone", "2348000000000")
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "message is required"}), 400
    reply = agent.generate_reply(phone, message)
    return jsonify({"reply": reply})


@app.get("/api/products")
def products():
    return jsonify(db.list_products())


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
    return jsonify(db.list_orders())


@app.post("/api/orders")
def add_order():
    data = request.get_json(silent=True) or {}
    if not data.get("customer_phone") or not data.get("items"):
        return jsonify({"error": "customer_phone and items are required"}), 400
    subtotal = sum(int(item.get("price", 0)) * int(item.get("quantity", 1)) for item in data["items"])
    delivery_fee = int(data.get("delivery_fee", 0))
    order_id = db.create_order({**data, "subtotal": subtotal, "total": subtotal + delivery_fee})
    return jsonify({"ok": True, "id": order_id}), 201


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

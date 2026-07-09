import os
import re

from . import business, db, meta_catalog


SYSTEM_PROMPT = """
You are a WhatsApp sales assistant for a Cigma Fashion Line.
Your job is to answer product questions, recommend outfits, collect order details, and provide warm customer service.
Rules:
- Never invent prices, stock, sizes, colors, policies, or delivery timelines.
- Use only the product and story context provided.
- If details are missing, ask one clear follow-up question.
- If a customer wants to order, collect product, size, color, quantity, name, and delivery address.
- After the customer confirms an order summary, share configured bank transfer details and ask them to send payment receipt before processing.
- Do not ask for payment until the product, quantity, size/color where applicable, customer name, delivery area/address, and order total are clear.
- Escalate to a human for complaints, refunds, custom tailoring, payment disputes, or low confidence.
- Keep WhatsApp replies concise, friendly, and easy to act on.
- You are connected to backend tools that can send product images.
- Never say you are text-only.
- Never say you cannot send images.
- If the customer asks to see a product or asks for the image again, assume the backend will send the image automatically.
- Simply respond naturally, for example:
  "Certainly! Here's the product image."
"""


def money(amount, currency="NGN"):
    return f"{currency} {int(amount):,}"


def _extract_order_intent(message):
    text = message.lower()
    return any(word in text for word in ("buy", "order", "deliver", "checkout", "Cost", "i want", "reserve"))


def _extract_story_intent(message):
    text = message.lower()
    return any(word in text for word in ("story", "status", "look", "posted", "today"))


def _is_catalog_request(message):
    text = message.lower()
    inventory_phrases = (
        "what products do you have",
        "what products are available",
        "show me your products",
        "show me the catalog",
        "what do you sell",
        "what items do you have",
        "all products",
        "catalog",
        "inventory",
        "available products",
    )
    return any(phrase in text for phrase in inventory_phrases)


def _format_product(product):

    name = product.get("name", "Unknown Product")

    sku = product.get("sku", product.get("retailer_id", ""))

    price = product.get("price", 0)

    currency = product.get("currency", "NGN")

    sizes = ", ".join(product.get("sizes", [])) or "Not specified"

    colors = ", ".join(product.get("colors", [])) or "Not specified"

    stock = product.get("stock", "Available")

    description = product.get("description", "")

    return (
        f"{name} ({sku})\n"
        f"Price: {money(price, currency)}\n"
        f"Sizes: {sizes}\n"
        f"Colors: {colors}\n"
        f"Stock: {stock}\n"
        f"{description}"
    )


def _fallback_reply(message):
    story_items = db.list_story_items()
    query = message.strip()
    products = db.list_products() if _is_catalog_request(message) else db.search_products(query)

    if _is_catalog_request(message) and products:
        lines = ["Here are the products I currently have:"]
        for product in products[:5]:
            lines.append(
                f"- {product['name']} ({product['sku']}) - {money(product['price'], product.get('currency', 'NGN'))}"
            )
        lines.append("Would you like details on any of these products?")
        return "\n".join(lines)

    if _extract_story_intent(message) and story_items:
        lines = ["Here are the current story items I can help with:"]
        for idx, story in enumerate(story_items[:5], start=1):
            price = story.get("product_price")
            price_text = f" - {money(price)}" if price else ""
            lines.append(f"{idx}. {story['title']}: {story.get('product_name') or story['caption']}{price_text}")
        lines.append("Reply with the item name or number, and I'll confirm size, color, and availability.")
        return "\n".join(lines)

    if products:
        if len(products) == 1 or re.search(r"\b(price|size|color|detail|fabric|stock)\b", message.lower()):
            product = products[0]
            next_step = "Would you like me to reserve it? Please send your size, color, quantity, name, and delivery area."
            return f"{_format_product(product)}\n\n{next_step}"
        lines = ["I found these options:"]
        for product in products[:5]:
            lines.append(f"- {product['name']} ({product['sku']}) - {money(product['price'], product.get('currency', 'NGN'))}")
        lines.append("Which one should I show details for?")
        return "\n".join(lines)

    if _extract_order_intent(message):
        return (
            "I can help with your order. Please send the item name or SKU, preferred size, color, quantity, "
            "your name, and delivery area. Once we confirm the summary, I will share payment details and ask for your receipt."
        )

    featured = [product for product in db.list_products() if product.get("is_featured")]
    if featured:
        options = "\n".join(
            f"- {product['name']} ({product['sku']}) - {money(product['price'], product.get('currency', 'NGN'))}"
            for product in featured[:3]
        )
        return f"Welcome. I can help you find items, check sizes, and start an order.\n\nFeatured now:\n{options}"

    return "Welcome. Send me a product name, story item, size, color, or order request and I'll help right away."


def generate_reply(phone, message):
    db.log_message(phone, "customer", message)

    if _is_catalog_request(message):
        reply = _fallback_reply(message)
        db.log_message(phone, "assistant", reply)
        return reply

    context_products = (
    db.list_products()
    if _is_catalog_request(message)
    else db.search_products(message)
    )
    # If SQLite finds nothing, search Meta Catalog
    if not context_products:
        context_products = meta_catalog.search_products(message)
    context_stories = db.list_story_items()[:5]
    history = db.recent_conversation(phone)
    business_context = business.business_context_text()

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()

    if not api_key:
        reply = _fallback_reply(message)
        db.log_message(phone, "assistant", reply)
        return reply

    try:
        from groq import Groq
    except ImportError:
        reply = (
            "Groq is configured, but the Python package is not installed yet. "
            "Please run `pip install -r requirements.txt`, then try again."
        )
        db.log_message(phone, "assistant", reply)
        return reply

    client = Groq(api_key=api_key)
    product_context = "\n\n".join(_format_product(product) for product in context_products) or "No matching products."
    story_context_lines = []
    for story in context_stories:
        linked_product = db.get_product(story.get("product_sku")) if story.get("product_sku") else None
        line = f"- {story['title']}: {story.get('caption', '')}"
        if linked_product:
            line += (
                f" Linked product: {linked_product['name']} ({linked_product['sku']}), "
                f"{money(linked_product['price'], linked_product.get('currency', 'NGN'))}, "
                f"sizes {', '.join(linked_product.get('sizes', []))}, "
                f"colors {', '.join(linked_product.get('colors', []))}, "
                f"stock {linked_product['stock']}."
            )
        else:
            line += " Linked product: unlinked."
        story_context_lines.append(line)
    story_context = "\n".join(story_context_lines) or "No active story items."
    history_context = "\n".join(f"{item['role']}: {item['message']}" for item in history[-6:])

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Conversation history:\n{history_context}\n\n"
                    f"Business information:\n{business_context}\n\n"
                    f"Relevant products:\n{product_context}\n\n"
                    f"Story items:\n{story_context}\n\n"
                    f"Customer message: {message}"
                ),
            },
        ],
        temperature=0.3,
    )
    reply = response.choices[0].message.content.strip()
    db.log_message(phone, "assistant", reply)
    return reply

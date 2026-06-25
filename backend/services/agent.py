import os
import re

from . import db


SYSTEM_PROMPT = """
You are a WhatsApp sales assistant for a fashion business.
Your job is to answer product questions, recommend outfits, collect order details, and provide warm customer service.
Rules:
- Never invent prices, stock, sizes, colors, policies, or delivery timelines.
- Use only the product and story context provided.
- If details are missing, ask one clear follow-up question.
- If a customer wants to order, collect product, size, color, quantity, name, and delivery address.
- Escalate to a human for complaints, refunds, custom tailoring, payment disputes, or low confidence.
- Keep WhatsApp replies concise, friendly, and easy to act on.
"""


def money(amount, currency="NGN"):
    return f"{currency} {int(amount):,}"


def _extract_order_intent(message):
    text = message.lower()
    return any(word in text for word in ("buy", "order", "deliver", "checkout", "i want", "reserve"))


def _extract_story_intent(message):
    text = message.lower()
    return any(word in text for word in ("story", "status", "look", "posted", "today"))


def _format_product(product):
    sizes = ", ".join(product.get("sizes", [])) or "ask for available sizes"
    colors = ", ".join(product.get("colors", [])) or "ask for available colors"
    return (
        f"{product['name']} ({product['sku']})\n"
        f"Price: {money(product['price'], product.get('currency', 'NGN'))}\n"
        f"Sizes: {sizes}\n"
        f"Colors: {colors}\n"
        f"Stock: {product['stock']} available\n"
        f"{product.get('description', '')}"
    )


def _fallback_reply(message):
    story_items = db.list_story_items()
    query = message.strip()
    products = db.search_products(query)

    if _extract_story_intent(message) and story_items:
        lines = ["Here are the current story items I can help with:"]
        for idx, story in enumerate(story_items[:5], start=1):
            price = story.get("product_price")
            price_text = f" - {money(price)}" if price else ""
            lines.append(f"{idx}. {story['title']}: {story.get('product_name') or story['caption']}{price_text}")
        lines.append("Reply with the item name or number, and I’ll confirm size, color, and availability.")
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
            "your name, and delivery area."
        )

    featured = [product for product in db.list_products() if product.get("is_featured")]
    if featured:
        options = "\n".join(
            f"- {product['name']} ({product['sku']}) - {money(product['price'], product.get('currency', 'NGN'))}"
            for product in featured[:3]
        )
        return f"Welcome. I can help you find items, check sizes, and start an order.\n\nFeatured now:\n{options}"

    return "Welcome. Send me a product name, SKU, story item, size, color, or order request and I’ll help right away."


def generate_reply(phone, message):
    db.log_message(phone, "customer", message)
    context_products = db.search_products(message)
    context_stories = db.list_story_items()[:5]
    history = db.recent_conversation(phone)

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
    story_context = "\n".join(
        f"- {story['title']}: {story.get('caption', '')} SKU={story.get('product_sku') or 'unlinked'}"
        for story in context_stories
    ) or "No active story items."
    history_context = "\n".join(f"{item['role']}: {item['message']}" for item in history[-6:])

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Conversation history:\n{history_context}\n\n"
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

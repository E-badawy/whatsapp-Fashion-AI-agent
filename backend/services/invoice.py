from datetime import datetime

from . import business


def money(amount, currency="NGN"):
    return f"{currency} {int(amount):,}"


def generate_invoice(order):
    profile = business.business_profile()
    payment = business.payment_text()
    created_at = order.get("created_at") or datetime.utcnow().isoformat(timespec="seconds")
    lines = [
        f"INVOICE #{order['id']}",
        profile["name"],
        f"Date: {created_at}",
        "",
        "Customer",
        f"Name: {order.get('customer_name') or 'Not provided'}",
        f"Phone: {order.get('customer_phone') or 'Not provided'}",
        f"Address: {order.get('address') or 'Not provided'}",
        "",
        "Items",
    ]
    for item in order.get("items", []):
        name = item.get("name") or item.get("sku") or "Item"
        quantity = int(item.get("quantity", 1))
        price = int(item.get("price", 0))
        lines.append(f"- {quantity} x {name}: {money(price * quantity)}")
    lines.extend(
        [
            "",
            f"Subtotal: {money(order.get('subtotal', 0))}",
            f"Delivery fee: {money(order.get('delivery_fee', 0))}",
            f"Total: {money(order.get('total', 0))}",
            f"Payment status: {order.get('payment_status', 'unpaid')}",
            f"Order status: {order.get('status', 'pending')}",
            "",
            payment,
        ]
    )
    return "\n".join(lines)

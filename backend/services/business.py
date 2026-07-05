import os

def business_profile():
    return {
        "name": os.getenv(
            "BUSINESS_NAME",
            "Cigma General Solutions"
        ).strip(),

        "owner": os.getenv(
            "BUSINESS_OWNER",
            "Badawi Aminu Muhammed"
        ).strip(),

        "owner_role": os.getenv(
            "BUSINESS_OWNER_ROLE",
            "Founder and Creative Director"
        ).strip(),

        "description": os.getenv(
            "BUSINESS_DESCRIPTION",
            "A fashion and lifestyle business helping customers choose quality clothing and accessories."
        ).strip(),

        "location": os.getenv(
            "BUSINESS_LOCATION",
            "Kaduna, Nigeria"
        ).strip(),

        "full_address": os.getenv(
            "BUSINESS_FULL_ADDRESS",
            ""
        ).strip(),

        "google_maps": os.getenv(
            "BUSINESS_GOOGLE_MAPS",
            ""
        ).strip(),

        "phone": os.getenv(
            "BUSINESS_PHONE",
            ""
        ).strip(),

        "whatsapp": os.getenv(
            "BUSINESS_WHATSAPP",
            ""
        ).strip(),

        "email": os.getenv(
            "BUSINESS_EMAIL",
            "Cigmageneralsolution@gmail.com"
        ).strip(),

        "hours": os.getenv(
            "BUSINESS_HOURS",
            "Monday - Saturday, 9:00 AM - 7:00 PM"
        ).strip(),

        "delivery_policy": os.getenv(
            "BUSINESS_DELIVERY_POLICY",
            "Delivery fee and timeline are confirmed after the customer shares their location."
        ).strip(),

        "return_policy": os.getenv(
            "BUSINESS_RETURN_POLICY",
            "Returns and exchanges are handled by a member of staff."
        ).strip(),

        "contact_name": os.getenv(
            "BUSINESS_CONTACT_NAME",
            "Badawi Aminu Muhammed"
        ).strip(),
    }

def payment_profile():
    return {
        "bank_name": os.getenv("PAYMENT_BANK_NAME", "Fidelity Bank").strip(),
        "account_number": os.getenv("PAYMENT_ACCOUNT_NUMBER", "5333801204").strip(),
        "account_name": os.getenv("PAYMENT_ACCOUNT_NAME", "Cigma General Solutions").strip(),
        "instructions": os.getenv(
            "PAYMENT_INSTRUCTIONS",
            "After payment, please send your receipt here so we can confirm and process your order.",
        ).strip(),
    }


def payment_text():
    payment = payment_profile()
    if not payment["bank_name"] or not payment["account_number"]:
        return "Payment details are not configured yet. A staff member will confirm payment instructions."
    lines = [
        "Payment details:",
        f"Bank: {payment['bank_name']}",
        f"Account number: {payment['account_number']}",
    ]
    if payment["account_name"]:
        lines.append(f"Account name: {payment['account_name']}")
    lines.append(payment["instructions"])
    return "\n".join(lines)

def business_context_text():
    profile = business_profile()
    payment = payment_profile()

    parts = [
        f"Business name: {profile['name']}",

        f"Business owner: {profile['owner']}",

        f"Owner role: {profile['owner_role']}",

        f"Business description: {profile['description']}",

        f"Location: {profile['location']}",

        f"Full address: {profile['full_address']}",

        f"Business phone: {profile['phone']}",

        f"Business WhatsApp: {profile['whatsapp']}",

        f"Business email: {profile['email']}",

        f"Google Maps: {profile['google_maps']}",

        f"Business hours: {profile['hours']}",

        f"Delivery policy: {profile['delivery_policy']}",

        f"Return policy: {profile['return_policy']}",
    ]
    
    if profile["contact_name"]:
        parts.append(
            f"Human contact/personality reference: {profile['contact_name']}"
        )

    if payment["bank_name"] and payment["account_number"]:
        parts.append(
            "Payment instruction: when an order summary is confirmed, share the configured bank details and ask the customer to send receipt before processing."
        )
        parts.append(payment_text())

    return "\n".join(parts)
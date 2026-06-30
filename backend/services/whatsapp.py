import os

import requests


def send_text(to_phone, text):
    token = os.getenv("WHATSAPP_ACCESS_TOKEN", "EAAYZA9aPNzOUBR7x08ZAGw9ChC862gQZCzsZC2jTRO4j9CZCmJlM7PGqyKhdcEOGYylSxukXjZAJFMEmcL8lv4ht9ascKvjzKmQcZBP8jUlGKreixg7W1M64m5i2diURnUD4ZCZCZBxJpSRcjsYj3C25P8V8lmWoRxc6oc8kCeWoZBQiIWOABo5kFx83qGlZCut9ZCSPGSAZDZD").strip()
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "1195845743610160").strip()

    if not token or not phone_number_id:
        print(f"[whatsapp dry-run] to={to_phone} text={text}")
        return {"dry_run": True, "to": to_phone, "text": text}

    url = f"https://graph.facebook.com/v20.0/{phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"preview_url": False, "body": text},
    }
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers, timeout=20)
    response.raise_for_status()
    return response.json()

def send_image(to_phone, image_url, caption=""):

    token = os.getenv("WHATSAPP_ACCESS_TOKEN").strip()
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID").strip()

    url = f"https://graph.facebook.com/v20.0/{phone_number_id}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "image",
        "image": {
            "link": image_url,
            "caption": caption
        }
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=20
    )

    response.raise_for_status()

    return response.json()
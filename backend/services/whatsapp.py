import os
import tempfile
from pathlib import Path
import requests


def send_text(to_phone, text):
    token = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()

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

    token = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()

    if not token or not phone_number_id:
        print(f"[whatsapp dry-run] to={to_phone} image={image_url} caption={caption}")
        return {"dry_run": True, "to": to_phone, "image": image_url, "caption": caption}

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

def download_media(media_id):
    """
    Downloads a WhatsApp media file (voice note, image, etc.)
    and returns the local file path.
    """

    token = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()

    if not token:
        raise RuntimeError("Missing WHATSAPP_ACCESS_TOKEN")

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Step 1: Ask Meta for the temporary download URL
    meta_url = f"https://graph.facebook.com/v20.0/{media_id}"

    response = requests.get(
        meta_url,
        headers=headers,
        timeout=20,
    )

    response.raise_for_status()

    media_info = response.json()

    download_url = media_info["url"]

    # Step 2: Download the actual media
    media = requests.get(
        download_url,
        headers=headers,
        timeout=60,
    )

    media.raise_for_status()

    # Step 3: Save to a temporary file
    suffix = ".ogg"

    if "audio/ogg" not in media.headers.get("Content-Type", ""):
        content_type = media.headers.get("Content-Type", "")
        if "/" in content_type:
            suffix = "." + content_type.split("/")[-1]

    temp = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
    )

    temp.write(media.content)
    temp.close()

    return Path(temp.name)
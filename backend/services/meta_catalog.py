import os
import requests

GRAPH_VERSION = "v23.0"


def search_products(query=""):

    token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    catalog_id = os.getenv("META_CATALOG_ID")

    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{catalog_id}/products"

    params = {
        "access_token": token,
        "fields": "id,name,price,image_url,retailer_id,availability"
    }

    response = requests.get(url, params=params, timeout=20)

    response.raise_for_status()

    products = response.json().get("data", [])

    if not query:
        return products

    query = query.lower()

    return [
        p
        for p in products
        if query in p.get("name", "").lower()
    ]
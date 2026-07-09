import os
import requests

GRAPH_VERSION = "v23.0"


def search_products(query=""):

    token = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
    catalog_id = os.getenv("META_CATALOG_ID", "").strip()

    # If Meta is not configured,
    # silently fall back to SQLite.
    if not token or not catalog_id:
        return []

    url = (
        f"https://graph.facebook.com/"
        f"{GRAPH_VERSION}/{catalog_id}/products"
    )

    params = {
        "access_token": token,
        "fields": (
            "id,"
            "name,"
            "price,"
            "image_url,"
            "retailer_id,"
            "availability"
        ),
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=20,
        )

    except Exception as e:

        print("Meta Catalog Connection Error:")
        print(e)

        return []

    if not response.ok:

        print("Meta Catalog API Error")
        print("Status:", response.status_code)
        print(response.text)

        # Never crash the chatbot.
        # Just return no products.
        return []

    try:

        products = response.json().get("data", [])

    except Exception:

        return []

    if not query:
        return products

    query = query.lower()

    results = []

    for product in products:

        name = product.get("name", "").lower()

        retailer = product.get("retailer_id", "").lower()

        if (
            query in name
            or query in retailer
        ):
            results.append(product)

    return results

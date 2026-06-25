import json
import re
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "fashion_agent.db"


def get_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row):
    if row is None:
        return None
    data = dict(row)
    for key in ("sizes", "colors", "image_urls", "items"):
        if key in data and isinstance(data[key], str):
            try:
                data[key] = json.loads(data[key])
            except json.JSONDecodeError:
                data[key] = []
    return data


def init_db():
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price INTEGER NOT NULL,
                currency TEXT NOT NULL DEFAULT 'NGN',
                sizes TEXT NOT NULL DEFAULT '[]',
                colors TEXT NOT NULL DEFAULT '[]',
                stock INTEGER NOT NULL DEFAULT 0,
                description TEXT NOT NULL DEFAULT '',
                care TEXT NOT NULL DEFAULT '',
                image_urls TEXT NOT NULL DEFAULT '[]',
                source TEXT NOT NULL DEFAULT 'catalog',
                is_featured INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS story_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                caption TEXT NOT NULL DEFAULT '',
                product_sku TEXT,
                image_url TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(product_sku) REFERENCES products(sku)
            );

            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL DEFAULT '',
                address TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_phone TEXT NOT NULL,
                customer_name TEXT NOT NULL DEFAULT '',
                address TEXT NOT NULL DEFAULT '',
                items TEXT NOT NULL,
                subtotal INTEGER NOT NULL,
                delivery_fee INTEGER NOT NULL DEFAULT 0,
                total INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                payment_status TEXT NOT NULL DEFAULT 'unpaid',
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT NOT NULL,
                role TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        existing = conn.execute("SELECT COUNT(*) AS count FROM products").fetchone()["count"]
        if existing == 0:
            seed_products(conn)


def seed_products(conn):
    samples = [
        {
            "sku": "DRS-001",
            "name": "Emerald Satin Maxi Dress",
            "category": "Dresses",
            "price": 45000,
            "sizes": ["S", "M", "L"],
            "colors": ["emerald", "green"],
            "stock": 8,
            "description": "A flowing satin maxi dress with a soft drape, best for dinners, weddings, and evening events.",
            "care": "Hand wash cold. Steam on low heat.",
            "image_urls": ["https://images.unsplash.com/photo-1595777457583-95e059d581b8"],
            "source": "story",
            "is_featured": 1,
        },
        {
            "sku": "KFT-014",
            "name": "Ivory Embroidered Kaftan",
            "category": "Kaftans",
            "price": 38000,
            "sizes": ["M", "L", "XL"],
            "colors": ["ivory", "cream"],
            "stock": 5,
            "description": "Relaxed kaftan with neckline embroidery and breathable fabric for elegant casual wear.",
            "care": "Dry clean preferred.",
            "image_urls": ["https://images.unsplash.com/photo-1612336307429-8a898d10e223"],
            "source": "catalog",
            "is_featured": 1,
        },
        {
            "sku": "BAG-009",
            "name": "Mini Structured Handbag",
            "category": "Accessories",
            "price": 22000,
            "sizes": ["One size"],
            "colors": ["black", "tan"],
            "stock": 12,
            "description": "Compact structured handbag with detachable strap and gold-tone hardware.",
            "care": "Wipe with a soft dry cloth.",
            "image_urls": ["https://images.unsplash.com/photo-1594223274512-ad4803739b7c"],
            "source": "catalog",
            "is_featured": 0,
        },
    ]
    for product in samples:
        create_product(product, conn=conn)
    conn.execute(
        """
        INSERT INTO story_items (title, caption, product_sku, image_url)
        VALUES (?, ?, ?, ?)
        """,
        (
            "Today Look 1",
            "Emerald satin dress from today's story. Great for evening events.",
            "DRS-001",
            samples[0]["image_urls"][0],
        ),
    )


def create_product(product, conn=None):
    owns_conn = conn is None
    conn = conn or get_connection()
    try:
        conn.execute(
            """
            INSERT INTO products
            (sku, name, category, price, currency, sizes, colors, stock, description, care, image_urls, source, is_featured)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product["sku"],
                product["name"],
                product.get("category", "Fashion"),
                int(product.get("price", 0)),
                product.get("currency", "NGN"),
                json.dumps(product.get("sizes", [])),
                json.dumps(product.get("colors", [])),
                int(product.get("stock", 0)),
                product.get("description", ""),
                product.get("care", ""),
                json.dumps(product.get("image_urls", [])),
                product.get("source", "catalog"),
                1 if product.get("is_featured") else 0,
            ),
        )
        if owns_conn:
            conn.commit()
    finally:
        if owns_conn:
            conn.close()


def list_products():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM products ORDER BY created_at DESC").fetchall()
        return [row_to_dict(row) for row in rows]


def search_products(query):
    terms = f"%{query.lower()}%"
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM products
            WHERE lower(sku) LIKE ?
               OR lower(name) LIKE ?
               OR lower(category) LIKE ?
               OR lower(description) LIKE ?
               OR lower(colors) LIKE ?
            ORDER BY is_featured DESC, stock DESC
            LIMIT 8
            """,
            (terms, terms, terms, terms, terms),
        ).fetchall()
        direct_matches = [row_to_dict(row) for row in rows]

        tokens = [
            token
            for token in re.findall(r"[a-z0-9]+", query.lower())
            if len(token) >= 3
            and token not in {"how", "much", "have", "with", "that", "this", "your", "from", "want"}
        ]
        if not tokens:
            return direct_matches

        all_rows = conn.execute("SELECT * FROM products").fetchall()
        scored = []
        for row in all_rows:
            product = row_to_dict(row)
            haystack = " ".join(
                [
                    product.get("sku", ""),
                    product.get("name", ""),
                    product.get("category", ""),
                    product.get("description", ""),
                    " ".join(product.get("sizes", [])),
                    " ".join(product.get("colors", [])),
                ]
            ).lower()
            score = sum(1 for token in tokens if token in haystack)
            if score:
                scored.append((score, product.get("is_featured", 0), product.get("stock", 0), product))

        scored.sort(reverse=True, key=lambda item: (item[0], item[1], item[2]))
        merged = []
        seen = set()
        for product in direct_matches + [item[3] for item in scored]:
            if product["sku"] not in seen:
                seen.add(product["sku"])
                merged.append(product)
        return merged[:8]


def get_product(sku):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM products WHERE sku = ?", (sku,)).fetchone()
        return row_to_dict(row)


def list_story_items():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT story_items.*, products.name AS product_name, products.price AS product_price
            FROM story_items
            LEFT JOIN products ON products.sku = story_items.product_sku
            ORDER BY story_items.created_at DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]


def create_story_item(story):
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO story_items (title, caption, product_sku, image_url, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                story["title"],
                story.get("caption", ""),
                story.get("product_sku") or None,
                story.get("image_url", ""),
                story.get("status", "active"),
            ),
        )
        return cur.lastrowid


def create_order(order):
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO orders
            (customer_phone, customer_name, address, items, subtotal, delivery_fee, total, status, payment_status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order["customer_phone"],
                order.get("customer_name", ""),
                order.get("address", ""),
                json.dumps(order["items"]),
                int(order["subtotal"]),
                int(order.get("delivery_fee", 0)),
                int(order["total"]),
                order.get("status", "pending"),
                order.get("payment_status", "unpaid"),
                order.get("notes", ""),
            ),
        )
        return cur.lastrowid


def list_orders():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall()
        return [row_to_dict(row) for row in rows]


def log_message(phone, role, message):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO conversations (phone, role, message) VALUES (?, ?, ?)",
            (phone, role, message),
        )


def recent_conversation(phone, limit=8):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT role, message FROM conversations
            WHERE phone = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (phone, limit),
        ).fetchall()
        return [dict(row) for row in reversed(rows)]

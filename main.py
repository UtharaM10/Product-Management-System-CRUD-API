
from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
DATABASE = "products.db"


def connect_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def create_database():
    connection = connect_db()
    connection.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL CHECK(price > 0),
            category TEXT NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
            created_at TEXT NOT NULL
        )
    """)

    count = connection.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]

    if count == 0:
        sample_products = [
            ("Wireless Mouse", "Bluetooth Wireless Mouse", 799, "Electronics", 25),
            ("Keyboard", "USB wired keyboard", 999, "Electronics", 15),
            ("Headphones", "Wireless over-ear headphones", 1499, "Electronics", 10),
            ("Water Bottle", "1 litre stainless steel bottle", 499, "Accessories", 30),
            ("Notebook", "A5 ruled notebook", 99, "Stationery", 50)
        ]

        for product in sample_products:
            connection.execute("""
                INSERT INTO products
                (name, description, price, category, stock, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (*product, datetime.now().isoformat()))

    connection.commit()
    connection.close()


def valid_id(product_id):
    return product_id.isdigit() and int(product_id) > 0


@app.route("/api/products", methods=["POST"])
def create_product():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Valid JSON is required"}), 400

    for field in ["name", "description", "category"]:
        if not isinstance(data.get(field), str) or not data[field].strip():
            return jsonify({"error": field + " is required"}), 400

    try:
        price = float(data["price"])
        stock = data.get("stock", 0)

        if isinstance(stock, bool) or not isinstance(stock, int):
            raise ValueError()

        if price <= 0 or stock < 0:
            raise ValueError()

    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "Price must be positive and stock must be a non-negative integer"}), 400

    connection = connect_db()
    cursor = connection.execute("""
        INSERT INTO products
        (name, description, price, category, stock, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data["name"].strip(),
        data["description"].strip(),
        price,
        data["category"].strip(),
        stock,
        datetime.now().isoformat()
    ))

    connection.commit()
    product = connection.execute(
        "SELECT * FROM products WHERE id = ?", (cursor.lastrowid,)
    ).fetchone()

    connection.close()
    return jsonify(dict(product)), 201


@app.route("/api/products", methods=["GET"])
def get_products():
    connection = connect_db()
    products = connection.execute(
        "SELECT * FROM products"
    ).fetchall()
    connection.close()

    return jsonify([dict(product) for product in products]), 200


@app.route("/api/products/<product_id>", methods=["GET"])
def get_product(product_id):
    if not valid_id(product_id):
        return jsonify({"error": "Invalid product ID"}), 400

    connection = connect_db()
    product = connection.execute(
        "SELECT * FROM products WHERE id = ?", (int(product_id),)
    ).fetchone()
    connection.close()

    if product is None:
        return jsonify({"error": "Product not found"}), 404

    return jsonify(dict(product)), 200


@app.route("/api/products/<product_id>", methods=["PUT"])
def update_product(product_id):
    if not valid_id(product_id):
        return jsonify({"error": "Invalid product ID"}), 400

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Valid JSON is required"}), 400

    try:
        price = float(data["price"])
        stock = data["stock"]

        if isinstance(stock, bool) or not isinstance(stock, int):
            raise ValueError()

        if price <= 0 or stock < 0:
            raise ValueError()

    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "Provide a positive price and non-negative integer stock"}), 400

    connection = connect_db()
    product = connection.execute(
        "SELECT * FROM products WHERE id = ?", (int(product_id),)
    ).fetchone()

    if product is None:
        connection.close()
        return jsonify({"error": "Product not found"}), 404

    connection.execute("""
        UPDATE products
        SET price = ?, stock = ?
        WHERE id = ?
    """, (price, stock, int(product_id)))

    connection.commit()
    updated_product = connection.execute(
        "SELECT * FROM products WHERE id = ?", (int(product_id),)
    ).fetchone()

    connection.close()
    return jsonify(dict(updated_product)), 200


@app.route("/api/products/<product_id>", methods=["DELETE"])
def delete_product(product_id):
    if not valid_id(product_id):
        return jsonify({"error": "Invalid product ID"}), 400

    connection = connect_db()
    product = connection.execute(
        "SELECT * FROM products WHERE id = ?", (int(product_id),)
    ).fetchone()

    if product is None:
        connection.close()
        return jsonify({"error": "Product not found"}), 404

    connection.execute(
        "DELETE FROM products WHERE id = ?", (int(product_id),)
    )
    connection.commit()
    connection.close()

    return "", 204


@app.route("/api/products/category/<category_name>", methods=["GET"])
def get_products_by_category(category_name):
    connection = connect_db()
    products = connection.execute(
        "SELECT * FROM products WHERE LOWER(category) = LOWER(?)",
        (category_name,)
    ).fetchall()
    connection.close()

    return jsonify([dict(product) for product in products]), 200


if __name__ == "__main__":
    create_database()
    app.run(debug=True)

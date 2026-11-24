from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

DATABASE = "shop.db"


def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def create_tables():
    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    product_count = connection.execute(
        "SELECT COUNT(*) AS count FROM products"
    ).fetchone()["count"]

    if product_count == 0:
        products = [
            ("Notebook", 50, "A good quality notebook for school and daily writing."),
            ("Pen", 10, "Smooth writing ball pen suitable for students and office use."),
            ("School Bag", 650, "Strong and spacious school bag with multiple compartments."),
            ("Water Bottle", 150, "Reusable water bottle for school, office and travel."),
            ("Pencil Box", 100, "Compact pencil box for keeping stationery organized.")
        ]

        connection.executemany("""
            INSERT INTO products (name, price, description)
            VALUES (?, ?, ?)
        """, products)

    connection.commit()
    connection.close()


@app.route("/")
def home():
    connection = get_connection()
    products = connection.execute(
        "SELECT * FROM products ORDER BY id"
    ).fetchall()
    connection.close()

    return render_template("home.html", products=products)


@app.route("/product/<int:id>")
def product_details(id):
    connection = get_connection()
    product = connection.execute(
        "SELECT * FROM products WHERE id = ?", (id,)
    ).fetchone()
    connection.close()

    if product is None:
        return render_template(
            "product.html",
            product=None,
            message="Product does not exist."
        ), 404

    return render_template("product.html", product=product, message=None)


@app.route("/order/<int:id>", methods=["GET", "POST"])
def order(id):
    connection = get_connection()

    product = connection.execute(
        "SELECT * FROM products WHERE id = ?", (id,)
    ).fetchone()

    if product is None:
        connection.close()
        return render_template(
            "order.html",
            product=None,
            message="Product does not exist."
        ), 404

    if request.method == "POST":
        customer_name = request.form.get("customer_name", "").strip()
        quantity_text = request.form.get("quantity", "").strip()

        if not customer_name:
            connection.close()
            return render_template(
                "order.html",
                product=product,
                message="Customer name cannot be empty."
            )

        try:
            quantity = int(quantity_text)
        except ValueError:
            connection.close()
            return render_template(
                "order.html",
                product=product,
                message="Quantity must be a positive whole number."
            )

        if quantity <= 0:
            connection.close()
            return render_template(
                "order.html",
                product=product,
                message="Quantity must be a positive whole number."
            )

        cursor = connection.execute("""
            INSERT INTO orders (customer_name, product_id, quantity)
            VALUES (?, ?, ?)
        """, (customer_name, product["id"], quantity))

        connection.commit()
        order_id = cursor.lastrowid
        connection.close()

        return redirect(url_for("confirmation", id=order_id))

    connection.close()
    return render_template("order.html", product=product, message=None)


@app.route("/confirmation/<int:id>")
def confirmation(id):
    connection = get_connection()

    order_data = connection.execute("""
        SELECT
            orders.id,
            orders.customer_name,
            orders.quantity,
            products.name AS product_name,
            products.price
        FROM orders
        JOIN products ON orders.product_id = products.id
        WHERE orders.id = ?
    """, (id,)).fetchone()

    connection.close()

    if order_data is None:
        return render_template(
            "confirmation.html",
            order=None,
            message="Order does not exist."
        ), 404

    total_amount = order_data["price"] * order_data["quantity"]

    return render_template(
        "confirmation.html",
        order=order_data,
        total_amount=total_amount,
        message=None
    )


if __name__ == "__main__":
    create_tables()
    app.run(debug=True)

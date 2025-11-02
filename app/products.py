# server_flask/app/products.py

from flask import Blueprint, jsonify, request
from .db import get_db_connection
from .decorators import manager_required# Import our shared db function

# Define the blueprint
products_bp = Blueprint('products', __name__, url_prefix='/api/products')


@products_bp.route('/', methods=['GET'])
def get_products():
    """ Function to get all products (menu items). """
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM products;')
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        products = [dict(zip(columns, row)) for row in rows]
        cur.close()
        conn.close()
        return jsonify(products)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@products_bp.route('/', methods=['POST'])
@manager_required
def add_product():
    """ Function to add a new product. """
    data = request.get_json()
    try:
        product_name = data.get('product_name')
        price = data.get('price')
        # ... (rest of your fields)
        if not product_name or price is None:
            return jsonify({"error": "product_name and price are required"}), 400
    except Exception as e:
        return jsonify({"error": "Invalid JSON data provided", "details": str(e)}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        cur = conn.cursor()
        sql_query = """
            INSERT INTO products (product_name, price, category, flavor, flavor_2, flavor_3, milk, cream, sugar)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING product_id
        """
        values = (
            data.get('product_name'), data.get('price'), data.get('category'),
            data.get('flavor'), data.get('flavor_2'), data.get('flavor_3'),
            data.get('milk'), data.get('cream'), data.get('sugar')
        )
        cur.execute(sql_query, values)
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "Product added successfully", "id": new_id}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500


@products_bp.route('/<int:product_id>', methods=['PUT'])
@manager_required
def update_product(product_id):
    """ Function to update an existing product using its product_id. """
    data = request.get_json()
    try:
        product_name = data.get('product_name')
        price = data.get('price')
        if not product_name or price is None:
            return jsonify({"error": "product_name and price are required"}), 400
    except Exception as e:
        return jsonify({"error": "Invalid JSON data", "details": str(e)}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        cur = conn.cursor()
        sql_query = """
            UPDATE products SET product_name = %s, price = %s, category = %s, flavor = %s, 
            flavor_2 = %s, flavor_3 = %s, milk = %s, cream = %s, sugar = %s
            WHERE product_id = %s
        """
        values = (
            data.get('product_name'), data.get('price'), data.get('category'),
            data.get('flavor'), data.get('flavor_2'), data.get('flavor_3'),
            data.get('milk'), data.get('cream'), data.get('sugar'), product_id
        )
        cur.execute(sql_query, values)
        conn.commit()

        rowcount = cur.rowcount  # Get rowcount *before* closing cursor
        cur.close()
        conn.close()

        if rowcount == 0:
            return jsonify({"error": "Product not found"}), 404
        return jsonify({"message": f"Product {product_id} updated successfully"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500


@products_bp.route('/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """ Function to delete a product using its product_id. """
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
        conn.commit()

        rowcount = cur.rowcount
        cur.close()
        conn.close()

        if rowcount == 0:
            return jsonify({"error": "Product not found"}), 404
        return jsonify({"message": f"Product {product_id} deleted successfully"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
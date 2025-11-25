# server_flask/app/orders.py

from flask import Blueprint, jsonify, request
from .db import get_db_connection
from .decorators import staff_required

# We use a general prefix since this file handles /orders AND /items
orders_bp = Blueprint('orders', __name__, url_prefix='/api')


@orders_bp.route('/orders', methods=['GET'], strict_slashes=False)
@staff_required
def get_orders():
    """Function to get paginated orders."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))

        cur = conn.cursor()
        # 1️⃣ Get paginated data
        cur.execute(
            "SELECT * FROM orders ORDER BY order_id DESC LIMIT %s OFFSET %s;",
            (limit, offset)
        )
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        orders = [dict(zip(columns, row)) for row in rows]

        # 2️⃣ Get total count of all orders (for pagination)
        cur.execute("SELECT COUNT(*) FROM orders;")
        total_count = cur.fetchone()[0]

        cur.close()
        conn.close()

        return jsonify({
            "orders": orders,
            "count": total_count,
            "limit": limit,
            "offset": offset
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@orders_bp.route('/orders', methods=['POST'], strict_slashes=False)
def add_order():
    """ Function to add a new order. This is a TRANSACTION. """
    data = request.get_json()
    order_details = {
        "time": data.get('time'), "day": data.get('day'), "month": data.get('month'),
        "year": data.get('year'), "total_price": data.get('total_price'), "tip": data.get('tip'),
        "special_notes": data.get('special_notes'), "payment_method": data.get('payment_method'), "tax": data.get('tax')
    }
    items_list = data.get('items')

    # Basic validation
    if not all(v is not None for v in order_details.values()) or not items_list:
         # A more robust check for required fields
        if not data.get('time') or not data.get('day') or not data.get('month') or not data.get('year') or data.get('total_price') is None or not data.get('payment_method'):
             return jsonify({"error": "Missing required order details"}), 400
        if not items_list:
            return jsonify({"error": "Order must contain at least one item"}), 400


    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        cur = conn.cursor()
        order_sql = """
            INSERT INTO orders (time, day, month, year, total_price, tip, special_notes, payment_method, tax)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING order_id
        """
        # Use .get() for optional fields like tip and special_notes
        order_values = (
            order_details["time"], order_details["day"], order_details["month"],
            order_details["year"], order_details["total_price"], order_details.get("tip"),
            order_details.get("special_notes"), order_details["payment_method"], order_details["tax"]
        )
        cur.execute(order_sql, order_values)
        new_order_id = cur.fetchone()[0]

        item_sql = """
            INSERT INTO items (order_id, product_id, size, sugar_level, ice_level, toppings, price)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        for item in items_list:
            item_values = (
                new_order_id, item.get('product_id'), item.get('size'),
                item.get('sugar_level'), item.get('ice_level'), item.get('toppings'), item.get('price')
            )
            cur.execute(item_sql, item_values)

        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "Order added successfully", "order_id": new_order_id}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"Transaction failed: {str(e)}"}), 500

# ... (after the add_order function) ...

@orders_bp.route('/orders/<int:order_id>', methods=['GET'], strict_slashes=False)
@staff_required
def get_order_by_id(order_id):
    """
    Function to get a single order by its ID, including all its items
    and their product names.
    """
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        cur = conn.cursor()

        # 1. Get the main order details
        cur.execute('SELECT * FROM orders WHERE order_id = %s;', (order_id,))
        order_row = cur.fetchone()

        if order_row is None:
            cur.close()
            conn.close()
            return jsonify({"error": "Order not found"}), 404

        # Convert the order row to a dictionary
        order_columns = [desc[0] for desc in cur.description]
        order_details = dict(zip(order_columns, order_row))

        # 2. Get all items for that order, joining with products to get product_name
        # We use LEFT JOIN in case a product was somehow deleted
        # but we still want to show the order item.
        item_sql = """
            SELECT i.*, p.product_name
            FROM items i
            LEFT JOIN products p ON i.product_id = p.product_id
            WHERE i.order_id = %s
            ORDER BY i.item_id;
        """
        cur.execute(item_sql, (order_id,))
        item_rows = cur.fetchall()

        # Convert item rows to a list of dictionaries
        item_columns = [desc[0] for desc in cur.description]
        order_items = [dict(zip(item_columns, row)) for row in item_rows]

        # 3. Combine and return
        # This matches what the frontend OrderDetailsModal expects:
        # an order object with an 'items' key containing an array.
        order_details['items'] = order_items

        cur.close()
        conn.close()
        return jsonify(order_details)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ... (keep the get_items function below this) ...

@orders_bp.route('/items', methods=['GET'], strict_slashes=False)
@staff_required
def get_items():
    """ Function to get the last 1000 items, most recent first. """
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM items ORDER BY item_id DESC LIMIT 1000;')
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        items = [dict(zip(columns, row)) for row in rows] # Fixed variable name
        cur.close()
        conn.close()
        return jsonify(items)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
# server_flask/app/inventory.py

from flask import Blueprint, jsonify, request
from .db import get_db_connection
from .decorators import manager_required, staff_required

inventory_bp = Blueprint('inventory', __name__, url_prefix='/api')


@inventory_bp.route('/inventory', methods=['GET'])
@staff_required
def get_inventory():
    """ Function to get all inventory items. """
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        cur = conn.cursor()
        # This aliases numservings to numServings
        cur.execute('SELECT inv_item_id, name, units_remaining, numservings AS "numServings" FROM inventory;')
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        inventory = [dict(zip(columns, row)) for row in rows]  # Fixed variable name
        cur.close()
        conn.close()
        return jsonify(inventory)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inventory_bp.route('/inventory/<int:inv_item_id>', methods=['PUT'])
@manager_required
def update_inventory(inv_item_id):
    """ Function to update an inventory item's stock levels using its inv_item_id. """
    data = request.get_json()
    try:
        # --- START FIX ---

        # We only care about stock levels in this route
        units_remaining = data.get('units_remaining')
        numServings = data.get('numServings')

        # Updated validation: Check for units_remaining and numServings
        if units_remaining is None or numServings is None:
            return jsonify({"error": "units_remaining and numServings are required"}), 400

        # Optional: Check if they are valid numbers (though parseFloat on frontend helps)
        if not isinstance(units_remaining, (int, float)) or not isinstance(numServings, (int, float)):
            return jsonify({"error": "Stock levels must be numbers"}), 400

        # --- END FIX ---

    except Exception as e:
        return jsonify({"error": "Invalid JSON data", "details": str(e)}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        cur = conn.cursor()

        # --- START FIX 2 ---

        # Updated SQL query: Do NOT update the name
        sql_query = "UPDATE inventory SET units_remaining = %s, numServings = %s WHERE inv_item_id = %s"
        values = (units_remaining, numServings, inv_item_id)

        # --- END FIX 2 ---

        cur.execute(sql_query, values)
        conn.commit()

        rowcount = cur.rowcount

        if rowcount == 0:
            cur.close()
            conn.close()
            return jsonify({"error": "Inventory item not found"}), 404


        cur.execute("SELECT * FROM inventory WHERE inv_item_id = %s", (inv_item_id,))
        columns = [desc[0] for desc in cur.description]
        updated_item = dict(zip(columns, cur.fetchone()))

        cur.close()
        conn.close()

        return jsonify(updated_item)  # Return the full object


    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"error": str(e)}), 500


@inventory_bp.route('/inventory/<int:inv_item_id>', methods=['DELETE'])
@manager_required
def delete_inventory(inv_item_id):
    """ Function to delete an inventory item using its inv_item_id. """
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM inventory WHERE inv_item_id = %s", (inv_item_id,))
        conn.commit()

        rowcount = cur.rowcount
        cur.close()
        conn.close()

        if rowcount == 0:
            return jsonify({"error": "Inventory item not found"}), 404
        return jsonify({"message": f"Inventory item {inv_item_id} deleted successfully"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500


@inventory_bp.route('/ingredients', methods=['GET'])
@staff_required
def get_ingredients():
    """ Function to get all ingredients. """
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM ingredients;')
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        ingredients = [dict(zip(columns, row)) for row in rows]
        cur.close()
        conn.close()
        return jsonify(ingredients)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
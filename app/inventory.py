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
        cur.execute('SELECT * FROM inventory;')
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
    """ Function to update an inventory item using its inv_item_id. """
    data = request.get_json()
    try:
        name = data.get('name')
        units_remaining = data.get('units_remaining')
        if not name or units_remaining is None:
            return jsonify({"error": "name and units_remaining are required"}), 400
    except Exception as e:
        return jsonify({"error": "Invalid JSON data", "details": str(e)}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        cur = conn.cursor()
        sql_query = "UPDATE inventory SET name = %s, units_remaining = %s, numServings = %s WHERE inv_item_id = %s"
        values = (name, units_remaining, data.get('numServings'), inv_item_id)
        cur.execute(sql_query, values)
        conn.commit()

        rowcount = cur.rowcount
        cur.close()
        conn.close()

        if rowcount == 0:
            return jsonify({"error": "Inventory item not found"}), 404
        return jsonify({"message": f"Inventory item {inv_item_id} updated successfully"})
    except Exception as e:
        conn.rollback()
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
# server_flask/app/staff.py

from flask import Blueprint, jsonify, request
from .db import get_db_connection
from .decorators import manager_required

staff_bp = Blueprint('staff', __name__, url_prefix='/api/staff')


@staff_bp.route('/', methods=['GET'])
@manager_required
def get_staff():
    """ Function to get all staff members. """
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM staff;')
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        staff = [dict(zip(columns, row)) for row in rows]  # Fixed variable name
        cur.close()
        conn.close()
        return jsonify(staff)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@staff_bp.route('/', methods=['POST'])
@manager_required
def add_employee():
    """ Function to add a new employee. """
    data = request.get_json()
    try:
        staff_id = data.get('staff_id')
        name = data.get('name')
        role = data.get('role')
        if not staff_id or not name or not role:
            return jsonify({"error": "staff_id, name, and role are required"}), 400
    except Exception as e:
        return jsonify({"error": "Invalid JSON data", "details": str(e)}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        cur = conn.cursor()
        sql_query = "INSERT INTO staff (staff_id, name, role, salary, hours_worked) VALUES (%s, %s, %s, %s, %s)"
        values = (
            staff_id, name, role,
            data.get('salary'), data.get('hours_worked')
        )
        cur.execute(sql_query, values)
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": f"Employee {name} added successfully"}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500


@staff_bp.route('/<string:staff_id>', methods=['PUT'])
@manager_required
def update_employee(staff_id):
    """ Function to update an existing employee's details. """
    data = request.get_json()
    try:
        name = data.get('name')
        role = data.get('role')
        if not name or not role:
            return jsonify({"error": "name and role are required"}), 400
    except Exception as e:
        return jsonify({"error": "Invalid JSON data", "details": str(e)}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        cur = conn.cursor()
        sql_query = "UPDATE staff SET name = %s, role = %s, salary = %s, hours_worked = %s WHERE staff_id = %s"
        values = (
            name, role, data.get('salary'),
            data.get('hours_worked'), staff_id
        )
        cur.execute(sql_query, values)
        conn.commit()

        rowcount = cur.rowcount
        cur.close()
        conn.close()

        if rowcount == 0:
            return jsonify({"error": "Staff member not found"}), 404
        return jsonify({"message": f"Staff member {staff_id} updated successfully"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500


@staff_bp.route('/<string:staff_id>', methods=['DELETE'])
@manager_required
def remove_employee(staff_id):
    """ Function to remove an employee using their staff_id. """
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM staff WHERE staff_id = %s", (staff_id,))
        conn.commit()

        rowcount = cur.rowcount
        cur.close()
        conn.close()

        if rowcount == 0:
            return jsonify({"error": "Staff member not found"}), 404
        return jsonify({"message": f"Staff member {staff_id} removed successfully"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
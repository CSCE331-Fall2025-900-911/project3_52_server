# server_flask/app/decorators.py

from functools import wraps
from flask import session, jsonify

def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_role" not in session:
            return jsonify({"error": "Not authenticated"}), 401
        if session["user_role"] != "Manager":
            return jsonify({"error": "Access denied: Managers only"}), 403
        return f(*args, **kwargs)
    return decorated_function


def staff_required(f):
    """
    Checks if a user is a logged-in staff member (Manager or Cashier).
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_role" not in session:
            return jsonify({"error": "Not authenticated"}), 401

        allowed_roles = ["Manager", "Cashier"]
        if session["user_role"] not in allowed_roles:
            return jsonify({"error": "Access denied: Staff only"}), 403

        return f(*args, **kwargs)

    return decorated_function
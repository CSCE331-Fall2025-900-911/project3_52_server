# server_flask/app/auth.py

import os
from flask import Blueprint, jsonify, session, redirect, url_for
from flask_dance.contrib.google import make_google_blueprint, google
from .db import get_db_connection
from .decorators import login_required

# 1. Create the main auth blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# 2. Create the Flask-Dance blueprint
# Note: This will create a /google/login route and /google/callback route
# We "nest" it inside our /api/auth blueprint
google_bp = make_google_blueprint(
    client_id=os.environ.get("GOOGLE_OAUTH_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET"),
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"
    ],
    redirect_to="auth.google_callback"  # The function to call after login
)


# This is the /api/auth/login route
@auth_bp.route('/login', strict_slashes=False)
def login():
    """
    Redirects the user to the Google login page.
    The 'google.login' is the route Flask-Dance creates.
    """
    return redirect(url_for('google.login'))


# This is the /api/auth/logout route
@auth_bp.route('/logout', strict_slashes=False)
@login_required
def logout():
    """Clears the user's session."""
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200


# This is the internal callback route that Flask-Dance will hit.
# It is NOT the same as the /api/auth/google/callback we told Google.
@auth_bp.route('/google/callback', strict_slashes=False)
def google_callback():
    """
    This is the route Google redirects to *after* the user logs in.
    Flask-Dance handles the token exchange.
    """
    if not google.authorized:
        return jsonify({"error": "Login failed."}), 401

    # Get user info from Google
    try:
        resp = google.get("/oauth2/v2/userinfo")
        assert resp.ok, resp.text
        user_info = resp.json()
        user_email = user_info["email"]
    except Exception as e:
        return jsonify({"error": "Failed to fetch user info from Google", "details": str(e)}), 500

    # Now, find this user in our 'staff' table
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cur = conn.cursor()
        cur.execute("SELECT staff_id, name, role FROM staff WHERE email = %s", (user_email,))
        staff_member = cur.fetchone()
        cur.close()
        conn.close()

        if staff_member:
            # User is found! Create a session.
            session["user_id"] = staff_member[0]
            session["user_name"] = staff_member[1]
            session["user_role"] = staff_member[2]
            session["user_email"] = user_email

            # Redirect to the frontend's dashboard
            return redirect("http://127.0.0.1:3000")
        else:
            # User is not in the staff table
            return redirect("http://127.0.0.1:3000")

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# This is an endpoint for your React app to check if a user is logged in
@auth_bp.route("/me", strict_slashes=False)
def get_current_user():
    """Gets the currently logged-in user from the session."""
    if "user_id" in session:
        return jsonify({
            "staff_id": session["user_id"],
            "name": session["user_name"],
            "role": session["user_role"],
            "email": session["user_email"]
        }), 200
    else:
        return jsonify({"error": "Not authenticated"}), 401
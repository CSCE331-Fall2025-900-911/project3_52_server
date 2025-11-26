from flask import Blueprint, request, jsonify
from app.db import get_db_connection
from datetime import datetime

discounts_bp = Blueprint("discounts", __name__)

@discounts_bp.route("/api/discounts/check", methods=["POST"])
def check_discount():
    data = request.get_json()
    code = data.get("code", "").strip().upper()

    if not code:
        return jsonify({"valid": False, "reason": "No code provided"}), 400

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT code, discount_type, value, starts_at, ends_at
                FROM discount_codes
                WHERE code = %s
            """, (code,))
            row = cur.fetchone()

    if not row:
        return jsonify({"valid": False, "reason": "Invalid code"}), 404

    code, dtype, value, starts_on, ends_on = row

    today = datetime.now().date()

    start = starts_on.date() if hasattr(starts_on, "date") else starts_on
    end = ends_on.date() if hasattr(ends_on, "date") else ends_on

    if today < start or today > end:
        return jsonify({"valid": False, "reason": "Code expired or inactive"}), 410


    return jsonify({
        "valid": True,
        "code": code.upper(),
        "type": dtype,
        "value": float(value)
    })

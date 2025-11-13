# app/reports.py
from flask import Blueprint, jsonify
from datetime import datetime
import pytz
from .xz_report import x_report_today, z_report_preview, z_report_close
from .db import get_db_connection  # ✅ Import your connection function

reports_bp = Blueprint("reports", __name__, url_prefix="/api/reports")
chicago_tz = pytz.timezone("America/Chicago")


@reports_bp.route("/x", methods=["GET"])
def x_report_route():
    return jsonify(x_report_today())



@reports_bp.route("/z/preview", methods=["GET"])
def z_preview_route():
    return jsonify(z_report_preview())

@reports_bp.route("/z/status", methods=["GET"])
def z_status_route():
    """Check whether a Z-report has been run today."""
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "error": "Database connection failed"}), 500
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT * 
            FROM lastzreport 
        """)
        row = cur.fetchone()

        z_closed_today = False
        closed_at = None

        if row and row[0]:
            last_ts = row[0]
            if last_ts.date() == datetime.now(chicago_tz).date():
                z_closed_today = True
                closed_at = last_ts.strftime("%Y-%m-%d %H:%M:%S")

        cur.close()
        conn.close()
        return jsonify({"success": True, "z_closed_today": z_closed_today, "closed_at": closed_at})

    except Exception as e:
        if conn:
            conn.close()
        return jsonify({"success": False, "error": str(e)}), 500


@reports_bp.route("/z/close", methods=["POST"])
def z_close_route():
    """
    Runs the Z-report (end-of-day) only if one has not already been done today.
    """
    conn = get_db_connection()
    if not conn:
        return jsonify({
            "success": False,
            "message": "Database connection failed."
        }), 500

    try:
        cur = conn.cursor()

        # 1️⃣ Check if a Z-report has already been run today
        cur.execute("""
            SELECT last_ts 
            FROM lastzreport 
            ORDER BY last_ts DESC 
            LIMIT 1;
        """)
        row = cur.fetchone()

        # Convert timezones safely
        central = pytz.timezone("America/Chicago")
        now_local = datetime.now(central)

        # Only check if we actually have a previous record
        if row and row[0]:
            last_ts = row[0]

            # Convert database timestamp (UTC) → local time
            if last_ts.tzinfo is None:
                # If your DB stores naive timestamps (no tz), assume UTC
                last_ts = pytz.utc.localize(last_ts)

            last_local = last_ts.astimezone(central)

            # Compare the local dates
            if last_local.date() == now_local.date():
                cur.close()
                conn.close()
                return jsonify({
                    "success": False,
                    "message": "Z-report already run today. Try again tomorrow."
                }), 400

        # 2️⃣ Run the close logic (your existing z_report_close function)
        result = z_report_close()

        conn.commit()
        cur.close()
        conn.close()

        return jsonify(result)

    except Exception as e:
        print("Error running Z-report:", e)
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({
            "success": False,
            "message": "Error running Z-report.",
            "error": str(e)
        }), 500

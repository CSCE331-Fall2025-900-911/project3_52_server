# app/xz_report.py
from datetime import datetime
from app.db import get_db_connection
import pytz

ORDER_TS_SQL = """
  (
    to_timestamp(
      concat(year,'-',lpad(month::text,2,'0'),'-',lpad(day::text,2,'0'),' ', time::text),
      'YYYY-MM-DD HH24:MI:SS'
    ) AT TIME ZONE 'America/Chicago'
  )
"""



def _get_last_z_timestamp(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT last_ts FROM lastzreport LIMIT 1;")
        row = cur.fetchone()
        return row[0] if row and row[0] else None


def _get_start_time(conn):
    """Return start time for reporting:
       - if last Z is today → start from last Z
       - else → start from today's midnight
    """
    central = pytz.timezone("America/Chicago")
    now = datetime.now(central)
    last_z = _get_last_z_timestamp(conn)
    midnight_today = datetime.combine(now.date(), datetime.min.time())

    if last_z and last_z.date() == now.date():
        # Last Z happened today → start from that timestamp
        start_time = last_z
    else:
        # No Z today → start from midnight
        start_time = midnight_today
    print (start_time)

    return start_time, last_z



def x_report_today():
    """X report: totals since midnight or last Z if earlier."""
    conn = get_db_connection()
    if not conn:
        return {"summary": {}, "by_payment": [], "by_hour": []}

    try:
        start_time, _ = _get_start_time(conn)
        with conn.cursor() as cur:
            # Summary
            cur.execute(f"""
                SELECT COUNT(*) AS total_orders,
                       COALESCE(SUM(total_price),0),
                       COALESCE(SUM(tip),0)
                FROM orders
                WHERE {ORDER_TS_SQL} >= %s;
            """, (start_time,))
            total_orders, total_revenue, total_tips = cur.fetchone() or (0, 0, 0)

            # By payment
            cur.execute(f"""
                SELECT payment_method,
                       COUNT(*),
                       COALESCE(SUM(total_price),0)
                FROM orders
                WHERE {ORDER_TS_SQL} >= %s
                GROUP BY payment_method
                ORDER BY 3 DESC;
            """, (start_time,))
            by_payment = [
                {"payment_method": r[0], "orders": int(r[1]), "revenue": float(r[2])}
                for r in cur.fetchall()
            ]

            # By hour
            cur.execute(f"""
                SELECT LEFT(time::text,2)||':00' AS hour,
                       COUNT(*),
                       COALESCE(SUM(total_price),0),
                       COALESCE(SUM(tip),0)
                FROM orders
                WHERE {ORDER_TS_SQL} >= %s
                GROUP BY hour
                ORDER BY hour;
            """, (start_time,))
            by_hour = [
                {"hour": r[0], "orders": int(r[1]), "revenue": float(r[2]), "tips": float(r[3])}
                for r in cur.fetchall()
            ]

            return {
                "summary": {
                    "total_orders": int(total_orders or 0),
                    "total_revenue": float(total_revenue or 0),
                    "total_tips": float(total_tips or 0),
                },
                "by_payment": by_payment,
                "by_hour": by_hour,
            }
    finally:
        conn.close()


def z_report_preview():
    """Preview Z report since last Z or midnight."""
    conn = get_db_connection()
    if not conn:
        return {"summary": {}, "by_payment": [], "last_z": None}

    try:
        start_time, last_z = _get_start_time(conn)
        with conn.cursor() as cur:
            # Summary
            cur.execute(f"""
                SELECT COUNT(*),
                       COALESCE(SUM(total_price),0),
                       COALESCE(SUM(tip),0)
                FROM orders
                WHERE {ORDER_TS_SQL} >= %s;
            """, (start_time,))
            total_orders, total_revenue, total_tips = cur.fetchone() or (0, 0, 0)

            # By payment
            cur.execute(f"""
                SELECT payment_method,
                       COUNT(*),
                       COALESCE(SUM(total_price),0)
                FROM orders
                WHERE {ORDER_TS_SQL} >= %s
                GROUP BY payment_method
                ORDER BY 3 DESC;
            """, (start_time,))
            by_payment = [
                {"payment_method": r[0], "orders": int(r[1]), "revenue": float(r[2])}
                for r in cur.fetchall()
            ]

            summary = {
                "total_orders": int(total_orders or 0),
                "total_revenue": float(total_revenue or 0),
                "total_tips": float(total_tips or 0),
            }

            return {
                "last_z": last_z.strftime("%Y-%m-%d %H:%M:%S") if last_z else None,
                "summary": summary,
                "by_payment": by_payment,
            }
    finally:
        conn.close()


def z_report_close():
    """Close Z report for today and update last_ts in the database."""
    conn = get_db_connection()
    if not conn:
        return {"closed_at": None, "summary": {}, "by_payment": []}

    try:
        start_time, last_z = _get_start_time(conn)

        with conn.cursor() as cur:
            # Compute totals for the range
            cur.execute(f"""
                SELECT COUNT(*) AS total_orders,
                       COALESCE(SUM(total_price),0) AS total_revenue,
                       COALESCE(SUM(tip),0) AS total_tips
                FROM orders
                WHERE {ORDER_TS_SQL} >= %s;
            """, (start_time,))
            total_orders, total_revenue, total_tips = cur.fetchone() or (0, 0, 0)

            # By payment method
            cur.execute(f"""
                SELECT payment_method,
                       COUNT(*) AS orders,
                       COALESCE(SUM(total_price),0) AS revenue
                FROM orders
                WHERE {ORDER_TS_SQL} >= %s
                GROUP BY payment_method
                ORDER BY revenue DESC;
            """, (start_time,))
            by_payment = [
                {"payment_method": r[0], "orders": int(r[1]), "revenue": float(r[2])}
                for r in cur.fetchall()
            ]

            # Update last_zreport timestamp
            cur.execute("UPDATE lastzreport SET last_ts = (NOW() AT TIME ZONE 'America/Chicago');")
            conn.commit()

            # Format output timestamps
            central = pytz.timezone("America/Chicago")
            closed_at_local = datetime.now(pytz.utc).astimezone(central)
            last_z_str = last_z.strftime("%Y-%m-%d %H:%M:%S") if last_z else None

            return {
                "closed_at": closed_at_local.strftime("%Y-%m-%d %H:%M:%S"),
                "since_last_z": last_z_str,
                "summary": {
                    "total_orders": int(total_orders or 0),
                    "total_revenue": float(total_revenue or 0),
                    "total_tips": float(total_tips or 0),
                },
                "by_payment": by_payment,
            }
    except Exception as e:
        conn.rollback()
        print("Error in z_report_close:", e)
        return {"error": str(e)}
    finally:
        conn.close()

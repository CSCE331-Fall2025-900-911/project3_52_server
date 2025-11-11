from flask import Blueprint, jsonify
from .db import get_db_connection
from .decorators import manager_required

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@dashboard_bp.route('/stats', methods=['GET'])
@manager_required
def get_dashboard_stats():
    """
    Comprehensive Manager Dashboard Stats
    Includes: Revenue trends, top products, staff performance,
              inventory alerts, order patterns, and category breakdown
    """
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cur = conn.cursor()

        cur.execute("SET TIME ZONE 'America/Chicago';")
        
        # ========================================
        # 1. REVENUE: Last 30 Days (Line Chart)
        # ========================================
        cur.execute("""
            SELECT 
                CONCAT(o.year, '-', LPAD(o.month::text, 2, '0'), '-', LPAD(o.day::text, 2, '0')) AS date,
                COALESCE(SUM(o.total_price + o.tip), 0) AS daily_total
            FROM orders o
            WHERE MAKE_DATE(o.year, o.month, o.day) >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY o.year, o.month, o.day
            ORDER BY o.year, o.month, o.day
            LIMIT 30;
        """)
        revenue_over_time = [
            {"date": str(row[0]), "revenue": float(row[1])}
            for row in cur.fetchall()
        ]

        total_revenue = sum(item["revenue"] for item in revenue_over_time)

        # ========================================
        # 2. TOP 10 BEST-SELLING PRODUCTS (Bar Chart)
        # ========================================
        cur.execute("""
            SELECT 
                p.product_name,
                COUNT(i.item_id) AS units_sold,
                COALESCE(SUM(i.price), 0) AS revenue
            FROM products p
            LEFT JOIN items i ON p.product_id = i.product_id
            GROUP BY p.product_id, p.product_name
            ORDER BY units_sold DESC, revenue DESC
            LIMIT 10;
        """)
        top_products = [
            {
                "name": row[0],
                "units_sold": int(row[1]),
                "revenue": float(row[2])
            }
            for row in cur.fetchall()
        ]

        # ========================================
        # 3. SALES BY CATEGORY (Pie / Donut Chart)
        # ========================================
        cur.execute("""
            SELECT p.category, 
                   COUNT(i.item_id) as items_sold
            FROM products p
            LEFT JOIN items i ON p.product_id = i.product_id
            GROUP BY p.category
            ORDER BY items_sold DESC;
        """)
        category_breakdown = [
            {"category": row[0] or "Uncategorized", "sold": int(row[1])}
            for row in cur.fetchall()
        ]

        # ========================================
        # 4. ORDERS BY HOUR (Heatmap / Bar Chart)
        # ========================================
        cur.execute("""
            SELECT 
                EXTRACT(HOUR FROM CAST(o.time AS time))::int AS hour,
                COUNT(*) AS order_count
            FROM orders o
            WHERE MAKE_DATE(o.year, o.month, o.day) >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY hour
            ORDER BY hour;
        """)
        hourly_orders = [
            {"hour": int(row[0]), "count": int(row[1])}
            for row in cur.fetchall()
        ]

        # ========================================
        # 5. STAFF PERFORMANCE (Table + Bar Chart)
        # ========================================
        cur.execute("""
            SELECT name, role, hours_worked, salary,
                   ROUND(salary / NULLIF(hours_worked, 0), 2) as hourly_rate
            FROM staff
            ORDER BY hours_worked DESC;
        """)
        staff_performance = [
            {
                "name": row[0],
                "role": row[1],
                "hours": int(row[2]) if row[2] else 0,
                "salary": float(row[3]),
                "hourly_rate": float(row[4]) if row[4] else 0
            }
            for row in cur.fetchall()
        ]

        total_hours_worked = sum(s["hours"] for s in staff_performance)

        # ========================================
        # 6. INVENTORY LOW STOCK ALERTS (Critical!)
        # ========================================
        cur.execute("""
            SELECT 
                name, 
                units_remaining, 
                numservings,
                (units_remaining * numservings) AS total_servings_left
            FROM inventory
            WHERE (units_remaining * numservings) < 200
            AND numservings > 0                     -- safety: avoid division-by-zero weirdness
            ORDER BY total_servings_left ASC
            LIMIT 10;
        """)
        low_stock = [
            {
                "name": row[0],
                "remaining": int(row[1]),
                "servings_per_unit": int(row[2]),
                "servings_left": int(row[3])
            }
            for row in cur.fetchall()
        ]

        # ========================================
        # 7. TODAY'S SUMMARY (KPI Cards)
        # ========================================
        cur.execute("""
            SELECT 
                COUNT(*) AS orders_today,
                COALESCE(SUM(total_price + tip), 0) AS revenue_today,
                COALESCE(AVG(total_price + tip), 0) AS avg_order_value
            FROM orders
            WHERE year = EXTRACT(YEAR FROM CURRENT_DATE)::int
            AND month = EXTRACT(MONTH FROM CURRENT_DATE)::int
            AND day = EXTRACT(DAY FROM CURRENT_DATE)::int;
        """)
        today = cur.fetchone()
        today_stats = {
            "orders": int(today[0]),
            "revenue": float(today[1]),
            "avg_order": float(today[2])
        }

        # Close connection
        cur.close()
        conn.close()

        # ========================================
        # FINAL RESPONSE
        # ========================================
        return jsonify({
            "summary": {
                "totalRevenue30Days": round(total_revenue, 2),
                "totalOrders30Days": len(revenue_over_time),
                "totalHoursWorked": total_hours_worked,
                "lowStockItems": len(low_stock),
                "today": today_stats
            },
            "charts": {
                "revenueOverTime": revenue_over_time,
                "topProducts": top_products,
                "categoryBreakdown": category_breakdown,
                "hourlyOrders": hourly_orders,
                "staffPerformance": staff_performance,
                "lowStockAlerts": low_stock
            }
        })

    except Exception as e:
        if conn:
            conn.close()
        print(str(e))
        return jsonify({"error": str(e)}), 500
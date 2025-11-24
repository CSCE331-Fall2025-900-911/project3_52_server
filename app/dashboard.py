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

        # ========================================
        # 8. REVENUE CONCENTRATION: % of revenue from top drinks
        # ========================================
        cur.execute("""
            WITH product_revenue AS (
                SELECT 
                    p.product_name,
                    COALESCE(SUM(i.price), 0) AS revenue
                FROM products p
                LEFT JOIN items i ON p.product_id = i.product_id
                GROUP BY p.product_id, p.product_name
            ),
            totals AS (
                SELECT SUM(revenue) AS total_revenue FROM product_revenue
            )
            SELECT 
                product_name,
                revenue,
                ROUND(100.0 * revenue / total_revenue, 2) AS pct_of_total_revenue
            FROM product_revenue, totals
            WHERE revenue > 0
            ORDER BY revenue DESC
            LIMIT 15;
        """)
        revenue_concentration = [
            {"name": row[0], "revenue": float(row[1]), "pct": float(row[2])}
            for row in cur.fetchall()
        ]

        # ========================================
        # 9. TOPPINGS REVENUE (The silent profit king)
        # ========================================
        cur.execute("""
            SELECT 
                CASE WHEN toppings = '' OR toppings IS NULL THEN 'No Toppings' ELSE toppings END AS topping_combo,
                COUNT(*) AS times_ordered,
                ROUND(SUM(i.price - p.price), 2) AS topping_revenue
            FROM items i
            JOIN products p ON i.product_id = p.product_id
            GROUP BY topping_combo
            ORDER BY topping_revenue DESC
            LIMIT 10;
        """)
        topping_profit = [
            {"combo": row[0], "orders": int(row[1]), "revenue": float(row[2])}
            for row in cur.fetchall()
        ]

        # ========================================
        # 10. SIZE IMPACT (Bucee's size dominance?)
        # ========================================
        cur.execute("""
            SELECT 
                size,
                COUNT(*) AS items_sold,
                ROUND(AVG(price), 2) AS avg_price,
                ROUND(SUM(price), 2) AS total_revenue,
                ROUND(100.0 * SUM(price) / (SELECT SUM(price) FROM items WHERE price > 0), 2) AS pct_of_revenue
            FROM items
            WHERE price > 0
            GROUP BY size
            ORDER BY total_revenue DESC;
        """)
        size_analysis = [
            {"size": row[0], "sold": int(row[1]), "avg_price": float(row[2]), "revenue": float(row[3]), "pct": float(row[4])}
            for row in cur.fetchall()
        ]

        # ========================================
        # 11. WHALE ORDERS (Catering / VIP detection)
        # ========================================
        cur.execute("""
            SELECT 
                o.order_id,
                o.time::text,
                ROUND(o.total_price + o.tip, 2) AS grand_total,
                COUNT(i.item_id) AS items_count
            FROM orders o
            LEFT JOIN items i ON o.order_id = i.order_id
            GROUP BY o.order_id, o.time, o.total_price, o.tip
            HAVING total_price + tip >= 150
            ORDER BY grand_total DESC
            LIMIT 15;
        """)
        whale_orders = [
            {"id": row[0], "time": row[1], "total": float(row[2]), "items": int(row[3])}
            for row in cur.fetchall()
        ]

        # ========================================
        # 13. TIP BEHAVIOR BY PAYMENT METHOD
        # ========================================
        cur.execute("""
            SELECT 
                payment_method,
                COUNT(*) AS orders,
                ROUND(AVG(100.0 * tip / NULLIF(total_price, 0)), 2) AS avg_tip_pct,
                ROUND(AVG(total_price + tip), 2) AS avg_order_value
            FROM orders
            WHERE total_price > 0
            GROUP BY payment_method
            ORDER BY avg_tip_pct DESC;
        """)
        tip_behavior = [
            {"method": row[0], "orders": int(row[1]), "tip_pct": float(row[2]), "avg_order": float(row[3])}
            for row in cur.fetchall()
        ]

        cur.close()
        conn.close()

        return jsonify({
            "summary": {
                "totalRevenue30Days": round(total_revenue, 2),
                "totalOrders30Days": len(revenue_over_time),
                "lowStockItems": len(low_stock),
                "today": today_stats
            },
            "charts": {
                "revenueOverTime": revenue_over_time,
                "topProducts": top_products,
                "categoryBreakdown": category_breakdown,
                "hourlyOrders": hourly_orders,
                "lowStockAlerts": low_stock,
                # New charts
                "revenueConcentration": revenue_concentration,
                "toppingProfit": topping_profit,
                "sizeAnalysis": size_analysis,
                "whaleOrders": whale_orders,
                "tipBehavior": tip_behavior
            }
        })

    except Exception as e:
        if conn:
            conn.close()
        print(str(e))
        return jsonify({"error": str(e)}), 500
from app.db import get_db_connection


# NOTE:
# lastzreport is a singleton system-state table and must NOT be reset or lost
# during bulk CSV imports. This script explicitly preserves it.

print('\n\n## WARNING ## DO NOT DO THIS PROCESS REPEATEDLY WITHOUT VERIFYING THE DATA EACH TIME\n' +
      '\t YOU MAY DELETE ALL OLD DATA')

flag = ''
while flag not in ('y', 'n'):
    flag = input('Make sure the new orders and new items are valid before continuing...\n\nProceed? (y/n): ').lower()
if flag == 'n':
    exit(0)

conn = get_db_connection()
if conn == None:
    exit(1)
cur = conn.cursor()

# === Preserve lastzreport (singleton state table) ===
cur.execute("SELECT last_z_time FROM lastzreport LIMIT 1;")
row = cur.fetchone()
saved_last_z_time = row[0] if row else None

try:
    # === IMPORT newOrders.csv → orders table ===
    with open('tables/newOrders.csv', 'r') as f:
        f.readline()
        firstOrderID = f.readline().split(',')[0]

    with open("tables/newOrders.csv", "r", newline="", encoding="utf-8") as f:
        cur.copy_expert(
            """
            COPY orders FROM STDIN WITH (FORMAT CSV, HEADER TRUE)
            """,
            f
        )
    print("Imported newOrders.csv → orders table")

    # === IMPORT newItems.csv → items table ===
    with open("tables/newItems.csv", "r", newline="", encoding="utf-8") as f:
        cur.copy_expert(
            """
            COPY items FROM STDIN WITH (FORMAT CSV, HEADER TRUE)
            """,
            f
        )
    print("Imported newItems.csv → items table")

    conn.commit()

    # === Restore lastzreport if it was wiped by reset/import ===
    if saved_last_z_time is not None:
        cur.execute(
            "UPDATE lastzreport SET last_z_time = %s;",
            (saved_last_z_time,)
        )
    else:
        cur.execute(
            """
            INSERT INTO lastzreport (last_z_time)
            SELECT NOW()
            WHERE NOT EXISTS (SELECT 1 FROM lastzreport);
            """
        )
    conn.commit()
    
    print('\n\nNotes: FIND OLD DB VERSION IN tables/items.csv and orders.csv TO REVERT ANY CHANGES')
    print('Notes: (use this command in the database to remove new entries into the DB)')
    print(f'\t\t> DELETE FROM orders WHERE order_id >= \'{firstOrderID}\';')
    print('Notes: (the DELETE command cascades to all tables that use order as a Foreign Key)')
    print('\n\n## WARNING ## IF YOU REPEAT THIS PROCESS MULTIPLE TIMES, IT MAY DELETE ALL OLD DATA\n\n')

    cur.execute("""
            SELECT setval(pg_get_serial_sequence('products', 'product_id'), COALESCE(MAX(product_id), 1)) FROM products;
            SELECT setval(pg_get_serial_sequence('orders', 'order_id'), COALESCE(MAX(order_id), 1)) FROM orders;
            SELECT setval(pg_get_serial_sequence('items', 'item_id'), COALESCE(MAX(item_id), 1)) FROM items;
            SELECT setval(pg_get_serial_sequence('inventory', 'inv_item_id'), COALESCE(MAX(inv_item_id), 1)) FROM inventory;
        """)

except Exception as e:
    print(f"Error importing data: {e}")
    print('Import rolled back...')
    conn.rollback()
finally:
    cur.close()
    conn.close()

    # os.remove('tables/exampleItems.csv')
    # os.remove('tables/newItems.csv')
    # os.remove('tables/exampleOrders.csv')
    # os.remove('tables/newOrders.csv')

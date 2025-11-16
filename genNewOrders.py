import csv
import random
from datetime import date, datetime, timedelta
from faker import Faker
import os

from app.db import get_db_connection

def merge_csv_files(original_path, new_path, output_path):
    """Merge CSV files, skipping the header from the new file."""
    
    if output_path in (original_path, new_path):
        print('The output cannot be either of the inputs.')
        exit(1)

    with open(original_path, 'r') as original, open(new_path, 'r') as new_file:
        original_reader = csv.reader(original)
        new_reader = csv.reader(new_file)
        
        # Get header from original file
        header = next(original_reader)
        
        # Write merged data
        with open(output_path, 'w', newline='') as output:
            writer = csv.writer(output)
            writer.writerow(header)
            writer.writerows(original_reader)
            next(new_reader)  # Skip header in new file
            writer.writerows(new_reader)


conn = get_db_connection()
if conn == None:
    exit(1)
cur = conn.cursor()

# ----------------------------------------------------------------------
# Need to update the Items and Orders Tables to ensure the right ID
# ----------------------------------------------------------------------
local_item_csv = "tables/items.csv"
local_order_csv = "tables/orders.csv"
local_product_csv = "tables/products.csv"
os.makedirs('tables', exist_ok=True)

with open(local_item_csv, "w", newline="", encoding="utf-8") as f:
    cur.copy_expert(
        r"COPY (SELECT * FROM items) TO STDOUT WITH CSV HEADER",
        f
    )
print(f"Exported to {local_item_csv} on your local machine")

with open(local_order_csv, "w", newline="", encoding="utf-8") as f:
    cur.copy_expert(
        r"COPY (SELECT * FROM orders) TO STDOUT WITH CSV HEADER",
        f
    )
print(f"Exported to {local_order_csv} on your local machine")

with open(local_product_csv, "w", newline="", encoding="utf-8") as f:
    cur.copy_expert(
        r"COPY (SELECT * FROM products) TO STDOUT WITH CSV HEADER",
        f
    )
print(f"Exported to {local_product_csv} on your local machine")

cur.close()
conn.close()


fake = Faker()

weekGoal = 39

with open('tables/products.csv', 'r') as products:
    products = products.readlines()

products = [line.strip().split(',') for line in products][1:]

with open('tables/orders.csv', 'r') as orders:
    orderID = int(orders.readlines()[-1].strip().split(',')[0]) + 1

with open('tables/items.csv', 'r') as items:
    itemID = int(items.readlines()[-1].strip().split(',')[0]) + 1



"""
Writing Orders table and Items table
"""
# Printing purposes
totalRevenue = 0
peakDays = 0

# holidays list for peakDay logic. expand as needed/wanted
holidays = [
    (1, 1),    # New Year's Day
    (7, 4),    # Independence Day
    (11, 27),  # Thanksgiving (apparently isn't always 27th but whatever)
    (12, 25)   # Christmas!
]

orders  = []
items   = []

""" Start date input validation """
badFormat = True
while badFormat:
    try:
        startDate = datetime.strptime(input("Enter the date from which you would like to populate the orders table (form MM-DD-YYYY): "), "%m-%d-%Y")
        checkDate = input(f"\n\nYou will create new orders from {startDate.date()} to {datetime.now().date()}.\nAre you sure? (y/n)\n>>> ")
        while checkDate.lower() not in ('y', 'n'):
            checkDate = input(f"Try again...\nAre you sure? (y/n)\n>>> ")
        badFormat = False if checkDate == 'y' else True
    except ValueError:
        print("Bad format")
        continue

endDate = datetime.now()
currentDate = startDate

sizes = ['Small', 'Medium', 'Large', 'Bucee\'s']
sugar_or_ice = ['0', '50', '75', '100']
toppings_options = ['Boba','Pudding','Red Bean','Grass Jelly','Lychee Jelly','Crystal Boba','None']
payment_methods = ["Cash", "Mobile Pay", "Credit Card"]


while (currentDate <= endDate):
    maxRange = 150
    minRange = 100
    peakDayThreshold = 170

    peakDay = datetime(2025, 8, 25) # for now, peak day will be 8/25/2025 (first day of school)
        
    numOrders = random.randint(minRange, maxRange)

    if currentDate.date() == peakDay.date():
        numOrders = numOrders * 2 #double the 'numOrders' on this specific day
    if currentDate.weekday() >= 5:
        numOrders = int(numOrders * 1.1) #weekends boost by 10%
    if (currentDate.month, currentDate.day) in holidays:
        numOrders = int(numOrders * 1.2) #holidays boost by 20%

    peakDays += 1 if numOrders >= peakDayThreshold else 0
    for _ in range(numOrders):
        # Generate random time for order_date
        hour = random.randint(9, 21) # shop open from 9:00 AM - 9:00 PM
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        order_datetime = datetime.combine(currentDate.date(), datetime.min.time()) + timedelta(hours=hour, minutes=minute, seconds=second)

        numItems = random.randint(1, 5)
        totalPrice = 0
        order_items_for_this_order = []

        for _ in range(numItems):
            prd = random.choice(products)
            productID = int(prd[0])
            base_price = float(prd[2])

            size = random.choice(sizes)
            sugar_level = random.choice(sugar_or_ice)
            ice_level = random.choice(sugar_or_ice)
            # toppings: random subset from toppings_options excluding 'None' if other toppings chosen
            chosen_toppings = random.sample(toppings_options, random.randint(1, 3))
            if 'None' in chosen_toppings and len(chosen_toppings) > 1:
                chosen_toppings.remove('None')
            toppings_str = ','.join(chosen_toppings)

            # Calculate price modifications
            price = base_price
            if size == 'Small':
                price -= 0.5
            elif size == 'Large':
                price += 0.5
            elif size == 'Bucees_Large':
                price += 1.0

            # Charge for toppings except 'None'
            price += 0.5 * len(toppings_str.split(','))

            totalPrice += price

            item = [
                itemID,
                orderID,
                productID,
                size,
                sugar_level,
                ice_level,
                toppings_str,
                round(price,2)
            ]
            order_items_for_this_order.append(item)
            itemID += 1

        tip = round(random.uniform(0,5),2)
        special_notes = fake.sentence() if random.random() < 0.3 else ""
        payment_method = random.choice(payment_methods)

        order = [
            orderID,
            order_datetime.time(),
            order_datetime.day,
            order_datetime.month,
            order_datetime.year,
            round(totalPrice,2),
            tip,
            special_notes,
            payment_method
        ]
        orderID = orderID+1
        totalRevenue += totalPrice
        orders.append(order)
        items.extend(order_items_for_this_order)

    currentDate += timedelta(days=1)



ordersTable     = open('tables/newOrders.csv', 'w', newline='') # using newline just to be safe. 
itemsTable      = open('tables/newItems.csv', 'w', newline='')

writer = csv.writer(itemsTable)
writer.writerow(['item_id','order_id','product_id','size','sugar_level','ice_level','toppings','price'])
writer.writerows(items)

writer = csv.writer(ordersTable)
writer.writerow(['order_id','time','day','month','year','total_price','tip','special_notes','payment_method'])
writer.writerows(orders)

ordersTable.close()
itemsTable.close()
print(f'TOTAL ORDERS: {len(orders)}\nTOTAL ITEMS ORDERED: {len(items)}')

# Merge items
merge_csv_files('tables/items.csv', 'tables/newItems.csv', 'tables/exampleItems.csv')

# Merge orders
merge_csv_files('tables/orders.csv', 'tables/newOrders.csv', 'tables/exampleOrders.csv')
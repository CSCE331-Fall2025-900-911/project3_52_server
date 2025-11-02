import os
import psycopg2
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

# Load environment variables from .env file
load_dotenv()

# Initialize the Flask app
app = Flask(__name__)
# Enable CORS for all routes, allowing your React frontend to make requests
CORS(app)


# Helper function to get a database connection
def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=os.environ.get('DB_HOST'),
            database=os.environ.get('DB_NAME'),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASS')
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None


# --- API Endpoints ---

@app.route('/')
def home():
    """A simple health-check route to see if the server is running."""
    return "TeaFlow API is running!"


@app.route('/api/products', methods=['GET'])
def get_products():
    """
    Function to get all products (menu items).
    Accessible by: Manager, Cashier, Kiosk.
    """
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        # Use a cursor to execute SQL commands
        cur = conn.cursor()
        cur.execute('SELECT * FROM products;')  # Assuming your table is named 'products'

        # Fetch all rows and get column names
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]

        # Convert the list of tuples into a list of dictionaries (JSON-friendly)
        products = [dict(zip(columns, row)) for row in rows]

        cur.close()
        conn.close()

        return jsonify(products)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/products', methods=['POST'])
def add_product():
    """
    Function to add a new product.
    Accessible by: Manager ONLY.
    (Note: We haven't added the security yet, this is just the function)
    """
    # Get the JSON data sent from the frontend
    data = request.get_json()

    # Extract data (you'll want to add error checking here)
    name = data.get('name')
    price = data.get('price')
    ingredients = data.get('ingredients')  # Example field

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cur = conn.cursor()

        # Execute the insert command with sanitized inputs
        cur.execute(
            'INSERT INTO products (name, price, ingredients) VALUES (%s, %s, %s) RETURNING id',
            (name, price, ingredients)
        )

        # Get the ID of the new product
        new_id = cur.fetchone()[0]

        # Commit the transaction to the database
        conn.commit()

        cur.close()
        conn.close()

        # Send a success response back
        return jsonify({"message": "Product added successfully", "id": new_id}), 201

    except Exception as e:
        conn.rollback()  # Roll back changes if an error occurs
        return jsonify({"error": str(e)}), 500


@app.route('/api/orders', methods=['GET'])
def get_orders():
    """
    Function to get the last 1000 orders, most recent first.
    Accessible by: Manager
    """
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cur = conn.cursor()
        # Execute the exact query you specified
        cur.execute('SELECT * FROM orders ORDER BY order_id DESC LIMIT 1000;')

        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]

        # Convert the list of tuples into a list of dictionaries (JSON-friendly)
        orders = [dict(zip(columns, row)) for row in rows]

        cur.close()
        conn.close()

        return jsonify(orders)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/items', methods=['GET'])
def get_items():
    """
    Function to get the last 1000 orders, most recent first.
    Accessible by: Manager
    """
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cur = conn.cursor()
        # Execute the exact query you specified
        cur.execute('SELECT * FROM items ORDER BY item_id DESC LIMIT 1000;')

        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]

        # Convert the list of tuples into a list of dictionaries (JSON-friendly)
        orders = [dict(zip(columns, row)) for row in rows]

        cur.close()
        conn.close()

        return jsonify(orders)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    """
    Function to get the last 1000 orders, most recent first.
    Accessible by: Manager
    """
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cur = conn.cursor()
        # Execute the exact query you specified
        cur.execute('SELECT * FROM inventory;')

        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]

        # Convert the list of tuples into a list of dictionaries (JSON-friendly)
        orders = [dict(zip(columns, row)) for row in rows]

        cur.close()
        conn.close()

        return jsonify(orders)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/employees', methods=['GET'])
def get_employees():
    """
    Function to get the last 1000 orders, most recent first.
    Accessible by: Manager
    """
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cur = conn.cursor()
        # Execute the exact query you specified
        cur.execute('SELECT * FROM staff;')

        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]

        # Convert the list of tuples into a list of dictionaries (JSON-friendly)
        orders = [dict(zip(columns, row)) for row in rows]

        cur.close()
        conn.close()

        return jsonify(orders)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Main entry point to run the server ---
if __name__ == '__main__':
    # Runs the server on http://localhost:5000
    # debug=True means the server will auto-reload when you save the file
    app.run(debug=True, port=5000)
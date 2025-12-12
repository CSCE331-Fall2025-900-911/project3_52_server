# MomTea POS API Server

This is the complete backend server for the TeaFlow Point-of-Sale system. It is built with Python (Flask) and connects to a PostgreSQL database.

The server provides a secure, role-based API for managing products, inventory, staff, and orders, and also integrates with Google OAuth2, Google Translate, and OpenWeatherMap.

---

## Tech Stacks
- **Flask**
- **Google OAuth 2.0**
- **Google Translate Api**
- **Stripe & PayPal SDKs** for payment integration
- **Openweather Api**

---

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.9+
- Postman (or a similar API client) for testing
- Access to the shared PostgreSQL database

---

## 1. Local Setup Instructions

Follow these steps to set up the project on your local machine.

### A. Clone and Install Dependencies

**Clone the Repository:**

```bash
git clone https://github.com/CSCE331-Fall2025-900-911/project3_52_server.git
cd project3_52_server
```

**Create and Activate a Virtual Environment:**  
This is a critical step to keep project libraries isolated.

```bash
# Create the virtual environment
python3 -m venv venv

# Activate it (Mac/Linux)
source venv/bin/activate

# Activate it (Windows)
.\venv\Scripts\activate
```

Your terminal prompt should now start with `(venv)`.

**Install All Required Packages:**

```bash
pip install -r requirements.txt
```

### B. Configure Environment Variables

The server requires a `.env` file to store all secret keys and database credentials. This file is **not** on GitHub and must be created manually.

1. Create a new file named `.env` in the `project3_52_server` root directory.
2. Copy and paste the following content into it, filling in your group's secret values:

```bash
# --- PostgreSQL Database ---
DB_HOST=csce-315-db.engr.tamu.edu
DB_NAME=gang_52_db
DB_USER=YOUR_USERNAME_HERE
DB_PASS=YOUR_PASSWORD_HERE

# --- Flask Session ---
# Generate a long, random string for this
FLASK_SECRET_KEY=YOUR_RANDOM_SECRET_KEY_HERE

# --- Google OAuth2 ---
GOOGLE_OAUTH_CLIENT_ID=YOUR_CLIENT_ID_FROM_GOOGLE
GOOGLE_OAUTH_CLIENT_SECRET=YOUR_CLIENT_SECRET_FROM_GOOGLE

# --- Local Development ONLY ---
# This allows OAuth to run on http://localhost
OAUTHLIB_INSECURE_TRANSPORT=1

# --- 3rd Party API Keys ---
OPENWEATHER_API_KEY=YOUR_OPENWEATHER_API_KEY
GOOGLE_TRANSLATE_API_KEY=YOUR_GOOGLE_TRANSLATE_API_KEY
PAYPAL_CLIENT_ID=YOUR_PAYPAL_CLIENT_ID
PAYPAL_SECRET=YOUR_PAYPAL_SECRET
PAYPAL_API_BASE=https://api-m.sandbox.paypal.com

# --- Frontend URL for Google Oauth Redirect
FRONTEND_URL=YOUR_FRONTEND_URL
```

### C. Sync Database Sequences

You might need to run this one-time fix on the PostgreSQL database before running the server:

```sql
SELECT setval(pg_get_serial_sequence('products', 'product_id'), COALESCE(MAX(product_id), 1)) FROM products;
SELECT setval(pg_get_serial_sequence('inventory', 'inv_item_id'), COALESCE(MAX(inv_item_id), 1)) FROM inventory;
SELECT setval(pg_get_serial_sequence('orders', 'order_id'), COALESCE(MAX(order_id), 1)) FROM orders;
SELECT setval(pg_get_serial_sequence('items', 'item_id'), COALESCE(MAX(item_id), 1)) FROM items;
```

---

## 2. Running the Server

With your virtual environment active and `.env` file configured, you can now run the server:

```bash
python run.py
```

The server will start, and you should see the following output:

```
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
 * Restarting with stat
 * Debugger is active!
```

Your API is now live at [http://localhost:5000](http://localhost:5000).

---

## 3. Testing the API

### A. Testing Public Endpoints

You can test public-facing endpoints (like `GET /api/products` or `GET /api/weather`) directly in your browser or Postman:

- [http://localhost:5000/api/products](http://localhost:5000/api/products)
- [http://localhost:5000/api/weather](http://localhost:5000/api/weather)

### B. Testing Protected (Staff) Endpoints

To test protected routes, you must authenticate as a staff member. This flow must be started in a browser.

#### Log In (Browser):

1. Open your web browser (e.g., Chrome).
2. Go to [http://localhost:5000/api/auth/login](http://localhost:5000/api/auth/login).
3. Log in with a Google account whose email exists in your staff table.
4. You will be redirected to `http://localhost:3000/dashboard` and see a "site not found" error. This is normal and means the login was successful.

#### Get Cookie (Browser):

1. On that same "error" page, open Developer Tools (Inspect).
2. Go to the **Application** tab.
3. Find **Cookies > http://localhost:5000**.
4. Copy the **Value** of the cookie named `session`.


#### Create test data:

1. Run genNewOrders.py with the last date (inclusive) that you want to create order days for up until the current date'
2. Run exportNewOrdersToDB.py to copy all new orders into the AWS databases. Take note of the delete command, as it will allow
for backtracking the export.
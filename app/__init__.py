# server_flask/app/__init__.py

import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv


def create_app():
    # Load environment variables from .env file
    load_dotenv()

    # Initialize the Flask app
    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes

    # --- Register Blueprints ---
    # We import and register each part of our app

    from . import products
    app.register_blueprint(products.products_bp)

    from . import orders
    app.register_blueprint(orders.orders_bp)

    from . import inventory
    app.register_blueprint(inventory.inventory_bp)

    from . import staff
    app.register_blueprint(staff.staff_bp)

    # --- A simple health-check route ---
    @app.route('/')
    def home():
        """A simple health-check route to see if the server is running."""
        return "TeaFlow API is running!"

    return app
# server_flask/app/__init__.py

import os
from flask import Flask, jsonify, session  # Import session
from flask_cors import CORS
from dotenv import load_dotenv
from flask_session import Session  # Import Session


def create_app():
    load_dotenv()

    app = Flask(__name__)
    # --- New Session Config ---
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY")
    # Configure session to use the filesystem (no db needed)
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_PERMANENT"] = True  # Make sessions last
    Session(app)

    # Enable CORS for all routes, and support credentials (cookies)
    CORS(app, supports_credentials=True)

    # --- Register Blueprints ---
    from . import products
    app.register_blueprint(products.products_bp)

    from . import orders
    app.register_blueprint(orders.orders_bp)

    from . import inventory
    app.register_blueprint(inventory.inventory_bp)

    from . import staff
    app.register_blueprint(staff.staff_bp)

    from . import weather
    app.register_blueprint(weather.weather_bp)

    from . import translate
    app.register_blueprint(translate.translate_bp)

    # --- New Auth Blueprint ---
    from . import auth
    # Register the main /api/auth blueprint
    app.register_blueprint(auth.auth_bp)
    # Register the nested /api/auth/google blueprint
    app.register_blueprint(auth.google_bp, url_prefix='/api/auth')

    @app.route('/')
    def home():
        return "TeaFlow API is running!"

    return app
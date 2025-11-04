import os
from flask import Flask, jsonify, session
from flask_cors import CORS
from dotenv import load_dotenv
from flask_session import Session


def create_app():
    load_dotenv()

    app = Flask(__name__)

    # --- Session Config ---
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY")
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_PERMANENT"] = True
    Session(app)

    # --- THIS IS THE CORS FIX ---
    # This configuration explicitly allows your React app (running on localhost:3000)
    # to make requests and send/receive cookies.
    app.config['SESSION_COOKIE_SECURE'] = True  # 1. Must be sent over HTTPS
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # 2. Allow cross-domain
    CORS(
        app,
        # Add all origins your React app might run on
        origins=["http://localhost:3000", "http://127.0.0.1:3000", "https://project3-52.vercel.app", "https://project3-52-git-main-aarons-projects-cc110603.vercel.app"
                 ,"https://project3-52-q917vdn6q-aarons-projects-cc110603.vercel.app"],
        supports_credentials=True
    )
    # --- END FIX ---

    # --- Register Blueprints ---
    from . import products
    app.register_blueprint(products.products_bp)

    from . import orders
    app.register_blueprint(orders.orders_bp)

    from . import inventory
    app.register_blueprint(inventory.inventory_bp)

    from . import staff
    app.register_blueprint(staff.staff_bp)

    from . import auth
    app.register_blueprint(auth.auth_bp)
    app.register_blueprint(auth.google_bp, url_prefix='/api/auth')

    from . import weather
    app.register_blueprint(weather.weather_bp)

    from . import translate
    app.register_blueprint(translate.translate_bp)

    @app.route('/',strict_slashes=False)
    def home():
        """A simple health-check route to see if the server is running."""
        return "TeaFlow API is running!"

    return app


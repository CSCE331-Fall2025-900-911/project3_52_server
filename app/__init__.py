import os
from flask import Flask, jsonify, session, send_from_directory  # 1. Import send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from flask_session import Session


def create_app():
    load_dotenv()

    app = Flask(
        __name__,
        static_folder='../build/static',  # This is correct
        template_folder='../build'  # This is correct
    )

    # --- Session Config ---
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY")
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_PERMANENT"] = True
    Session(app)


    # ---
    # 3. Simplify CORS
    # This is now *only* for local development. It's not used in production.
    # ---
    CORS(
        app,
        origins=["http://localhost:3000", "http://127.0.0.1:3000", "https://project3-52.vercel.app", "https://www.momtea-pos.shop", "https://momtea-pos.shop"],
        supports_credentials=True
    )
    # --- END FIX ---

    # --- Register Blueprints ---
    # (Your blueprints are all correct)
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

    from . import payments
    app.register_blueprint(payments.payments_bp)

    from . import paypal
    app.register_blueprint(paypal.paypal_bp)

    @app.route('/music.mp3')
    def music():
        return send_from_directory(os.path.join(app.template_folder), 'music.mp3')

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.template_folder), 'favicon.ico')

    @app.route('/manifest.json')
    def manifest():
        return send_from_directory(os.path.join(app.template_folder), 'manifest.json')

    @app.route('/android-chrome-192x192.png')
    def android_chrome_192():
        return send_from_directory(os.path.join(app.template_folder), 'android-chrome-192x192.png')

    @app.route('/android-chrome-512x512.png')
    def android_chrome_512():
        return send_from_directory(os.path.join(app.template_folder), 'android-chrome-512x512.png')

    @app.route('/apple-touch-icon.png')
    def apple_touch_icon():
        return send_from_directory(os.path.join(app.template_folder), 'apple-touch-icon.png')

    @app.route('/', defaults={'path': ''}, strict_slashes=False)
    @app.route('/<path:path>', strict_slashes=False)
    def serve_react_app(path):
        # Your API routes are handled by blueprints, so this check is a safeguard
        if path.startswith("api/"):
            return "API route not found", 404

        # If the path is a file in the build folder, serve it
        if path != "" and os.path.exists(os.path.join(app.template_folder, path)):
            return send_from_directory(app.template_folder, path)

        # Otherwise, serve the main index.html (React will handle the page)
        else:
            return send_from_directory(app.template_folder, 'index.html')

    # ---
    # 5. (CRITICAL) FIX THE RETURN STATEMENT
    # ---
    return app  # Was 'return' before
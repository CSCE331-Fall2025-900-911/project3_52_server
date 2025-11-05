import os, requests
from flask import Blueprint, jsonify, request
from dotenv import load_dotenv

load_dotenv()
paypal_bp = Blueprint("paypal", __name__, url_prefix="/api/paypal")

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET")
PAYPAL_API_BASE = os.getenv("PAYPAL_API_BASE", "https://api-m.sandbox.paypal.com")


def get_access_token():
    """Request a short-lived access token from PayPal."""
    auth_response = requests.post(
        f"{PAYPAL_API_BASE}/v1/oauth2/token",
        auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "client_credentials"},
    )
    auth_response.raise_for_status()
    return auth_response.json()["access_token"]


@paypal_bp.route("/create-order", methods=["POST"])
def create_order():
    """Step 1: Create an order."""
    try:
        data = request.get_json()
        amount = data.get("amount")
        if not amount:
            return jsonify({"error": "Missing amount"}), 400

        access_token = get_access_token()
        order_payload = {
            "intent": "CAPTURE",
            "purchase_units": [{"amount": {"currency_code": "USD", "value": str(amount)}}],
        }

        res = requests.post(
            f"{PAYPAL_API_BASE}/v2/checkout/orders",
            json=order_payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        res.raise_for_status()
        return jsonify(res.json())
    except Exception as e:
        print("PayPal create_order error:", e)
        return jsonify({"error": str(e)}), 500


@paypal_bp.route("/capture-order/<order_id>", methods=["POST"])
def capture_order(order_id):
    """Step 3: Capture the approved order."""
    try:
        access_token = get_access_token()
        res = requests.post(
            f"{PAYPAL_API_BASE}/v2/checkout/orders/{order_id}/capture",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        res.raise_for_status()
        return jsonify(res.json())
    except Exception as e:
        print("PayPal capture_order error:", e)
        return jsonify({"error": str(e)}), 500
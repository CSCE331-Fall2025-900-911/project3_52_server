import os
import stripe
from flask import jsonify, request, Blueprint

# Define the blueprint
payments_bp = Blueprint("payments", __name__, url_prefix="/api/pay")

# Load Stripe secret key securely from environment variables
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@payments_bp.route("/", methods=["POST"], strict_slashes=False)
def create_payment_intent():
    try:
        data = request.get_json(force=True)
        amount = data.get("amount")
        if not amount:
            return jsonify({"error": "Missing payment amount"}), 400

        intent = stripe.PaymentIntent.create(
            amount=int(amount),  # must be an integer (in cents)
            currency="usd",
            automatic_payment_methods={"enabled": True},
        )

        return jsonify({"clientSecret": intent.client_secret})
    except Exception as e:
        print("Stripe error:", e)
        return jsonify({"error": str(e)}), 400
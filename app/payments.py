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

@payments_bp.route("/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError:
        return "Invalid signature", 400

    # ✅ Handle payment success event
    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        amount = payment_intent["amount_received"] / 100
        email = payment_intent.get("receipt_email")
        print(f"✅ Payment succeeded for {amount} USD, email={email}")

        # Example: Update order status in DB
        # mark_order_paid(payment_intent["id"], amount)

    return jsonify(success=True), 200
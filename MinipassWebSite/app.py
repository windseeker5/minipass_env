from flask import Flask, render_template, request, redirect, url_for, session, abort, jsonify
from dotenv import load_dotenv
from datetime import datetime, timezone
import stripe
import os
import json
import secrets
import re
from subprocess import run
from shutil import copytree
import threading

from utils.deploy_helpers import insert_admin_user
from utils.email_helpers import init_mail, send_user_deployment_email, send_support_error_email
from utils.mail import mail
import subprocess


import logging
from utils.logging_config import (
    setup_subscription_logger, log_operation_start, log_operation_end, log_validation_check
)

# ✅ Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Initialize subscription logger for webhook operations
subscription_logger = setup_subscription_logger()


 
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
if not app.secret_key:
    raise ValueError("SECRET_KEY environment variable is required!")

app.config.update(
    SESSION_COOKIE_SECURE=True,    # HTTPS only
    SESSION_COOKIE_HTTPONLY=True,  # No JavaScript access
    SESSION_COOKIE_SAMESITE='Lax', # CSRF protection
)

# ✅ Stripe setup
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")

# ✅ Stripe Price ID Configuration for Multi-Tier Subscriptions
STRIPE_PRICES = {
    'basic_monthly': os.getenv('STRIPE_PRICE_BASIC_MONTHLY'),
    'basic_annual': os.getenv('STRIPE_PRICE_BASIC_ANNUAL'),
    'pro_monthly': os.getenv('STRIPE_PRICE_PRO_MONTHLY'),
    'pro_annual': os.getenv('STRIPE_PRICE_PRO_ANNUAL'),
    'ultimate_monthly': os.getenv('STRIPE_PRICE_ULTIMATE_MONTHLY'),
    'ultimate_annual': os.getenv('STRIPE_PRICE_ULTIMATE_ANNUAL'),
}

# ✅ Plan to Tier mapping (for customer container TIER env var)
PLAN_TO_TIER = {
    'basic': 1,
    'pro': 2,
    'ultimate': 3
}

# ✅ Validate all Price IDs are configured
missing_prices = [k for k, v in STRIPE_PRICES.items() if not v]
if missing_prices:
    logging.error(f"⚠️  Missing Stripe Price IDs in .env: {missing_prices}")

# ✅ Flask-Mail setup
init_mail(app)
mail.init_app(app)



# ✅ Footer year context
@app.context_processor
def inject_now():
    return {'now': datetime.now(timezone.utc)}




@app.route("/")
def home():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/politiques")
def politiques():
    return render_template("politiques.html")


@app.route("/check-subdomain", methods=["POST"])
def check_subdomain():
    data = request.get_json()
    name = data.get("subdomain", "").strip().lower()

    from utils.customer_helpers import init_customers_db, subdomain_taken
    init_customers_db()

    subdomain_pattern = re.compile(r'^[a-z0-9][a-z0-9-]{0,61}[a-z0-9]$')
    if not name or not subdomain_pattern.match(name):
        return {"available": False, "error": "Invalid subdomain"}, 200

    if subdomain_taken(name):
        return {"available": False, "error": "Subdomain already taken"}, 200

    return {"available": True}, 200





# ✅ Handle form submit
@app.route("/start-checkout", methods=["POST"])
def start_checkout():
    plan = request.form.get("plan", "basic").lower()
    billing_frequency = request.form.get("billing_frequency", "monthly").lower()  # NEW
    app_name = request.form.get("app_name")
    organization_name = request.form.get("organization_name")
    admin_email = request.form.get("admin_email")
    # Use admin_email as forwarding_email automatically
    forwarding_email = admin_email
    admin_password = secrets.token_urlsafe(12)

    # Validate plan
    if plan not in PLAN_TO_TIER:
        logging.error(f"Invalid plan selected: {plan}")
        return redirect(url_for("home") + "?error=invalid_plan")

    session["checkout_info"] = {
        "plan": plan,
        "billing_frequency": billing_frequency,  # NEW
        "tier": PLAN_TO_TIER[plan],  # NEW
        "app_name": app_name,
        "organization_name": organization_name,
        "admin_email": admin_email,
        "forwarding_email": forwarding_email,
        "admin_password": admin_password
    }

    return redirect(url_for("create_checkout_session"))




# ✅ Stripe session
@app.route("/create-checkout-session", methods=["GET", "POST"])
def create_checkout_session():
    info = session.get("checkout_info", {})
    plan = info.get("plan", "basic").lower()
    billing_frequency = info.get("billing_frequency", "monthly").lower()
    tier = info.get("tier", 1)

    # Build price key and get Stripe Price ID
    price_key = f"{plan}_{billing_frequency}"
    stripe_price_id = STRIPE_PRICES.get(price_key)

    if not stripe_price_id:
        logging.error(f"❌ Stripe Price ID not found for: {price_key}")
        return redirect(url_for("home") + "?error=price_config_error")

    logging.info(f"💳 Creating checkout session: plan={plan}, frequency={billing_frequency}, price_id={stripe_price_id}")

    try:
        session_obj = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": stripe_price_id,  # ✅ Use Stripe Price ID (now recurring)
                "quantity": 1,
            }],
            mode="subscription",  # ✅ CHANGED: Use subscription mode for auto-renewal
            success_url=url_for("deployment_in_progress", _external=True) + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=url_for("home", _external=True) + "?cancelled=true",
            metadata={
                "app_name": info.get("app_name", ""),
                "organization_name": info.get("organization_name", ""),
                "admin_email": info.get("admin_email", ""),
                "forwarding_email": info.get("forwarding_email", ""),
                "admin_password": info.get("admin_password", ""),
                "plan": plan,  # ✅ CRITICAL FIX: Add plan!
                "billing_frequency": billing_frequency,  # ✅ CRITICAL FIX: Add frequency!
                "tier": str(tier)  # ✅ CRITICAL FIX: Add tier!
            },
            subscription_data={
                "metadata": {
                    "app_name": info.get("app_name", ""),
                    "plan": plan,
                    "billing_frequency": billing_frequency,
                    "tier": str(tier)
                }
            }
        )

        session.pop('checkout_info', None)  # Clear sensitive data from session
        return redirect(session_obj.url, code=303)

    except stripe.error.StripeError as e:
        logging.error(f"❌ Stripe error creating checkout session: {e}")
        return redirect(url_for("home") + "?error=checkout_failed")







# ✅ Deployment progress page
@app.route("/deployment-in-progress")
def deployment_in_progress():
    from utils.customer_helpers import get_customer_by_stripe_session_id

    session_id = request.args.get('session_id', '')

    # Fetch customer to get subdomain
    customer = get_customer_by_stripe_session_id(session_id)
    subdomain = customer.get('subdomain', 'votre application') if customer else 'votre application'

    return render_template("deployment_progress.html", session_id=session_id, subdomain=subdomain)


# ✅ TEST PAGE - Deployment progress with mock data
@app.route("/test-deployment-progress")
def test_deployment_progress():
    """
    Test page for deployment progress UI without requiring real deployment.
    Uses mock log data and allows quick iteration on styling/animations.
    """
    return render_template("deployment_progress_test.html")


# ✅ API endpoint for deployment logs
@app.route("/api/deployment-logs/<session_id>")
def get_deployment_logs(session_id):
    """
    Returns deployment logs for a specific Stripe checkout session.
    Filters logs by app_name to show only relevant deployment steps.
    """
    try:
        from utils.customer_helpers import get_customer_by_stripe_session_id
        import os

        # Get customer from database
        customer = get_customer_by_stripe_session_id(session_id)

        if not customer:
            return jsonify({
                "status": "not_started",
                "logs": ["⏳ Waiting for payment confirmation..."],
                "app_name": None,
                "email": None
            })

        app_name = customer.get('app_name', '')
        email = customer.get('email', '')
        deployed = customer.get('deployed', 0)

        # Read log file
        log_file = "subscribed_app.log"
        logs = []

        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                all_lines = f.readlines()

            # Filter logs containing the app_name or session_id
            # Get last 100 lines to avoid reading entire file
            recent_lines = all_lines[-100:] if len(all_lines) > 100 else all_lines

            for line in recent_lines:
                # Filter by app_name
                if app_name and app_name in line:
                    logs.append(line.strip())

        # If no logs yet but customer exists, deployment is starting
        if not logs:
            logs = [f"🚀 Initializing deployment for {app_name}..."]
            status = "starting"
        elif deployed == 1:
            status = "completed"
        else:
            status = "in_progress"

        return jsonify({
            "status": status,
            "logs": logs,
            "app_name": app_name,
            "email": email
        })

    except Exception as e:
        logging.error(f"Error in get_deployment_logs: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "logs": [f"❌ Server error: {str(e)}"],
            "app_name": None,
            "email": None
        }), 500



def process_deployment_async(app_name, admin_email, admin_password, plan_key, port, organization_name,
                              tier, billing_frequency, subscription_start_date, subscription_end_date,
                              stripe_price_id, stripe_checkout_session_id, stripe_customer_id,
                              stripe_subscription_id, payment_amount, currency, email_address, forwarding_email):
    """
    Background worker function to handle deployment asynchronously.
    This runs in a separate thread so the webhook can return immediately.
    """
    from utils.customer_helpers import update_customer_deployment_status
    from utils.deploy_helpers import deploy_customer_container
    from utils.email_helpers import send_user_deployment_email, send_support_error_email
    from utils.mail_integration import setup_customer_email_complete

    # Wrap in Flask app context for email sending
    with app.app_context():
        try:
            subscription_logger.info(f"[{app_name}] 🚀 Background deployment started")

            # Step 1: Deploy container
            subscription_logger.info(f"[{app_name}] 🐳 Deploying customer container")
            success = deploy_customer_container(app_name, admin_email, admin_password, plan_key, port,
                                               organization_name, tier=tier, billing_frequency=billing_frequency,
                                               email_address=email_address)

            if not success:
                subscription_logger.error(f"[{app_name}] ❌ Container deployment failed")
                send_support_error_email(app_name, admin_email, "Container deployment failed")
                return

            log_validation_check(subscription_logger, f"[{app_name}] Container deployment", True, "Container deployed successfully")
            app_url = f"https://{app_name}.minipass.me"

            # Step 2: Setup customer email
            subscription_logger.info(f"[{app_name}] 📧 Setting up customer email")
            from utils.deploy_helpers import is_production_environment
            if is_production_environment():
                setup_customer_email_complete(app_name, admin_password, forwarding_email)
            else:
                subscription_logger.info(f"[{app_name}] ⚠️ LOCAL MODE: Skipping email creation")

            # Step 3: Send deployment email
            subscription_logger.info(f"[{app_name}] 📬 Sending deployment confirmation email")
            email_info = {
                'email_address': email_address,
                'email_password': admin_password,
                'forwarding_setup': True,
                'forwarding_email': forwarding_email
            }
            send_user_deployment_email(admin_email, app_url, admin_password, email_info)

            # Step 4: Mark deployment complete
            subscription_logger.info(f"[{app_name}] ✅ Marking deployment as complete")
            update_customer_deployment_status(app_name, deployed=True)

            subscription_logger.info(f"[{app_name}] 🎉 Deployment completed successfully!")
            log_operation_end(subscription_logger, f"Background Deployment [{app_name}]", success=True)

        except Exception as e:
            subscription_logger.error(f"[{app_name}] ❌ Background deployment failed: {e}")
            import traceback
            traceback.print_exc()
            send_support_error_email(app_name, admin_email, str(e))
            log_operation_end(subscription_logger, f"Background Deployment [{app_name}]", success=False, error_msg=str(e))


# ✅ Webhook listener
@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    import stripe
    import os
    from utils.customer_helpers import (
        init_customers_db, subdomain_taken,
        get_next_available_port, insert_customer, update_customer_email_status,
        update_customer_deployment_status, is_event_processed, mark_event_processed
    )
    from utils.deploy_helpers import insert_admin_user, deploy_customer_container, is_production_environment
    from utils.email_helpers import send_user_deployment_email, send_support_error_email
    from utils.mail_integration import setup_customer_email_complete

    payload = request.data

    subscription_logger.info("📩 Stripe webhook received")
    subscription_logger.info(f"Raw payload length: {len(payload)} bytes")

    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        subscription_logger.info("✅ Webhook signature verified successfully")
    except ValueError:
        subscription_logger.error("❌ Invalid webhook payload received")
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError:
        subscription_logger.error("❌ Invalid webhook signature")
        return "Invalid signature", 400

    if event["type"] == "checkout.session.completed":
        # Check for duplicate event processing
        event_id = event["id"]
        if is_event_processed(event_id):
            subscription_logger.info(f"🔄 Event {event_id} already processed, skipping")
            return "OK - Already processed", 200
        
        # Mark event as processed to prevent duplicates
        mark_event_processed(event_id, event["type"])
        subscription_logger.info(f"🆔 Processing new event: {event_id}")
        
        session_data = event["data"]["object"]
        metadata = session_data.get("metadata", {})

        app_name = metadata.get("app_name", "").strip().lower()
        organization_name = metadata.get("organization_name", "")
        admin_email = metadata.get("admin_email")
        forwarding_email = metadata.get("forwarding_email")
        admin_password = metadata.get("admin_password")
        plan_key = metadata.get("plan", "basic").lower()

        # ✅ NEW: Extract billing frequency and tier
        billing_frequency = metadata.get("billing_frequency", "monthly").lower()
        tier = int(metadata.get("tier", "1"))

        # ✅ NEW: Calculate subscription dates
        from datetime import datetime, timedelta
        subscription_start_date = datetime.now().isoformat()
        if billing_frequency == "monthly":
            end_date = datetime.now() + timedelta(days=30)
        else:  # annual
            end_date = datetime.now() + timedelta(days=365)
        subscription_end_date = end_date.isoformat()

        # ✅ NEW: Extract payment information
        payment_amount = session_data.get("amount_total")  # in cents
        currency = session_data.get("currency", "cad")
        stripe_checkout_session_id = session_data.get("id")

        # ✅ NEW: Extract Stripe Customer and Subscription IDs
        stripe_customer_id = session_data.get("customer")
        stripe_subscription_id = session_data.get("subscription")
        subscription_logger.info(f"💳 Stripe Customer ID: {stripe_customer_id}")
        subscription_logger.info(f"🔄 Stripe Subscription ID: {stripe_subscription_id}")

        # Get stripe_price_id from line_items if available
        stripe_price_id = None
        try:
            line_items_response = stripe.checkout.Session.list_line_items(stripe_checkout_session_id, limit=1)
            if line_items_response.data:
                stripe_price_id = line_items_response.data[0].price.id
        except:
            subscription_logger.warning("⚠️ Could not retrieve Stripe Price ID from line items")

        log_operation_start(subscription_logger, "Customer Subscription Processing",
                           app_name=app_name,
                           admin_email=admin_email,
                           plan=plan_key,
                           billing_frequency=billing_frequency,
                           tier=tier,
                           organization_name=organization_name,
                           forwarding_email=forwarding_email)

        try:
            # Step 1: Initialize database and validate subdomain
            subscription_logger.info("🧠 Step 1: Validating subdomain availability")
            init_customers_db()
            if subdomain_taken(app_name):
                error_msg = f"Subdomain '{app_name}' is already taken"
                log_validation_check(subscription_logger, "Subdomain availability", False, error_msg)
                raise ValueError(error_msg)
            else:
                log_validation_check(subscription_logger, "Subdomain availability", True, f"Subdomain '{app_name}' is available")

            # Step 2: Assign resources
            subscription_logger.info("🔢 Step 2: Assigning resources for deployment")
            port = get_next_available_port()
            email_address = f"{app_name}_app@minipass.me"
            subscription_logger.info(f"   📦 Assigned port: {port}")
            subscription_logger.info(f"   📧 Generated email: {email_address}")

            # Step 3: Create customer record IMMEDIATELY (so progress page can track it)
            subscription_logger.info(f"📝 Step 3: Creating customer record for tracking")
            insert_customer(
                admin_email, app_name, app_name, plan_key, admin_password, port,
                email_address=email_address, forwarding_email=forwarding_email,
                email_status='pending', organization_name=organization_name,
                billing_frequency=billing_frequency,
                subscription_start_date=subscription_start_date,
                subscription_end_date=subscription_end_date,
                stripe_price_id=stripe_price_id,
                stripe_checkout_session_id=stripe_checkout_session_id,
                stripe_customer_id=stripe_customer_id,
                stripe_subscription_id=stripe_subscription_id,
                payment_amount=payment_amount,
                currency=currency,
                subscription_status='active'
            )
            subscription_logger.info(f"✅ Customer record created - deployment can now be tracked")

            # Step 4: Launch background deployment thread
            subscription_logger.info(f"🚀 Step 4: Launching background deployment for {app_name}")
            deployment_thread = threading.Thread(
                target=process_deployment_async,
                args=(app_name, admin_email, admin_password, plan_key, port, organization_name,
                      tier, billing_frequency, subscription_start_date, subscription_end_date,
                      stripe_price_id, stripe_checkout_session_id, stripe_customer_id,
                      stripe_subscription_id, payment_amount, currency, email_address, forwarding_email),
                daemon=True
            )
            deployment_thread.start()
            subscription_logger.info(f"✅ Background deployment thread started for {app_name}")
            log_operation_end(subscription_logger, "Customer Subscription Processing (Webhook)", success=True)

            # Return 200 OK immediately - deployment continues in background
            return "OK - Deployment in progress", 200

        except Exception as e:
            error_msg = f"Webhook processing error: {str(e)}"
            subscription_logger.error(f"❌ {error_msg}")
            log_operation_end(subscription_logger, "Customer Subscription Processing (Webhook)", success=False, error_msg=error_msg)
            send_support_error_email(app_name, admin_email, error_msg)
            return "Webhook processing failed", 500

    elif event["type"] == "invoice.payment_succeeded":
        # Handle successful subscription renewal
        from datetime import datetime, timedelta
        from utils.customer_helpers import get_customer_by_stripe_subscription_id, update_customer_stripe_ids

        invoice = event["data"]["object"]
        stripe_subscription_id = invoice.get("subscription")

        if not stripe_subscription_id:
            subscription_logger.warning("⚠️ No subscription ID in invoice.payment_succeeded event")
            return "OK", 200

        subscription_logger.info(f"💰 Successful renewal payment for subscription: {stripe_subscription_id}")

        # Look up customer by subscription ID
        customer = get_customer_by_stripe_subscription_id(stripe_subscription_id)
        if customer:
            subdomain = customer['subdomain']
            billing_frequency = customer['billing_frequency']

            # Update subscription end date
            from utils.customer_helpers import subdomain_taken
            import sqlite3
            CUSTOMERS_DB = "customers.db"
            with sqlite3.connect(CUSTOMERS_DB) as conn:
                cur = conn.cursor()

                # Calculate new end date
                if billing_frequency == "monthly":
                    new_end_date = (datetime.now() + timedelta(days=30)).isoformat()
                else:  # annual
                    new_end_date = (datetime.now() + timedelta(days=365)).isoformat()

                cur.execute("""
                    UPDATE customers
                    SET subscription_end_date = ?,
                        subscription_status = 'active'
                    WHERE subdomain = ?
                """, (new_end_date, subdomain))
                conn.commit()

            subscription_logger.info(f"✅ Subscription renewed for {subdomain} until {new_end_date}")
        else:
            subscription_logger.warning(f"⚠️ Customer not found for subscription ID: {stripe_subscription_id}")

    elif event["type"] == "invoice.payment_failed":
        # Handle failed subscription renewal
        from utils.customer_helpers import get_customer_by_stripe_subscription_id

        invoice = event["data"]["object"]
        stripe_subscription_id = invoice.get("subscription")

        if not stripe_subscription_id:
            subscription_logger.warning("⚠️ No subscription ID in invoice.payment_failed event")
            return "OK", 200

        subscription_logger.warning(f"⚠️ Failed renewal payment for subscription: {stripe_subscription_id}")

        # Look up customer and update status
        customer = get_customer_by_stripe_subscription_id(stripe_subscription_id)
        if customer:
            subdomain = customer['subdomain']
            import sqlite3
            CUSTOMERS_DB = "customers.db"
            with sqlite3.connect(CUSTOMERS_DB) as conn:
                cur = conn.cursor()
                cur.execute("""
                    UPDATE customers
                    SET subscription_status = 'past_due'
                    WHERE subdomain = ?
                """, (subdomain,))
                conn.commit()

            subscription_logger.warning(f"⚠️ Subscription marked as past_due for {subdomain}")
            # TODO: Send payment failed notification email to customer
        else:
            subscription_logger.warning(f"⚠️ Customer not found for subscription ID: {stripe_subscription_id}")

    elif event["type"] == "customer.subscription.deleted":
        # Handle subscription cancellation
        from utils.customer_helpers import get_customer_by_stripe_subscription_id

        subscription_obj = event["data"]["object"]
        stripe_subscription_id = subscription_obj.get("id")

        subscription_logger.info(f"🚫 Subscription cancelled: {stripe_subscription_id}")

        # Look up customer and update status
        customer = get_customer_by_stripe_subscription_id(stripe_subscription_id)
        if customer:
            subdomain = customer['subdomain']
            import sqlite3
            CUSTOMERS_DB = "customers.db"
            with sqlite3.connect(CUSTOMERS_DB) as conn:
                cur = conn.cursor()
                cur.execute("""
                    UPDATE customers
                    SET subscription_status = 'cancelled'
                    WHERE subdomain = ?
                """, (subdomain,))
                conn.commit()

            subscription_logger.info(f"✅ Subscription marked as cancelled for {subdomain}")
            # Note: Container will remain deployed until subscription_end_date
            # TODO: Add scheduled job to stop container after end date
        else:
            subscription_logger.warning(f"⚠️ Customer not found for subscription ID: {stripe_subscription_id}")

    return "OK", 200



# ✅ Run server
if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=5000)

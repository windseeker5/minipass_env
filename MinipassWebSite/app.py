from flask import Flask, render_template, request, redirect, url_for, session, abort, jsonify, flash
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
import markdown
from functools import wraps

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


@app.route("/guides")
def guides():
    return render_template("guides.html")


@app.route("/guides/<slug>")
def guide_detail(slug):
    # Path to markdown file
    doc_path = os.path.join(app.static_folder, 'docs', f'{slug}.md')

    if not os.path.exists(doc_path):
        abort(404)

    # Read and convert markdown to HTML
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()

    html_content = markdown.markdown(content, extensions=['tables', 'fenced_code', 'toc'])

    return render_template('guide-detail.html', content=html_content, slug=slug)


@app.route("/politiques")
def politiques():
    return render_template("politiques.html")


@app.route("/sitemap.xml")
def sitemap():
    from flask import Response
    import glob as _glob

    base_url = "https://minipass.me"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    static_pages = [
        ("", "weekly", "1.0"),
        ("/about", "monthly", "0.8"),
        ("/guides", "weekly", "0.9"),
        ("/politiques", "monthly", "0.5"),
    ]

    docs_dir = os.path.join(app.static_folder, "docs")
    guide_slugs = [
        os.path.splitext(os.path.basename(f))[0]
        for f in _glob.glob(os.path.join(docs_dir, "*.md"))
    ]

    urls = []
    for path, changefreq, priority in static_pages:
        urls.append(
            f"  <url>\n"
            f"    <loc>{base_url}{path}</loc>\n"
            f"    <lastmod>{today}</lastmod>\n"
            f"    <changefreq>{changefreq}</changefreq>\n"
            f"    <priority>{priority}</priority>\n"
            f"  </url>"
        )
    for slug in sorted(guide_slugs):
        urls.append(
            f"  <url>\n"
            f"    <loc>{base_url}/guides/{slug}</loc>\n"
            f"    <lastmod>{today}</lastmod>\n"
            f"    <changefreq>monthly</changefreq>\n"
            f"    <priority>0.7</priority>\n"
            f"  </url>"
        )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>"
    )
    return Response(xml, mimetype="application/xml")


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


# ✅ Promo code validation (AJAX, read-only)
@app.route("/validate-promo-code", methods=["POST"])
def validate_promo_code_route():
    from utils.customer_helpers import init_customers_db, validate_promo_code
    init_customers_db()
    data = request.get_json()
    code = (data.get("code") or "").strip()
    if not code:
        return jsonify({"valid": False, "error": "Code manquant"}), 400
    result = validate_promo_code(code)
    return jsonify(result)


# ✅ Promo code redemption (full Stripe bypass)
@app.route("/redeem-promo", methods=["POST"])
def redeem_promo():
    from utils.customer_helpers import (
        init_customers_db, validate_promo_code, redeem_promo_code,
        subdomain_taken, get_next_available_port, insert_customer
    )

    init_customers_db()

    app_name = (request.form.get("app_name") or "").strip().lower()
    organization_name = (request.form.get("organization_name") or "").strip()
    admin_email = (request.form.get("admin_email") or "").strip()
    promo_code = (request.form.get("promo_code") or "").strip()

    # Server-side re-validation (never trust client state)
    if not app_name or not admin_email or not promo_code:
        return redirect(url_for("home") + "?error=missing_fields")

    validation = validate_promo_code(promo_code)
    if not validation.get("valid"):
        return redirect(url_for("home") + "?error=invalid_promo")

    subdomain_pattern = re.compile(r'^[a-z0-9][a-z0-9-]{0,61}[a-z0-9]$|^[a-z0-9]{1,2}$')
    if not subdomain_pattern.match(app_name):
        return redirect(url_for("home") + "?error=invalid_subdomain")

    if subdomain_taken(app_name):
        return redirect(url_for("home") + "?error=subdomain_taken")

    plan = validation["plan"]
    tier = validation["tier"]
    billing_frequency = validation["billing_frequency"]
    admin_password = secrets.token_urlsafe(12)
    promo_session_id = "promo_" + secrets.token_urlsafe(24)
    port = get_next_available_port()
    email_address = f"{app_name}_app@minipass.me"
    forwarding_email = admin_email

    from datetime import timedelta
    subscription_start_date = datetime.now().isoformat()
    subscription_end_date = (datetime.now() + timedelta(days=365)).isoformat()

    # Atomic mark-as-used (race condition guard)
    if not redeem_promo_code(promo_code, app_name):
        return redirect(url_for("home") + "?error=promo_already_used")

    insert_customer(
        admin_email, app_name, app_name, plan, admin_password, port,
        email_address=email_address, forwarding_email=forwarding_email,
        email_status='pending', organization_name=organization_name,
        billing_frequency=billing_frequency,
        subscription_start_date=subscription_start_date,
        subscription_end_date=subscription_end_date,
        stripe_checkout_session_id=promo_session_id,
        payment_amount=0,
        currency='cad',
        subscription_status='active'
    )

    logging.info(f"🎁 Promo code '{promo_code}' redeemed for {app_name} ({admin_email}) — session {promo_session_id}")

    deployment_thread = threading.Thread(
        target=process_deployment_async,
        args=(app_name, admin_email, admin_password, plan, port, organization_name,
              tier, billing_frequency, subscription_start_date, subscription_end_date,
              None, promo_session_id, None, None, 0, 'cad', email_address, forwarding_email),
        daemon=True
    )
    deployment_thread.start()

    return redirect(url_for("deployment_in_progress") + f"?session_id={promo_session_id}")





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
                send_support_error_email(admin_email, app_name, "Container deployment failed")
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
            send_support_error_email(admin_email, app_name, str(e))
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
            send_support_error_email(admin_email, app_name, error_msg)
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

    elif event["type"] == "customer.subscription.updated":
        from utils.customer_helpers import get_customer_by_stripe_subscription_id, update_customer_plan
        from utils.deploy_helpers import set_stripe_subscription_settings_to_database
        import os

        subscription_obj = event["data"]["object"]
        stripe_subscription_id = subscription_obj.get("id")

        subscription_logger.info(f"🔄 customer.subscription.updated: {stripe_subscription_id}")

        customer = get_customer_by_stripe_subscription_id(stripe_subscription_id)
        if not customer:
            subscription_logger.warning(f"⚠️ No customer found for subscription: {stripe_subscription_id}")
            return "OK", 200

        subdomain = customer['subdomain']

        # Determine new plan from price ID (may be unchanged for cancel/reactivate flips)
        new_price_id = None
        try:
            items = subscription_obj.get("items", {}).get("data", [])
            if items:
                new_price_id = items[0]["price"]["id"]
        except (KeyError, IndexError, TypeError):
            pass

        # Build reverse price-ID → plan_key mapping from env
        price_to_plan = {v: k for k, v in STRIPE_PRICES.items() if v}
        plan_key = price_to_plan.get(new_price_id) if new_price_id else None

        # Update plan/billing columns only when price changed
        if plan_key:
            plan_name, billing_frequency = plan_key.rsplit('_', 1)
            update_customer_plan(
                subdomain,
                plan=plan_name,
                billing_frequency=billing_frequency,
                stripe_price_id=new_price_id
            )
            subscription_logger.info(f"✅ Plan updated for {subdomain}: {plan_key}")

            # Update the customer app's Setting table
            try:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                db_path = os.path.join(base_dir, "..", "deployed", subdomain, "app", "instance", "minipass.db")
                db_path = os.path.normpath(db_path)
                if os.path.exists(db_path):
                    tier_map = {'basic': 1, 'pro': 2, 'ultimate': 3}
                    tier = tier_map.get(plan_name, customer.get('plan', 'basic'))
                    set_stripe_subscription_settings_to_database(
                        db_path,
                        customer.get('stripe_customer_id', ''),
                        stripe_subscription_id,
                        customer.get('payment_amount', ''),
                        customer.get('subscription_end_date', ''),
                        tier,
                        billing_frequency
                    )
                    subscription_logger.info(f"✅ Setting table updated for {subdomain}")
                else:
                    subscription_logger.warning(f"⚠️ DB not found at {db_path}")
            except Exception as e:
                subscription_logger.error(f"❌ Failed to update Setting table for {subdomain}: {e}")
        else:
            subscription_logger.info(f"ℹ️ No price change for {subdomain} — cancel/reactivate flip only")

        # Always sync subscription_status from Stripe
        update_customer_plan(subdomain, subscription_status=subscription_obj.get("status", "active"))

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


# ============================================================================
# ADMIN TOOLS
# ============================================================================

def require_admin(f):
    """Decorator to require admin authentication for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_authenticated'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Admin login page."""
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == os.getenv("ADMIN_PASSWORD"):
            session['admin_authenticated'] = True
            return redirect(url_for('admin_tools'))
        return render_template("admin/login.html", error="Invalid password")
    return render_template("admin/login.html")


@app.route("/admin/logout")
def admin_logout():
    """Admin logout - clear session."""
    session.pop('admin_authenticated', None)
    return redirect(url_for('admin_login'))


@app.route("/admin/tools")
@require_admin
def admin_tools():
    """Main admin tools page with customer list and email tools."""
    from utils.customer_helpers import get_all_customers
    from utils.deploy_helpers import is_production_environment

    customers = get_all_customers()
    is_prod = is_production_environment()

    # Get email config info for display
    if is_prod:
        email_server = os.getenv("PROD_MAIL_SERVER", "mail.minipass.me")
        email_sender = os.getenv("PROD_MAIL_DEFAULT_SENDER", "support@minipass.me")
    else:
        email_server = os.getenv("MAIL_SERVER", "smtp.gmail.com")
        email_sender = os.getenv("MAIL_DEFAULT_SENDER", "info@minipass.me")

    return render_template(
        "admin/tools.html",
        customers=customers,
        is_production=is_prod,
        email_server=email_server,
        email_sender=email_sender,
        message=request.args.get('message'),
        error=request.args.get('error')
    )


@app.route("/admin/test-email", methods=["POST"])
@require_admin
def admin_test_email():
    """Send a test email to verify email configuration."""
    from utils.deploy_helpers import is_production_environment
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    import smtplib

    recipient = request.form.get("recipient", "").strip()
    if not recipient:
        return redirect(url_for('admin_tools', error="Recipient email is required"))

    try:
        # Get SMTP settings based on environment
        if is_production_environment():
            smtp_server = os.getenv("PROD_MAIL_SERVER", "mail.minipass.me")
            smtp_port = int(os.getenv("PROD_MAIL_PORT", 587))
            smtp_user = os.getenv("PROD_MAIL_USERNAME", "support@minipass.me")
            smtp_pass = os.getenv("PROD_MAIL_PASSWORD")
            sender = os.getenv("PROD_MAIL_DEFAULT_SENDER", "minipass <support@minipass.me>")
            env_name = "Production (minipass.me)"
        else:
            smtp_server = os.getenv("MAIL_SERVER", "smtp.gmail.com")
            smtp_port = int(os.getenv("MAIL_PORT", 587))
            smtp_user = os.getenv("MAIL_USERNAME")
            smtp_pass = os.getenv("MAIL_PASSWORD")
            sender = os.getenv("MAIL_DEFAULT_SENDER", "info@minipass.me")
            env_name = "Development (Gmail)"

        # Build test email
        msg = MIMEMultipart()
        msg['Subject'] = f"[minipass] Test Email - {env_name}"
        msg['From'] = sender
        msg['To'] = recipient

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>minipass Test Email</h2>
            <p>This is a test email from the minipass admin tools.</p>
            <hr>
            <p><strong>Environment:</strong> {env_name}</p>
            <p><strong>SMTP Server:</strong> {smtp_server}:{smtp_port}</p>
            <p><strong>Sender:</strong> {sender}</p>
            <p><strong>Sent at:</strong> {datetime.now().isoformat()}</p>
            <hr>
            <p style="color: green;">If you received this email, your email configuration is working correctly!</p>
        </body>
        </html>
        """
        msg.attach(MIMEText(html, 'html'))

        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        return redirect(url_for('admin_tools', message=f"Test email sent to {recipient}"))

    except Exception as e:
        logging.error(f"Failed to send test email: {e}")
        return redirect(url_for('admin_tools', error=f"Failed to send email: {str(e)}"))


@app.route("/admin/resend-email/<subdomain>", methods=["POST"])
@require_admin
def admin_resend_email(subdomain):
    """Resend onboarding email to a customer."""
    from utils.customer_helpers import get_customer_by_subdomain

    customer = get_customer_by_subdomain(subdomain)
    if not customer:
        return redirect(url_for('admin_tools', error=f"Customer not found: {subdomain}"))

    try:
        # Build the app URL
        app_url = f"https://{subdomain}.minipass.me"

        # Get email info
        email_info = {
            'email_address': customer.get('email_address'),
            'email_password': customer.get('email_password'),
            'forwarding_setup': customer.get('forwarding_email') is not None,
            'forwarding_email': customer.get('forwarding_email')
        }

        # Note: We use the stored password (email_password field stores plaintext)
        admin_password = customer.get('email_password', 'See your original email')

        send_user_deployment_email(
            to=customer['email'],
            url=app_url,
            password=admin_password,
            email_info=email_info
        )

        return redirect(url_for('admin_tools', message=f"Onboarding email resent to {customer['email']}"))

    except Exception as e:
        logging.error(f"Failed to resend email for {subdomain}: {e}")
        return redirect(url_for('admin_tools', error=f"Failed to resend email: {str(e)}"))


@app.route("/admin/reset-password/<subdomain>", methods=["POST"])
@require_admin
def admin_reset_password(subdomain):
    """Generate a new password, reset it inside the container, and email the admin."""
    from utils.customer_helpers import (
        get_customer_by_subdomain, update_customer_password,
        reset_container_admin_password,
    )
    from utils.email_helpers import send_password_reset_email

    customer = get_customer_by_subdomain(subdomain)
    if not customer:
        return redirect(url_for('admin_tools', error=f"Customer not found: {subdomain}"))

    # admin_email is required — sent by the modal form
    admin_email = (request.form.get('admin_email') or '').strip()
    if not admin_email or not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', admin_email):
        return redirect(url_for('admin_tools', error="Invalid or missing admin email"))

    try:
        new_password = secrets.token_urlsafe(12)

        # 1. Reset password inside the container's SQLite DB
        reset_container_admin_password(subdomain, admin_email, new_password)

        # 2. Keep customers.db in sync (legacy field)
        update_customer_password(subdomain, new_password)

        # 3. Email the reset password to the admin whose account was changed
        app_url = f"https://{subdomain}.minipass.me"
        send_password_reset_email(
            to=admin_email,
            subdomain=subdomain,
            app_url=app_url,
            new_password=new_password
        )

        return redirect(url_for('admin_tools', message=f"Password reset email sent to {admin_email}"))

    except Exception as e:
        logging.error(f"Failed to reset password for {subdomain}: {e}")
        return redirect(url_for('admin_tools', error=f"Failed to reset password: {str(e)}"))


@app.route("/admin/api/container-admins/<subdomain>")
@require_admin
def admin_get_container_admins(subdomain):
    """Return JSON list of admins inside a customer's container (used by the reset-password modal)."""
    from utils.customer_helpers import get_container_admins
    try:
        admins = get_container_admins(subdomain)
        return jsonify({"success": True, "admins": admins})
    except Exception as e:
        logging.error(f"Failed to list admins for {subdomain}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/admin/delete-customer/<subdomain>", methods=["POST"])
@require_admin
def admin_delete_customer(subdomain):
    """Perform a complete teardown of a customer deployment."""
    import re as _re
    from utils.cleanup_helpers import delete_customer_complete
    from utils.customer_helpers import get_customer_by_subdomain

    if not _re.match(r'^[a-zA-Z0-9-]+$', subdomain):
        return jsonify({"success": False, "error": "Invalid subdomain format.", "results": []}), 400

    try:
        body = request.get_json(force=True) or {}
    except Exception:
        body = {}

    if body.get("confirm_subdomain") != subdomain:
        return jsonify({"success": False, "error": "Subdomain confirmation does not match.", "results": []}), 400

    if not get_customer_by_subdomain(subdomain):
        return jsonify({"success": False, "error": f"Customer '{subdomain}' not found.", "results": []}), 404

    try:
        results = delete_customer_complete(subdomain)
        success = all(r["status"] in ("ok", "warning") for r in results)
        logging.info(f"Admin deleted customer '{subdomain}': success={success}")
        return jsonify({"success": success, "subdomain": subdomain, "results": results})
    except Exception as e:
        logging.error(f"Admin delete customer '{subdomain}' unexpected error: {e}")
        return jsonify({"success": False, "error": str(e), "results": []}), 500


# ✅ Admin promo codes
@app.route("/admin/promo-codes")
@require_admin
def admin_promo_codes():
    from utils.customer_helpers import init_customers_db, get_all_promo_codes
    init_customers_db()
    codes = get_all_promo_codes()
    return render_template("admin/promo_codes.html", codes=codes,
                           message=request.args.get('message'),
                           error=request.args.get('error'),
                           now=datetime.utcnow())


@app.route("/admin/promo-codes/create", methods=["POST"])
@require_admin
def admin_create_promo_code():
    from utils.customer_helpers import init_customers_db, create_promo_code
    init_customers_db()

    code = (request.form.get("code") or "").strip().upper()
    plan = request.form.get("plan", "pro").lower()
    tier = PLAN_TO_TIER.get(plan, 2)
    billing_frequency = request.form.get("billing_frequency", "annual").lower()
    max_uses_raw = request.form.get("max_uses", "1").strip()
    expires_at = request.form.get("expires_at", "").strip() or None
    notes = request.form.get("notes", "").strip() or None

    try:
        max_uses = int(max_uses_raw)
        if max_uses < 1:
            raise ValueError
    except ValueError:
        return redirect(url_for("admin_promo_codes", error="Nombre d'utilisations invalide"))

    if not code:
        return redirect(url_for("admin_promo_codes", error="Code requis"))

    success = create_promo_code(code, plan=plan, tier=tier, billing_frequency=billing_frequency,
                                max_uses=max_uses, expires_at=expires_at, notes=notes)
    if success:
        return redirect(url_for("admin_promo_codes", message=f"Code '{code}' créé avec succès"))
    else:
        return redirect(url_for("admin_promo_codes", error=f"Le code '{code}' existe déjà"))


@app.route("/admin/promo-codes/delete/<code>", methods=["POST"])
@require_admin
def admin_delete_promo_code(code):
    from utils.customer_helpers import init_customers_db, delete_promo_code
    init_customers_db()
    ok = delete_promo_code(code)
    if ok:
        return redirect(url_for("admin_promo_codes", message=f"Code '{code}' supprimé"))
    return redirect(url_for("admin_promo_codes", error=f"Code '{code}' introuvable"))


@app.route("/admin/promo-codes/update/<code>", methods=["POST"])
@require_admin
def admin_update_promo_code(code):
    from utils.customer_helpers import init_customers_db, update_promo_code
    init_customers_db()
    plan = request.form.get("plan", "pro").lower()
    tier = PLAN_TO_TIER.get(plan, 2)
    billing_frequency = request.form.get("billing_frequency", "annual").lower()
    try:
        max_uses = max(1, int(request.form.get("max_uses", "1")))
    except ValueError:
        return redirect(url_for("admin_promo_codes", error="Nombre d'utilisations invalide"))
    expires_at = request.form.get("expires_at", "").strip() or None
    notes = request.form.get("notes", "").strip() or None
    ok = update_promo_code(code, plan, tier, billing_frequency, max_uses, expires_at, notes)
    if ok:
        return redirect(url_for("admin_promo_codes", message=f"Code '{code}' mis à jour"))
    return redirect(url_for("admin_promo_codes", error=f"Code '{code}' introuvable"))


def classify_error(msg):
    """Return a short plain-English label for a raw Postfix error string."""
    if not msg:
        return "Unknown error"
    m = msg.lower()
    if '421-4.7.28' in m or 'unsolicitedrate' in m:
        return "Gmail rate limit — IP block (temporary, Postfix will retry)"
    if '421-4.7.26' in m:
        return "Gmail SPF/DMARC issue (temporary)"
    if "user doesn't exist" in m or '5.1.1' in m:
        return "Recipient doesn't exist on this server"
    if '5.7.1' in m:
        return "Rejected by spam/policy filter"
    if '421' in m:
        return "Temporary rejection — Postfix will retry"
    if '550' in m:
        return "Permanent bounce"
    return "Delivery failure"


# ✅ Email Analytics Dashboard
@app.route("/admin/mail-dashboard")
@require_admin
def mail_dashboard():
    """Email analytics dashboard — reads from email_monitoring/monitoring.db."""
    import sqlite3 as _sqlite3
    from datetime import date as _date, timedelta as _timedelta

    db_path = os.path.join(os.path.dirname(__file__), '..', 'email_monitoring', 'monitoring.db')

    stats = {
        'sent_today': 0,
        'sent_week': 0,
        'success_rate': 100,
        'failures_week': 0,
    }
    chart_data = {'labels': [], 'sent': [], 'bounced': [], 'deferred': [], 'success_rate': []}
    failures = []
    sender_stats = []
    queue_snapshot = None
    mailbox_sizes = []
    mailbox_date = None

    try:
        conn = _sqlite3.connect(db_path)
        conn.row_factory = _sqlite3.Row
        cur = conn.cursor()

        today = _date.today().isoformat()
        week_ago = (_date.today() - _timedelta(days=6)).isoformat()

        # --- Stat cards ---
        row = cur.execute(
            "SELECT SUM(sent_count) FROM email_volume_daily WHERE date = ?", (today,)
        ).fetchone()
        stats['sent_today'] = row[0] or 0

        row = cur.execute(
            "SELECT SUM(sent_count), SUM(bounced_count), SUM(deferred_count) "
            "FROM email_volume_daily WHERE date >= ?", (week_ago,)
        ).fetchone()
        w_sent = row[0] or 0
        w_bounced = row[1] or 0
        w_deferred = row[2] or 0
        stats['sent_week'] = w_sent
        if w_sent > 0:
            stats['success_rate'] = round(100 * (w_sent - w_bounced) / w_sent, 1)

        row = cur.execute(
            "SELECT COUNT(*) FROM email_failures WHERE timestamp >= ?", (week_ago,)
        ).fetchone()
        stats['failures_week'] = row[0] or 0

        # --- Chart data (7 days) ---
        rows = cur.execute(
            "SELECT date, SUM(sent_count), SUM(bounced_count), SUM(deferred_count) "
            "FROM email_volume_daily WHERE date >= ? GROUP BY date ORDER BY date",
            (week_ago,)
        ).fetchall()
        for r in rows:
            d_sent = r[1] or 0
            d_bounced = r[2] or 0
            d_deferred = r[3] or 0
            d_success = round(100 * (d_sent - d_bounced) / d_sent, 1) if d_sent > 0 else 100
            chart_data['labels'].append(r[0][5:])  # MM-DD
            chart_data['sent'].append(d_sent)
            chart_data['bounced'].append(d_bounced)
            chart_data['deferred'].append(d_deferred)
            chart_data['success_rate'].append(d_success)

        # --- Recent failures ---
        rows = cur.execute(
            "SELECT timestamp, from_user, to_address, error_message, status "
            "FROM email_failures ORDER BY timestamp DESC LIMIT 200"
        ).fetchall()
        failures = [dict(r) for r in rows]
        for f in failures:
            f['reason'] = classify_error(f.get('error_message'))
            if f.get('status') == 'deferred':
                failure_date = (f.get('timestamp') or '')[:10]
                later = cur.execute(
                    "SELECT SUM(sent_count) AS later_sent FROM email_volume_daily "
                    "WHERE user_email = ? AND date > ?",
                    (f.get('from_user') or '', failure_date)
                ).fetchone()
                f['resolution'] = 'likely_delivered' if (later and later['later_sent']) else None
            else:
                f['resolution'] = None

        # --- Per-sender breakdown ---
        rows = cur.execute(
            "SELECT user_email, "
            "  SUM(CASE WHEN date = ? THEN sent_count ELSE 0 END) AS today_sent, "
            "  SUM(CASE WHEN date = ? THEN bounced_count ELSE 0 END) AS today_bounced, "
            "  SUM(sent_count) AS week_sent, "
            "  SUM(bounced_count) AS week_bounced, "
            "  SUM(deferred_count) AS week_deferred "
            "FROM email_volume_daily WHERE date >= ? GROUP BY user_email ORDER BY week_sent DESC",
            (today, today, week_ago)
        ).fetchall()
        for r in rows:
            ws = r['week_sent'] or 0
            wb = r['week_bounced'] or 0
            wd = r['week_deferred'] or 0
            pct = round(100 * (ws - wb) / ws, 1) if ws > 0 else 100
            sender_stats.append({
                'user_email': r['user_email'],
                'today_sent': r['today_sent'] or 0,
                'today_bounced': r['today_bounced'] or 0,
                'week_sent': ws,
                'week_deferred': wd,
                'success_pct': pct,
            })

        # --- Queue snapshot ---
        row = cur.execute(
            "SELECT timestamp, queue_size, oldest_age_minutes "
            "FROM mail_queue_log ORDER BY timestamp DESC LIMIT 1"
        ).fetchone()
        if row:
            queue_snapshot = dict(row)

        # --- Mailbox sizes ---
        row = cur.execute("SELECT MAX(date) FROM mailbox_sizes").fetchone()
        mailbox_date = row[0] if row else None
        if mailbox_date:
            rows = cur.execute(
                "SELECT user_email, size_mb FROM mailbox_sizes WHERE date = ? ORDER BY size_mb DESC",
                (mailbox_date,)
            ).fetchall()
            mailbox_sizes = [dict(r) for r in rows]

        conn.close()

    except Exception as e:
        logging.warning(f"mail_dashboard DB error: {e}")

    return render_template(
        'admin/mail_dashboard.html',
        stats=stats,
        chart_data=chart_data,
        failures=failures,
        sender_stats=sender_stats,
        queue_snapshot=queue_snapshot,
        mailbox_sizes=mailbox_sizes,
        mailbox_date=mailbox_date,
    )


@app.route("/admin/mail-dashboard/sender-detail")
@require_admin
def mail_dashboard_sender_detail():
    """JSON endpoint — per-sender drill-down for the dashboard modal."""
    import sqlite3 as _sqlite3
    sender = request.args.get('sender', '')
    db_path = os.path.join(os.path.dirname(__file__), '..', 'email_monitoring', 'monitoring.db')
    try:
        conn = _sqlite3.connect(db_path)
        conn.row_factory = _sqlite3.Row
        cur = conn.cursor()
        daily = cur.execute(
            "SELECT date, sent_count, bounced_count, deferred_count "
            "FROM email_volume_daily WHERE user_email = ? ORDER BY date",
            (sender,)
        ).fetchall()
        fail_rows = cur.execute(
            "SELECT timestamp, to_address, error_message, status "
            "FROM email_failures WHERE from_user = ? ORDER BY timestamp DESC LIMIT 50",
            (sender,)
        ).fetchall()
        conn.close()
        return jsonify({
            "sender": sender,
            "daily": [
                {"date": r["date"], "sent": r["sent_count"],
                 "bounced": r["bounced_count"], "deferred": r["deferred_count"]}
                for r in daily
            ],
            "failures": [
                {"timestamp": r["timestamp"], "to": r["to_address"],
                 "reason": classify_error(r["error_message"]),
                 "error": r["error_message"], "status": r["status"]}
                for r in fail_rows
            ],
        })
    except Exception as e:
        logging.warning(f"mail_dashboard_sender_detail error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/admin/run-monitor", methods=["POST"])
@require_admin
def run_monitor():
    """Manually trigger email_monitor_to_db.py for today's date."""
    import subprocess, time, os
    from datetime import date as _date
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script = os.path.join(base_dir, "scripts", "email_monitor_to_db.py")
    today = _date.today().strftime("%Y-%m-%d")
    t0 = time.time()
    try:
        result = subprocess.run(
            ["/usr/bin/python3", script, "--date", today],
            cwd=base_dir,
            capture_output=True,
            text=True,
            timeout=120,
        )
        duration = round(time.time() - t0, 1)
        if result.returncode == 0:
            return jsonify({"ok": True, "date": today, "duration": duration})
        else:
            return jsonify({"ok": False, "error": result.stderr[-500:], "date": today}), 500
    except subprocess.TimeoutExpired:
        return jsonify({"ok": False, "error": "Script timed out after 120s"}), 504
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/admin/dmarc")
@require_admin
def dmarc_dashboard():
    """DMARC authentication analysis dashboard."""
    import sqlite3 as _sqlite3
    import glob as _glob
    from datetime import date as _date, timedelta as _timedelta, datetime as _datetime

    db_path = os.path.join(os.path.dirname(__file__), '..', 'email_monitoring', 'monitoring.db')
    reports_dir = os.path.join(os.path.dirname(__file__), '..', 'email_monitoring', 'reports')

    dmarc_stats = []
    dmarc_overall = None
    dmarc_date_range = None

    # --- Pipeline health defaults ---
    pipeline = {
        'latest_report_date': None,    # most recent `date` column in DB
        'latest_reporter':    None,    # which reporter sent it
        'latest_file_date':   None,    # mtime of newest .md file on disk
        'latest_file_reporter': None,  # reporter extracted from filename
        'days_stale':         None,    # today - latest_report_date
        'status':             'unknown',  # 'ok' / 'warn' / 'stale'
    }

    # --- Recommendation defaults ---
    rec = {
        'last_failure_date':      None,
        'days_since_fix':         None,
        'post_fix_total':         0,
        'post_fix_passed':        0,
        'post_fix_rate':          None,
        'quarantine_eligible_date': None,
        'days_remaining':         None,
        'status':                 'no_data',  # 'on_track' / 'ready' / 'needs_work' / 'no_data'
    }

    try:
        conn = _sqlite3.connect(db_path)
        conn.row_factory = _sqlite3.Row
        cur = conn.cursor()

        thirty_ago = (_date.today() - _timedelta(days=30)).isoformat()

        # --- 30-day reporter breakdown ---
        dmarc_rows = cur.execute(
            "SELECT reporter, SUM(total_messages) AS total, SUM(pass_count) AS passed "
            "FROM dmarc_daily WHERE date >= ? "
            "GROUP BY reporter ORDER BY total DESC",
            (thirty_ago,)
        ).fetchall()

        for r in dmarc_rows:
            total  = r['total']  or 0
            passed = r['passed'] or 0
            rate   = round(100 * passed / total, 1) if total > 0 else 0.0
            dmarc_stats.append({
                'reporter': r['reporter'],
                'total':    total,
                'passed':   passed,
                'failed':   total - passed,
                'pass_rate': rate,
            })

        if dmarc_stats:
            grand_total  = sum(d['total']  for d in dmarc_stats)
            grand_passed = sum(d['passed'] for d in dmarc_stats)
            dmarc_overall = round(100 * grand_passed / grand_total, 1) if grand_total > 0 else 0.0

        dmarc_date_row = cur.execute(
            "SELECT MIN(date) AS earliest, MAX(date) AS latest FROM dmarc_daily"
        ).fetchone()
        if dmarc_date_row and dmarc_date_row['earliest']:
            dmarc_date_range = f"{dmarc_date_row['earliest']} to {dmarc_date_row['latest']}"

        # --- Pipeline health: latest DB entry ---
        latest_row = cur.execute(
            "SELECT reporter, date FROM dmarc_daily ORDER BY date DESC LIMIT 1"
        ).fetchone()
        if latest_row:
            pipeline['latest_report_date'] = latest_row['date']
            pipeline['latest_reporter']    = latest_row['reporter']
            days_stale = (_date.today() - _date.fromisoformat(latest_row['date'])).days
            pipeline['days_stale'] = days_stale
            # DMARC reports lag 1-3 days naturally; flag if > 7 days
            if days_stale <= 4:
                pipeline['status'] = 'ok'
            elif days_stale <= 7:
                pipeline['status'] = 'warn'
            else:
                pipeline['status'] = 'stale'

        # --- Pipeline health: most recent file on disk ---
        md_files = _glob.glob(os.path.join(reports_dir, '*.md'))
        if md_files:
            newest = max(md_files, key=os.path.getmtime)
            mtime = os.path.getmtime(newest)
            pipeline['latest_file_date'] = _datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
            # extract reporter from filename: "google.com!minipass.me!..." → "google.com"
            pipeline['latest_file_reporter'] = os.path.basename(newest).split('!')[0]

        # --- Recommendation data ---
        # Find the date of the most recent failure
        last_fail_row = cur.execute(
            "SELECT MAX(date) AS d FROM dmarc_daily WHERE fail_count > 0"
        ).fetchone()
        last_failure_date = last_fail_row['d'] if last_fail_row else None

        if last_failure_date:
            rec['last_failure_date'] = last_failure_date
            last_fail_dt = _date.fromisoformat(last_failure_date)
            days_since = (_date.today() - last_fail_dt).days
            rec['days_since_fix'] = days_since

            # Post-fix metrics (everything AFTER the last failure date)
            pf_row = cur.execute(
                "SELECT SUM(total_messages) AS t, SUM(pass_count) AS p "
                "FROM dmarc_daily WHERE date > ?",
                (last_failure_date,)
            ).fetchone()
            pf_total  = pf_row['t'] or 0
            pf_passed = pf_row['p'] or 0
            rec['post_fix_total']  = pf_total
            rec['post_fix_passed'] = pf_passed
            rec['post_fix_rate']   = round(100 * pf_passed / pf_total, 1) if pf_total > 0 else None

            # Quarantine eligibility: 30 days of post-fix data at 98%+
            days_remaining = max(0, 30 - days_since)
            rec['days_remaining'] = days_remaining
            eligible_dt = last_fail_dt + _timedelta(days=30)
            rec['quarantine_eligible_date'] = eligible_dt.isoformat()

            pf_rate = rec['post_fix_rate'] or 0
            if days_remaining == 0 and pf_rate >= 98:
                rec['status'] = 'ready'
            elif pf_rate >= 98:
                rec['status'] = 'on_track'
            else:
                rec['status'] = 'needs_work'
        else:
            # No failures ever recorded — already excellent
            rec['status'] = 'ready'
            rec['days_since_fix'] = None

        conn.close()

    except Exception as e:
        logging.warning(f"dmarc_dashboard DB error: {e}")

    return render_template(
        'admin/dmarc_dashboard.html',
        dmarc_stats=dmarc_stats,
        dmarc_overall=dmarc_overall,
        dmarc_date_range=dmarc_date_range,
        pipeline=pipeline,
        rec=rec,
    )


@app.route("/internal/notify-password-reset", methods=["POST"])
def internal_notify_password_reset():
    """Called by customer containers after a self-service password reset."""
    data = request.get_json(silent=True) or {}
    if data.get("secret") != os.environ.get("INTERNAL_API_SECRET"):
        return jsonify({"error": "unauthorized"}), 401

    subdomain = data.get("subdomain", "").strip()
    new_password = data.get("new_password", "")
    if not subdomain or not new_password:
        return jsonify({"error": "missing fields"}), 400

    # Update admin_password (bcrypt hash for app login) AND email_password (plaintext,
    # used when resending onboarding email so the customer gets their current password).
    import sqlite3 as _sqlite3
    import bcrypt as _bcrypt
    hashed = _bcrypt.hashpw(new_password.encode(), _bcrypt.gensalt())
    with _sqlite3.connect("customers.db") as _conn:
        _cur = _conn.execute(
            "UPDATE customers SET admin_password = ?, email_password = ? WHERE subdomain = ?",
            (hashed, new_password, subdomain)
        )
        _conn.commit()
    if _cur.rowcount == 0:
        return jsonify({"error": "subdomain not found"}), 404

    return jsonify({"ok": True})


# ✅ Run server
if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=5000)

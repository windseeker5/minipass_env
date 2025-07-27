from flask import Flask, render_template, request, redirect, url_for, session, abort
from dotenv import load_dotenv
from datetime import datetime, timezone
import stripe
import os
import json
import secrets
from subprocess import run
from shutil import copytree

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
app.secret_key = os.getenv("SECRET_KEY", "fallback123")

# ✅ Stripe setup
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")

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




@app.route("/check-subdomain", methods=["POST"])
def check_subdomain():
    data = request.get_json()
    name = data.get("subdomain", "").strip().lower()

    from utils.customer_helpers import init_customers_db, subdomain_taken
    init_customers_db()

    if not name or not name.isalnum():
        return {"available": False, "error": "Invalid subdomain"}, 200

    if subdomain_taken(name):
        return {"available": False, "error": "Subdomain already taken"}, 200

    return {"available": True}, 200





# ✅ Handle form submit
@app.route("/start-checkout", methods=["POST"])
def start_checkout():
    plan = request.form.get("plan")
    app_name = request.form.get("app_name")
    organization_name = request.form.get("organization_name")
    admin_email = request.form.get("admin_email")
    # Use admin_email as forwarding_email automatically
    forwarding_email = admin_email
    admin_password = secrets.token_urlsafe(12)

    session["checkout_info"] = {
        "plan": plan,
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
    plan_key = info.get("plan", "basic").lower()

    plan_map = {
        "basic": {"price": 1000, "name": "MiniPass Basic"},
        "pro": {"price": 2500, "name": "MiniPass Pro"},
        "ultimate": {"price": 5000, "name": "MiniPass Ultimate"},
    }
    plan = plan_map.get(plan_key, plan_map["basic"])

    session_obj = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "cad",
                "product_data": {"name": plan["name"]},
                "unit_amount": plan["price"],
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=url_for("deployment_in_progress", _external=True),
        cancel_url=url_for("home", _external=True) + "?cancelled=true",
        metadata={
            "app_name": info.get("app_name", ""),
            "organization_name": info.get("organization_name", ""),
            "admin_email": info.get("admin_email", ""),
            "forwarding_email": info.get("forwarding_email", ""),
            "admin_password": info.get("admin_password", "")
        }
    )

    return redirect(session_obj.url, code=303)







# ✅ Deployment progress page
@app.route("/deployment-in-progress")
def deployment_in_progress():
    return render_template("deployment_progress.html")




# ✅ Webhook listener
@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    import stripe
    import os
    from utils.customer_helpers import (
        init_customers_db, subdomain_taken,
        get_next_available_port, insert_customer, update_customer_email_status
    )
    from utils.deploy_helpers import insert_admin_user, deploy_customer_container
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
        session_data = event["data"]["object"]
        metadata = session_data.get("metadata", {})

        app_name = metadata.get("app_name", "").strip().lower()
        organization_name = metadata.get("organization_name", "")
        admin_email = metadata.get("admin_email")
        forwarding_email = metadata.get("forwarding_email")
        admin_password = metadata.get("admin_password")
        plan_key = metadata.get("plan", "basic").lower()

        log_operation_start(subscription_logger, "Customer Subscription Processing",
                           app_name=app_name,
                           admin_email=admin_email,
                           plan=plan_key,
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

            # Step 2: Assign resources and create customer record
            subscription_logger.info("🔢 Step 2: Assigning resources and creating customer record")
            port = get_next_available_port()
            email_address = f"{app_name}_app@minipass.me"
            subscription_logger.info(f"   📦 Assigned port: {port}")
            subscription_logger.info(f"   📧 Generated email: {email_address}")
            
            # Insert customer with email info into database
            insert_customer(
                admin_email, app_name, app_name, plan_key, admin_password, port,
                email_address=email_address, forwarding_email=forwarding_email, 
                email_status='pending', organization_name=organization_name
            )
            log_validation_check(subscription_logger, "Customer record created", True, f"Customer {app_name} added to database")

            # Step 3: Deploy container
            subscription_logger.info("🐳 Step 3: Deploying customer container")
            success = deploy_customer_container(app_name, admin_email, admin_password, plan_key, port, organization_name)

            if success:
                log_validation_check(subscription_logger, "Container deployment", True, f"Container deployed successfully for {app_name}")
                app_url = f"https://{app_name}.minipass.me"
                subscription_logger.info(f"🌐 Application URL: {app_url}")

                # Step 4: Setup customer email
                subscription_logger.info("📧 Step 4: Setting up customer email and forwarding")
                email_success, created_email, error_msg = setup_customer_email_complete(
                    app_name, admin_password, forwarding_email
                )
                
                if email_success:
                    subscription_logger.info(f"✅ Email setup completed: {created_email} -> {forwarding_email}")
                    update_customer_email_status(app_name, created_email, 'success')
                    log_validation_check(subscription_logger, "Email setup", True, f"Email {created_email} created and forwarded to {forwarding_email}")
                else:
                    subscription_logger.warning(f"⚠️ Email setup failed for {created_email}: {error_msg}")
                    update_customer_email_status(app_name, created_email, 'failed')
                    log_validation_check(subscription_logger, "Email setup", False, f"Email setup failed: {error_msg}")
                    # Continue with deployment even if email setup fails

                # Step 5: Send deployment notification
                subscription_logger.info(f"📧 Step 5: Sending deployment notification to {admin_email}")
                
                # Include email credentials in the deployment email
                email_info = {
                    'email_address': created_email,
                    'email_password': admin_password,
                    'forwarding_setup': email_success and forwarding_email
                }
                send_user_deployment_email(admin_email, app_url, admin_password, email_info)
                log_validation_check(subscription_logger, "Deployment notification sent", True, f"Email sent to {admin_email}")

                log_operation_end(subscription_logger, "Customer Subscription Processing", success=True)

            else:
                log_validation_check(subscription_logger, "Container deployment", False, "Container deployment failed")
                raise RuntimeError("Container failed to deploy")

        except Exception as e:
            error_msg = f"Deployment error: {str(e)}"
            subscription_logger.error(f"❌ {error_msg}")
            log_operation_end(subscription_logger, "Customer Subscription Processing", success=False, error_msg=error_msg)

            error_output = getattr(e, 'output', '') or getattr(e, 'stderr', '') or str(e)
            send_support_error_email(admin_email, app_name, error_output)
            return "Deployment failed", 500

    return "OK", 200



# ✅ Run server
if __name__ == "__main__":
    app.run(debug=True, port=5000)

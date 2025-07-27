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

# ✅ Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


 
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

    logging.info("📩 Stripe webhook received")
    logging.info(f"Raw payload: {payload}")

    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError:
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError:
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

        logging.info(f"✅ Payment confirmed for: {app_name}")
        logging.info(f"🚀 Triggering container setup for {admin_email} with plan: {plan_key}")

        try:
            # 🧠 Init DB and recheck subdomain (safety)
            init_customers_db()
            if subdomain_taken(app_name):
                raise ValueError("Subdomain already taken")

            # 🔢 Assign port + create email address
            port = get_next_available_port()
            email_address = f"{app_name}_app@minipass.me"
            
            # Insert customer with email info into database
            insert_customer(
                admin_email, app_name, app_name, plan_key, admin_password, port,
                email_address=email_address, forwarding_email=forwarding_email, 
                email_status='pending', organization_name=organization_name
            )

            # 🐳 Deploy container
            success = deploy_customer_container(app_name, admin_email, admin_password, plan_key, port, organization_name)

            if success:
                app_url = f"https://{app_name}.minipass.me"

                # 📧 Setup customer email with mail server using new integration
                email_success, created_email, error_msg = setup_customer_email_complete(
                    app_name, admin_password, forwarding_email
                )
                
                if email_success:
                    logging.info(f"✅ Email setup completed: {created_email} -> {admin_email} (admin email)")
                    update_customer_email_status(app_name, created_email, 'success')
                else:
                    logging.warning(f"⚠️ Email setup failed for {created_email}: {error_msg}")
                    update_customer_email_status(app_name, created_email, 'failed')
                    # Continue with deployment even if email setup fails

                logging.info(f"📧 Sending deployment email to {admin_email} for {app_url}")
                
                # Include email credentials in the deployment email
                email_info = {
                    'email_address': created_email,
                    'email_password': admin_password,
                    'forwarding_setup': email_success and forwarding_email
                }
                send_user_deployment_email(admin_email, app_url, admin_password, email_info)
                logging.info("📨 Email sent successfully")

                logging.info(f"✅ Deployment successful for {app_name}")

            else:
                raise RuntimeError("Container failed to deploy")

        except Exception as e:
            logging.error(f"❌ Deployment error: {e}")

            error_output = getattr(e, 'output', '') or getattr(e, 'stderr', '') or str(e)
            send_support_error_email(admin_email, app_name, error_output)
            return "Deployment failed", 500

    return "OK", 200



# ✅ Run server
if __name__ == "__main__":
    app.run(debug=True, port=5000)

# 📦 Core Python Modules
import os
import io
import uuid
import json
import base64
import socket
import hashlib
import bcrypt
import stripe
import qrcode
from datetime import datetime, timezone

# 🌐 Flask Core
from flask import (
    Flask, render_template, render_template_string, request, redirect,
    url_for, session, flash, get_flashed_messages, jsonify, current_app
)


# 🛠 Flask Extensions
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import CSRFProtect



# 🧱 SQLAlchemy Extras
from sqlalchemy import extract, func, case, desc

# 📎 File Handling
from werkzeug.utils import secure_filename

# 🧠 Models
from models import db, Admin, Pass, Redemption, Setting, EbankPayment, ReminderLog, EmailLog
from models import Activity, User, Signup, Passport, AdminActionLog


# ⚙️ Config
from config import Config

# 🔁 Background Jobs
from apscheduler.schedulers.background import BackgroundScheduler

# 🧰 App Utilities
from utils import (
    send_email_async,
    get_setting,
    generate_qr_code_image,
    get_pass_history_data,
    get_all_activity_logs,
    match_gmail_payments_to_passes,
    utc_to_local,
    send_unpaid_reminders,
    get_kpi_stats,
    notify_pass_event,
    generate_pass_code
)

# 🧠 Data Tools
from collections import defaultdict

#from app.chatbot.to_delete_routes_chatbot import chat_bp
#from chatbot.routes_chatbot import chat_bp
from chatbot import chat_bp


# ✅ Pass the full datetime object
from utils import send_email, generate_qr_code_image, get_pass_history_data, get_setting
from flask import render_template, render_template_string, url_for

import requests
from flask import send_from_directory


from flask import render_template, request, redirect, url_for, session, flash
from datetime import datetime
from models import Signup, Activity, User, db


from models import Admin, Activity, Passport, User, db
from utils import get_setting, notify_pass_event

from models import Passport, User, AdminActionLog, Activity
import time




env = os.environ.get("FLASK_ENV", "prod").lower()
db_filename = "dev_database.db" if env == "dev" else "prod_database.db"

db_path = os.path.join("instance", db_filename)
print(f"📦 Using {'DEV' if env == 'dev' else 'PROD'} database → {db_path}")



app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB limit
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.jpeg', '.png', '.gif']
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads', 'activity_images')





app.config.from_object(Config)

# ✅ Initialize database
db.init_app(app)




migrate = Migrate(app, db)


#if not os.path.exists(db_path):
#    print(f"❌ {db_path} is missing!")
#    exit(1)


print(f"📂 Connected DB path: {app.config['SQLALCHEMY_DATABASE_URI']}")


UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

csrf = CSRFProtect(app)
app.config["SECRET_KEY"] = "MY_SECRET_KEY_FOR_NOW"

app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour

import hashlib

@app.template_filter("hashlib_md5")
def hashlib_md5(s):
    return hashlib.md5(s.encode()).hexdigest()





# ✅ Load settings only if the database is ready
with app.app_context():
    app.config["MAIL_SERVER"] = Config.get_setting(app, "MAIL_SERVER", "smtp.gmail.com")
    #app.config["MAIL_PORT"] = int(Config.get_setting(app, "MAIL_PORT", 587))
    app.config["MAIL_PORT"] = int(Config.get_setting(app, "MAIL_PORT", "587") or 587)
    app.config["MAIL_USE_TLS"] = Config.get_setting(app, "MAIL_USE_TLS", "True") == "True"
    app.config["MAIL_USERNAME"] = Config.get_setting(app, "MAIL_USERNAME", "")
    app.config["MAIL_PASSWORD"] = Config.get_setting(app, "MAIL_PASSWORD", "")
    app.config["MAIL_DEFAULT_SENDER"] = Config.get_setting(app, "MAIL_DEFAULT_SENDER", "")





app.register_blueprint(chat_bp)         


##
##  All the Scheduler JOB 🟢
##


#scheduler = BackgroundScheduler()
#scheduler.add_job(func=match_gmail_payments_to_passes, trigger="interval", hours=1)
#scheduler.start()


scheduler = BackgroundScheduler()
from utils import get_setting  # ✅ at the top of app.py
from sqlalchemy.exc import OperationalError


with app.app_context():
    try:
        if get_setting("ENABLE_EMAIL_PAYMENT_BOT", "False") == "True":
            print("🟢 Email Payment Bot is ENABLED. Scheduling job every 30 minutes.")
            def run_payment_bot():
                with app.app_context():
                    match_gmail_payments_to_passes()

            scheduler.add_job(run_payment_bot, trigger="interval", minutes=30, id="email_payment_bot")
            scheduler.start()
        else:
            print("⚪ Email Payment Bot is DISABLED. No job scheduled.")
    except OperationalError as e:
        print("⚠️ DB not ready yet (probably during initial setup), skipping email bot setup.")






scheduler = BackgroundScheduler()
scheduler.add_job(func=lambda: send_unpaid_reminders(app), trigger="interval", days=1)
#scheduler.add_job(func=lambda: send_unpaid_reminders(app), trigger="interval", days=0.001)

scheduler.start()





@app.context_processor
def inject_globals_and_csrf():
    from flask_wtf.csrf import generate_csrf
    return {
        'now': datetime.now(timezone.utc),
        'ORG_NAME': get_setting("ORG_NAME", "Ligue hockey Gagnon Image"),
        'csrf_token': generate_csrf  # returns the raw CSRF token
    }


@app.template_filter('encode_md5')
def encode_md5(s):
    if not s:
        return ''
    return hashlib.md5(s.strip().lower().encode('utf-8')).hexdigest()



@app.template_filter("datetimeformat")
def datetimeformat(value, format="%Y-%m-%d %H:%M"):
    return value.strftime(format) if value else ""



@app.before_request
def check_first_run():
    if request.endpoint != 'setup' and not Admin.query.first():
        return redirect(url_for('setup'))



@app.template_filter("trim_email")
def trim_email(email):
    if not email:
        return "-"
    return email.split("@")[0]





##
## - = - = - = - = - = - = - = - = - = - = - = - = - =
##
##    TESTING ROUTES
##
## - = - = - = - = - = - = - = - = - = - = - = - = - =
##

  
@app.route("/preview-email/<event>")
def preview_email(event):
    from utils import notify_pass_event
    from models import Pass
    from flask import current_app

    sample_pass = Pass.query.filter(Pass.user_email.isnot(None)).order_by(Pass.id.desc()).first()

    if not sample_pass:
        return "❌ No sample pass with email found in DB.", 404

    notify_pass_event(
        app=current_app._get_current_object(),
        event_type=event,
        hockey_pass=sample_pass,
        admin_email="preview@test",
    )

    return f"✅ Preview email sent using event type: {event}"



@app.route("/retry-failed-emails")
def retry_failed_emails():
    if "admin" not in session:
        return redirect(url_for("login"))

    from models import EmailLog, Pass
    from utils import send_email_async
    from datetime import datetime

    failed_logs = EmailLog.query.filter_by(result="FAILED").all()
    retried = 0

    # 🔁 Replace with your email for testing
    override_email = "kdresdell@gmail.com"
    #testing_mode = True
    testing_mode = False

    for log in failed_logs:
        pass_obj = Pass.query.filter_by(pass_code=log.pass_code).first()
        if not pass_obj:
            continue  # Skip if no matching pass

        try:
            context = json.loads(log.context_json)
        except:
            continue

        send_email_async(
            current_app._get_current_object(),
            user_email=override_email if testing_mode else log.to_email,
            subject=f"[TEST] {log.subject}" if testing_mode else log.subject,
            user_name=context.get("user_name", "User"),
            pass_code=log.pass_code,
            created_date=context.get("created_date", datetime.utcnow().strftime("%Y-%m-%d")),
            remaining_games=context.get("remaining_games", 0),
            special_message=context.get("special_message", None),
            admin_email=session.get("admin")
        )

        retried += 1

    flash(f"📤 Retried {retried} failed email(s) — sent to {override_email}.", "info")
    return redirect(url_for("dashboard"))



@app.route("/test-reminders")
def test_reminders():
    if "admin" not in session:
        return redirect(url_for("login"))

    from utils import send_unpaid_reminders
    send_unpaid_reminders(app)
    flash("✅ Test run of send_unpaid_reminders() executed. Check logs and emails.", "success")
    return redirect(url_for("dashboard"))



@app.route("/test-email-match")
def test_email_match():
    if "admin" not in session:
        return redirect(url_for("login"))

    from utils import match_gmail_payments_to_passes
    match_gmail_payments_to_passes()
    flash("✅ Gmail payment match test executed. Check logs and DB.", "success")
    return redirect(url_for("dashboard"))



##
## - = - = - = - = - = - = - = - = - = - = - = - = - =
##
##    EXTERNAL API TESTING ONLY
##
## - = - = - = - = - = - = - = - = - = - = - = - = - =
##



# 🔵 Unsplash Search API
@app.route("/unsplash-search")
def unsplash_search():
    query = request.args.get("q", "")
    page = int(request.args.get("page", 1))  # ✅ Get page from query string

    if not query:
        return jsonify([])

    access_key = "DpPe0DZwUlYsEjrnZf-E5njVC0VLePUmHmRAhBELgWc"  # 🔥 Replace this with your real key
    url = f"https://api.unsplash.com/search/photos?query={query}&page={page}&per_page=9&client_id={access_key}"  # ✅ Add `page`

    try:
        resp = requests.get(url)
        data = resp.json()

        results = []
        for result in data.get("results", []):
            results.append({
                "thumb": result["urls"]["small"],
                "full": result["urls"]["full"]
            })

        return jsonify(results)
    except Exception as e:
        print("❌ Unsplash API error:", e)
        return jsonify([])






# 🔵 Download and Save Selected Unsplash Image
@app.route("/download-unsplash-image")
def download_unsplash_image():
    image_url = request.args.get("url")
    if not image_url:
        return jsonify({"success": False})

    try:
        resp = requests.get(image_url)
        if resp.status_code != 200:
            return jsonify({"success": False})

        # Save the file locally
        os.makedirs("static/uploads/activity_images", exist_ok=True)
        filename = f"activity_{uuid.uuid4().hex[:10]}.jpg"
        filepath = os.path.join("static/uploads/activity_images", filename)

        with open(filepath, "wb") as f:
            f.write(resp.content)

        return jsonify({"success": True, "filename": filename})
    except Exception as e:
        print("❌ Error downloading Unsplash image:", e)
        return jsonify({"success": False})









##
## - = - = - = - = - = - = - = - = - = - = - = - = - =
##
##    Regular ROUTES
##
## - = - = - = - = - = - = - = - = - = - = - = - = - =
##



@app.route("/")
def home():
    if "admin" not in session:
        return redirect(url_for("login"))

    activities = Activity.query.all()
    return render_template("index.html", activities=activities)




@app.route("/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect(url_for("login"))

    from utils import get_kpi_stats, get_all_activity_logs
    from models import Activity, Signup, Passport, db
    from sqlalchemy.sql import func
    from datetime import datetime

    kpi_data = get_kpi_stats()
    activities = db.session.query(Activity).filter_by(status='active').all()
    activity_cards = []

    for a in activities:
        # Signups
        all_signups = Signup.query.filter_by(activity_id=a.id).all()
        pending_signups = [s for s in all_signups if s.status == 'pending']

        # Passports
        all_passports = Passport.query.filter_by(activity_id=a.id).all()
        paid_passports = [p for p in all_passports if p.paid]
        unpaid_passports = [p for p in all_passports if not p.paid]
        active_passports = [p for p in paid_passports if p.uses_remaining > 0]

        # Revenue
        paid_amount = round(sum(p.sold_amt for p in paid_passports), 2)
        unpaid_amount = round(sum(p.sold_amt for p in unpaid_passports), 2)

        # Optional: Days left
        if a.end_date:
            days_left = max((a.end_date - datetime.utcnow()).days, 0)
        else:
            days_left = "N/A"

        activity_cards.append({
            "id": a.id,
            "name": a.name,
            "sessions_included": a.sessions_included,
            "signups": len(all_signups),
            "pending_signups": len(pending_signups),
            "passports": len(all_passports),
            "active_passports": len(active_passports),
            "unpaid_passports": len(unpaid_passports),
            "paid_passports": len(paid_passports),
            "paid_amount": paid_amount,
            "unpaid_amount": unpaid_amount,
            "goal_revenue": a.goal_revenue,
            "image_filename": a.image_filename,
            "days_left": days_left
        })

    # ✅ Use working helper function
    all_logs = get_all_activity_logs()
    recent_logs = all_logs[:20]  # last 20 logs only

    return render_template(
        "dashboard.html",
        activities=activity_cards,
        kpi_data=kpi_data,
        logs=recent_logs
    )




@app.route("/admin/signup/mark-paid/<int:signup_id>", methods=["POST"])
def mark_signup_paid(signup_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    signup = db.session.get(Signup, signup_id)
    if not signup:
        flash("❌ Signup not found.", "error")
        return redirect(url_for("admin_signups"))

    signup.paid = True
    signup.paid_at = datetime.utcnow()
    db.session.commit()

    flash(f"✅ Marked {signup.user.name}'s signup as paid.", "success")
    return redirect(url_for("admin_signups"))



@app.route("/admin/signups")
def admin_signups():
    if "admin" not in session:
        return redirect(url_for("login"))

    signups = Signup.query.order_by(Signup.signed_up_at.desc()).all()
    return render_template("admin_signups.html", signups=signups)



@app.route("/admin/signup/create-pass/<int:signup_id>")
def create_pass_from_signup(signup_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    signup = db.session.get(Signup, signup_id)
    if not signup:
        flash("❌ Signup not found.", "error")
        return redirect(url_for("admin_signups"))

    from models import Passport

    # Check if a passport already exists
    existing_passport = Passport.query.filter_by(user_id=signup.user_id, activity_id=signup.activity_id).first()
    if existing_passport:
        flash("⚠️ A passport for this user and activity already exists.", "warning")
        return redirect(url_for("admin_signups"))

    # Create new passport
    new_passport = Passport(
        pass_code=f"MP{datetime.utcnow().timestamp():.0f}",
        user_id=signup.user_id,
        activity_id=signup.activity_id,
        sold_amt=signup.activity.price_per_user,
        uses_remaining=signup.activity.sessions_included,
        created_dt=datetime.utcnow(),
        paid=signup.paid,
        notes=f"Created from signup {signup.id}"
    )
    db.session.add(new_passport)
    db.session.commit()

    flash("✅ Passport created from signup!", "success")
    return redirect(url_for("admin_signups"))



@app.route("/admin/signup/edit/<int:signup_id>", methods=["GET", "POST"])
def edit_signup(signup_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    signup = db.session.get(Signup, signup_id)
    if not signup:
        flash("❌ Signup not found.", "error")
        return redirect(url_for("admin_signups"))

    if request.method == "POST":
        signup.subject = request.form.get("subject", "").strip()
        signup.description = request.form.get("description", "").strip()
        db.session.commit()
        flash("✅ Signup updated.", "success")
        return redirect(url_for("admin_signups"))

    return render_template("edit_signup.html", signup=signup)



@app.route("/signup/status/<int:signup_id>", methods=["POST"])
def update_signup_status(signup_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    signup = db.session.get(Signup, signup_id)
    if not signup:
        flash("❌ Signup not found.", "error")
        return redirect(url_for("admin_signups"))

    status = request.form.get("status")

    if status in ["rejected", "cancelled"]:
        signup.status = status
        db.session.commit()

        from utils import log_admin_action

        user_name = signup.user.name if signup.user else "-"
        activity_name = signup.activity.name if signup.activity else "-"

        log_admin_action(
            f"Signup ID {signup.id}, {user_name}, for Activity '{activity_name}' was marked as {status}"
        )

        flash(f"✅ Signup marked as {status}.", "success")
    else:
        flash("❌ Invalid status.", "error")

    return redirect(url_for("admin_signups"))




@app.route("/signup/approve-create-pass/<int:signup_id>")
def approve_and_create_pass(signup_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    signup = db.session.get(Signup, signup_id)
    if not signup:
        flash("❌ Signup not found.", "error")
        return redirect(url_for("admin_signups"))

    from models import Passport, AdminActionLog, Admin
    from utils import notify_pass_event, generate_pass_code
    from datetime import datetime, timezone
    import time

    now_utc = datetime.now(timezone.utc)

    # ✅ Step 1: Approve the signup
    signup.status = "approved"
    db.session.commit()

    # ✅ Step 2: Get current Admin info
    current_admin = Admin.query.filter_by(email=session.get("admin")).first()

    # ✅ Step 3: Create Passport
    passport = Passport(
        pass_code=generate_pass_code(),
        user_id=signup.user_id,
        activity_id=signup.activity_id,
        sold_amt=signup.activity.price_per_user,
        uses_remaining=signup.activity.sessions_included,
        created_by=current_admin.id if current_admin else None,
        created_dt=now_utc,
        paid=signup.paid,
        notes=f"Created automatically from signup {signup.id}"
    )
    db.session.add(passport)
    db.session.commit()
    db.session.expire_all()

    # ✅ Step 4: Log admin action
    db.session.add(AdminActionLog(
        admin_email=session.get("admin", "unknown"),
        action=f"Passport created from signup for {signup.user.name} (Code: {passport.pass_code}) by {session.get('admin', 'unknown')}"
    ))
    db.session.commit()

    # ✅ Step 5: Sleep to ensure clean timestamps
    time.sleep(0.5)

    # ✅ Step 6: Refresh now_utc
    now_utc = datetime.now(timezone.utc)

    # ✅ Step 7: Send confirmation email
    notify_pass_event(
        app=current_app._get_current_object(),
        event_type="pass_created",
        pass_data=passport,
        admin_email=session.get("admin"),
        timestamp=now_utc
    )

    flash("Signup approved and passport created! Email sent to user.", "success")
    return redirect(url_for("activity_dashboard", activity_id=signup.activity_id))




@app.route("/create-activity", methods=["GET", "POST"])
def create_activity():
    if "admin" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        from models import Activity, AdminActionLog, db
        import os
        import uuid

        start_date_raw = request.form.get("start_date")
        end_date_raw = request.form.get("end_date")

        start_date = datetime.strptime(start_date_raw, "%Y-%m-%d") if start_date_raw else None
        end_date = datetime.strptime(end_date_raw, "%Y-%m-%d") if end_date_raw else None

        name = request.form.get("name", "").strip()
        activity_type = request.form.get("type", "").strip()
        description = request.form.get("description", "").strip()
        sessions_included = int(request.form.get("sessions_included", 1))
        price_per_user = float(request.form.get("price_per_user", 0.0))
        goal_users = int(request.form.get("goal_users", 0))
        goal_revenue = float(request.form.get("goal_revenue", 0.0))
        cost_to_run = float(request.form.get("cost_to_run", 0.0))
        payment_instructions = request.form.get("payment_instructions", "").strip()

        status = request.form.get("status", "active")

        # 🖼️ Handle image selection
        uploaded_file = request.files.get('upload_image')
        selected_image_filename = request.form.get("selected_image_filename", "").strip()

        image_filename = None

        if uploaded_file and uploaded_file.filename != '':
            ext = os.path.splitext(uploaded_file.filename)[1].lower()
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            if ext in allowed_extensions:
                filename = f"upload_{uuid.uuid4().hex[:10]}{ext}"
                upload_folder = os.path.join("static", "uploads", "activity_images")
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                uploaded_file.save(filepath)
                image_filename = filename
        elif selected_image_filename:
            image_filename = selected_image_filename

        # Create the activity
        new_activity = Activity(
            name=name,
            type=activity_type,
            description=description,
            start_date=start_date,
            end_date=end_date,
            sessions_included=sessions_included,
            price_per_user=price_per_user,
            goal_users=goal_users,
            goal_revenue=goal_revenue,
            cost_to_run=cost_to_run,
            payment_instructions=payment_instructions,
            created_by=session.get("admin"),
            image_filename=image_filename,  # ✅ Now supports upload or unsplash
        )

        db.session.add(new_activity)
        db.session.commit()

        # Log the action
        db.session.add(AdminActionLog(
            admin_email=session.get("admin", "unknown"),
            action=f"Activity Created: {new_activity.name}"
        ))
        db.session.commit()

        flash("✅ Activity created successfully!", "success")
        return redirect(url_for("create_activity"))

    # ✅ GET request
    return render_template("activity_form.html")



@app.route("/edit-activity/<int:activity_id>", methods=["GET", "POST"])
def edit_activity(activity_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    activity = db.session.get(Activity, activity_id)

    if not activity:
        flash("❌ Activity not found.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        import os
        import uuid

        activity.name = request.form.get("name", "").strip()
        activity.type = request.form.get("type", "").strip()
        activity.description = request.form.get("description", "").strip()
        activity.sessions_included = int(request.form.get("sessions_included", 1))
        activity.price_per_user = float(request.form.get("price_per_user", 0.0))
        activity.goal_users = int(request.form.get("goal_users", 0))
        activity.goal_revenue = float(request.form.get("goal_revenue", 0.0))
        activity.cost_to_run = float(request.form.get("cost_to_run", 0.0))
        activity.payment_instructions = request.form.get("payment_instructions", "").strip()

        activity.status = request.form.get("status", "active")

        start_date_raw = request.form.get("start_date")
        end_date_raw = request.form.get("end_date")

        activity.start_date = datetime.strptime(start_date_raw, "%Y-%m-%d") if start_date_raw else None
        activity.end_date = datetime.strptime(end_date_raw, "%Y-%m-%d") if end_date_raw else None

        uploaded_file = request.files.get('upload_image')
        selected_image_filename = request.form.get("selected_image_filename", "").strip()

        if uploaded_file and uploaded_file.filename != '':
            ext = os.path.splitext(uploaded_file.filename)[1].lower()
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            if ext in allowed_extensions:
                filename = f"upload_{uuid.uuid4().hex[:10]}{ext}"
                upload_folder = os.path.join("static", "uploads", "activity_images")
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                uploaded_file.save(filepath)
                activity.image_filename = filename
        elif selected_image_filename:
            activity.image_filename = selected_image_filename

        db.session.commit()

        from models import AdminActionLog

        db.session.add(AdminActionLog(
            admin_email=session.get("admin", "unknown"),
            action=f"Activity Updated: {activity.name}"
        ))
        db.session.commit()

        flash("Activity updated successfully!", "success")
        #return redirect(url_for("edit_activity", activity_id=activity.id))
        return redirect(url_for("activity_dashboard", activity_id=activity.id))

    return render_template("activity_form.html", activity=activity)





@app.route("/signup/<int:activity_id>", methods=["GET", "POST"])
def signup(activity_id):
    activity = db.session.get(Activity, activity_id)
    if not activity:
        flash("❌ Activity not found.", "error")
        return redirect(url_for("dashboard"))

    # ✅ Corrected settings loading
    settings = {s.key: s.value for s in Setting.query.all()}

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()

        user = User(name=name, email=email, phone_number=phone)
        db.session.add(user)
        db.session.flush()

        signup = Signup(
            user_id=user.id,
            activity_id=activity.id,
            subject=f"Signup for {activity.name}",
            description=request.form.get("notes", "").strip(),
            form_data="",
        )
        db.session.add(signup)
        db.session.commit()

        from utils import notify_signup_event
        notify_signup_event(app, signup=signup, activity=activity)

        flash("✅ Signup submitted!", "success")
        return redirect(url_for("dashboard"))

    return render_template("signup_form.html", activity=activity, settings=settings)



@app.route("/setup", methods=["GET", "POST"])
def setup():

    ##
    ##  POST REQUEST 
    ##

    if request.method == "POST":
        # 🔐 Step 1: Admin accounts
        admin_emails = request.form.getlist("admin_email[]")
        admin_passwords = request.form.getlist("admin_password[]")

        for email, password in zip(admin_emails, admin_passwords):
            email = email.strip()
            password = password.strip()
            if not email:
                continue

            existing = Admin.query.filter_by(email=email).first()
            if existing:
                if password and password != "********":
                    existing.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            else:
                if password and password != "********":
                    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                    db.session.add(Admin(email=email, password_hash=hashed))

        # 🗑️ Step 2: Remove deleted admins
        deleted_emails_raw = request.form.get("deleted_admins", "")
        if deleted_emails_raw:
            for email in deleted_emails_raw.split(","):
                email = email.strip()
                if email:
                    admin_to_delete = Admin.query.filter_by(email=email).first()
                    if admin_to_delete:
                        db.session.delete(admin_to_delete)

        # 📧 Step 3: Email settings
        email_settings = {
            "MAIL_SERVER": request.form.get("mail_server", "").strip(),
            "MAIL_PORT": request.form.get("mail_port", "587").strip(),
            "MAIL_USE_TLS": "mail_use_tls" in request.form,
            "MAIL_USERNAME": request.form.get("mail_username", "").strip(),
            "MAIL_PASSWORD": request.form.get("mail_password_raw", "").strip(),
            "MAIL_DEFAULT_SENDER": request.form.get("mail_default_sender", "").strip()
        }

        for key, value in email_settings.items():
            if key == "MAIL_PASSWORD" and (not value or value == "********"):
                continue
            setting = Setting.query.filter_by(key=key).first()
            if setting:
                setting.value = str(value)
            else:
                db.session.add(Setting(key=key, value=str(value)))

        # ⚙️ Step 4: App-level settings
        extra_settings = {
            "DEFAULT_PASS_AMOUNT": request.form.get("default_pass_amount", "50").strip(),
            "DEFAULT_SESSION_QT": request.form.get("default_session_qt", "4").strip(),
            "EMAIL_INFO_TEXT": request.form.get("email_info_text", "").strip(),
            "EMAIL_FOOTER_TEXT": request.form.get("email_footer_text", "").strip(),
            "ORG_NAME": request.form.get("ORG_NAME", "").strip(),
            "CALL_BACK_DAYS": request.form.get("CALL_BACK_DAYS", "0").strip()
        }

        for key, value in extra_settings.items():
            existing = Setting.query.filter_by(key=key).first()
            if existing:
                existing.value = value
            else:
                db.session.add(Setting(key=key, value=value))

        # 🤖 Step 5: Email Payment Bot Config
        bot_settings = {
            "ENABLE_EMAIL_PAYMENT_BOT": "enable_email_payment_bot" in request.form,
            "BANK_EMAIL_FROM": request.form.get("bank_email_from", "").strip(),
            "BANK_EMAIL_SUBJECT": request.form.get("bank_email_subject", "").strip(),
            "BANK_EMAIL_NAME_CONFIDANCE": request.form.get("bank_email_name_confidance", "85").strip(),
            "GMAIL_LABEL_FOLDER_PROCESSED": request.form.get("gmail_label_folder_processed", "InteractProcessed").strip()
        }

        for key, value in bot_settings.items():
            existing = Setting.query.filter_by(key=key).first()
            if existing:
                existing.value = str(value)
            else:
                db.session.add(Setting(key=key, value=str(value)))

        # 🏷 Step 6: Activity Tags
        activity_raw = request.form.get("activities", "").strip()
        try:
            if activity_raw.startswith("["):
                tag_objects = json.loads(activity_raw)
                activity_list = [
                    tag["value"].strip() if isinstance(tag, dict) and "value" in tag else str(tag).strip()
                    for tag in tag_objects if str(tag).strip()
                ]
            else:
                activity_list = [a.strip() for a in activity_raw.split(",") if a.strip()]

            setting = Setting.query.filter_by(key="ACTIVITY_LIST").first()
            if setting:
                setting.value = json.dumps(activity_list)
            else:
                db.session.add(Setting(key="ACTIVITY_LIST", value=json.dumps(activity_list)))
        except Exception as e:
            print("❌ Failed to parse/save activity list:", e)

        # 🖼 Step 7: Logo Upload
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        logo_file = request.files.get("ORG_LOGO_FILE")

        if logo_file and logo_file.filename:
            filename = secure_filename(logo_file.filename)
            logo_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            logo_file.save(logo_path)

            setting = Setting.query.filter_by(key="LOGO_FILENAME").first()
            if setting:
                setting.value = filename
            else:
                db.session.add(Setting(key="LOGO_FILENAME", value=filename))

            flash("✅ Logo uploaded successfully!", "success")

        # ✅ Step 8: Save email notification templates (including signup)
        for event in ["pass_created", "pass_redeemed", "payment_received", "payment_late", "signup"]:
            for key in ["SUBJECT", "TITLE", "INTRO", "CONCLUSION", "THEME"]:
                full_key = f"{key}_{event}"
                value = request.form.get(full_key, "").strip()
                if value:
                    existing = Setting.query.filter_by(key=full_key).first()
                    if existing:
                        existing.value = value
                    else:
                        db.session.add(Setting(key=full_key, value=value))

        db.session.commit()
        print("[SETUP] Admins configured:", admin_emails)
        print("[SETUP] Settings saved:", list(email_settings.keys()) + list(extra_settings.keys()))

        flash("Setup completed successfully!", "success")
        return redirect(url_for("setup"))

    ##
    ##  GET request — Load existing config
    ##

    settings = {s.key: s.value for s in Setting.query.all()}
    admins = Admin.query.all()
    backup_file = request.args.get("backup_file")

    backup_dir = os.path.join("static", "backups")
    backup_files = sorted(
        [f for f in os.listdir(backup_dir) if f.endswith(".zip")],
        reverse=True
    ) if os.path.exists(backup_dir) else []

    print("📥 Received backup_file from args:", backup_file)
    print("🗂️ Available backups in static/backups/:", os.listdir("static/backups"))

    template_base = os.path.join("templates", "email_templates")
    email_templates = []

    for entry in os.listdir(template_base):
        full_path = os.path.join(template_base, entry)

        if entry.endswith(".html") and os.path.isfile(full_path):
            email_templates.append(entry)
        elif entry.endswith("_compiled") and os.path.isdir(full_path):
            index_path = os.path.join(full_path, "index.html")
            if os.path.exists(index_path):
                email_templates.append(entry.replace("_compiled", "") + ".html")

    email_templates.sort()

    return render_template(
        "setup.html",
        settings=settings,
        admins=admins,
        backup_file=backup_file,
        backup_files=backup_files,
        email_templates=email_templates
    )


@app.route("/erase-app-data", methods=["POST"])
def erase_app_data():
    if "admin" not in session:
        return redirect(url_for("login"))

    try:
        # 📛 List of tables to exclude
        protected_tables = ["Admin", "Setting"]

        # 🧨 Dynamically delete data from all tables except Admin and Setting
        from models import db
        for table in db.metadata.sorted_tables:
            if table.name not in [t.lower() for t in protected_tables]:
                db.session.execute(table.delete())

        db.session.commit()
        flash("🧨 All app data erased successfully, except Admins and Settings.", "success")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error erasing data: {e}")
        flash("An error occurred while erasing data.", "error")

    return redirect(url_for("setup"))



@app.route("/generate-backup")
def generate_backup():
    if "admin" not in session:
        return redirect(url_for("login"))

    from zipfile import ZipFile
    import tempfile
    import shutil

    try:
        # ✅ Use real DB path from config
        db_uri = app.config["SQLALCHEMY_DATABASE_URI"]
        db_path = db_uri.replace("sqlite:///", "")
        db_filename = os.path.basename(db_path)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        zip_filename = f"minipass_backup_{timestamp}.zip"
        print("📦 Generating backup:", zip_filename)

        tmp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(tmp_dir, zip_filename)

        with ZipFile(zip_path, "w") as zipf:
            zipf.write(db_path, arcname=db_filename)

        final_path = os.path.join("static", "backups", zip_filename)
        os.makedirs(os.path.dirname(final_path), exist_ok=True)

        print(f"🛠 Moving zip from {zip_path} → {final_path}")
        shutil.move(zip_path, final_path)
        print(f"✅ Backup saved to: {final_path}")

        flash(f"📦 Backup created: {zip_filename}", "success")
    except Exception as e:
        print("❌ Backup failed:", str(e))
        flash("❌ Backup failed. Check logs.", "danger")

    return redirect(url_for("setup", backup_file=zip_filename))




@app.route("/users.json")
def users_json():
    from models import User

    users = (
        db.session.query(User.name, User.email, User.phone_number)
        .distinct()
        .all()
    )

    result = [
        {"name": u[0], "email": u[1], "phone": u[2]}
        for u in users if u[0]  # ✅ Filter out empty names
    ]

    print("📦 Sending user cache JSON:", result)
    return jsonify(result)







@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        print(f"📨 Login attempt for: {email}")
        print(f"🔑 Password entered: {password}")

        with app.app_context():
            admin = Admin.query.filter_by(email=email).first()

        if not admin:
            print("❌ No admin found with that email.")
        else:
            print(f"✅ Admin found: {admin.email}")
            print(f"🔐 Stored hash (type): {type(admin.password_hash)}")
            print(f"🔐 Stored hash (value): {admin.password_hash}")

            try:
                stored_hash = admin.password_hash
                if isinstance(stored_hash, bytes):
                    stored_hash = stored_hash.decode()

                if bcrypt.checkpw(password.encode(), stored_hash.encode()):
                    print("✅ Password matched.")
                    session["admin"] = email
                    return redirect(url_for("dashboard"))
                else:
                    print("❌ Password does NOT match.")
            except Exception as e:
                print("💥 Exception during bcrypt check:", e)

        flash("Invalid login!", "error")
        return redirect(url_for("login"))

    return render_template("login.html")





@app.route("/pass/<pass_code>")
def show_pass(pass_code):
    from models import Passport

    hockey_pass = Passport.query.filter_by(pass_code=pass_code).first()

    if not hockey_pass:
        return "Pass not found", 404

    # ✅ Generate QR code
    qr_image_io = generate_qr_code_image(pass_code)
    qr_data = base64.b64encode(qr_image_io.read()).decode()

    # ✅ Pass fallback admin email for correct "Par" display
    history = get_pass_history_data(pass_code, fallback_admin_email=session.get("admin"))

    # ✅ Check if admin is logged in
    is_admin = "admin" in session

    # ✅ Load system settings
    settings_raw = {s.key: s.value for s in Setting.query.all()}

    # ✅ Render payment instructions
    email_info_rendered = render_template_string(
        settings_raw.get("EMAIL_INFO_TEXT", ""),
        hockey_pass=hockey_pass
    )

    return render_template(
        "pass.html",
        hockey_pass=hockey_pass,
        qr_data=qr_data,
        history=history,
        is_admin=is_admin,
        settings=settings_raw,
        email_info=email_info_rendered
    )




@app.route("/redeem-qr/<pass_code>", methods=["POST"])
def redeem_passport_qr(pass_code):
    from models import Passport, Redemption, AdminActionLog
    from utils import notify_pass_event
    from datetime import datetime, timezone
    import time

    if "admin" not in session:
        return redirect(url_for("login"))

    now_utc = datetime.now(timezone.utc)

    passport = Passport.query.filter_by(pass_code=pass_code).first()
    if not passport:
        flash("❌ Passport not found!", "error")
        return redirect(url_for("dashboard"))

    if passport.uses_remaining > 0:
        passport.uses_remaining -= 1
        db.session.add(passport)

        # ✅ Save Redemption
        redemption = Redemption(
            passport_id=passport.id,
            date_used=now_utc,
            redeemed_by=session.get("admin", "unknown")
        )
        db.session.add(redemption)
        db.session.commit()

        # ✅ Log Admin Action BEFORE sending email
        db.session.add(AdminActionLog(
            admin_email=session.get("admin", "unknown"),
            action=f"Passport {passport.pass_code} redeemed by QR scan."
        ))
        db.session.commit()

        # ✅ Sleep 0.5 seconds for natural separation
        time.sleep(0.5)

        # ✅ Fresh now_utc after sleep
        now_utc = datetime.now(timezone.utc)

        # ✅ Send confirmation email AFTER admin log
        notify_pass_event(
            app=current_app._get_current_object(),
            event_type="pass_redeemed",
            pass_data=passport,
            admin_email=session.get("admin"),
            timestamp=now_utc
        )

        flash(f"✅ Passport {passport.pass_code} redeemed via QR scan!", "success")
    else:
        flash("❌ No uses left on this passport!", "error")

    return redirect(url_for("activity_dashboard", activity_id=passport.activity_id))






@app.route("/edit-passport/<int:passport_id>", methods=["GET", "POST"])
def edit_passport(passport_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    from models import Passport, Activity

    passport = db.session.get(Passport, passport_id)
    if not passport:
        flash("❌ Passport not found.", "error")
        return redirect(url_for("dashboard2"))

    if request.method == "POST":
        passport.sold_amt = float(request.form.get("sold_amt", passport.sold_amt))
        passport.uses_remaining = int(request.form.get("uses_remaining", passport.uses_remaining))
        passport.paid = "paid_ind" in request.form
        passport.notes = request.form.get("notes", passport.notes).strip()

        db.session.commit()
        flash("Passport updated successfully.", "success")
        return redirect(url_for("activity_dashboard", activity_id=passport.activity_id))

    # 🟢 FIX: fetch activities and pass to template
    activity_list = Activity.query.order_by(Activity.name).all()

    return render_template(
        "passport_form.html",
        passport=passport,
        activity_list=activity_list  # 🛠️ Add this
    )




@app.route("/scan-qr")
def scan_qr():
    return render_template("scan_qr.html")




@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("login"))



 

@app.route("/activity-log")
def activity_log():
    if "admin" not in session:
        return redirect(url_for("login"))

    from utils import get_all_activity_logs
    logs = get_all_activity_logs()

    return render_template("activity_log.html", logs=logs)







@app.route("/activity-dashboard/<int:activity_id>")
def activity_dashboard(activity_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    from models import Activity, Signup, Passport
    from sqlalchemy.orm import joinedload
    from sqlalchemy import or_

    activity = Activity.query.get(activity_id)
    if not activity:
        flash("❌ Activity not found", "error")
        return redirect(url_for("dashboard2"))

    # Load all related signups with user eager-loaded
    signups = (
        Signup.query
        .options(joinedload(Signup.user))
        .filter_by(activity_id=activity_id)
        .order_by(Signup.signed_up_at.desc())
        .all()
    )

    # Load only relevant passports: unpaid OR with uses remaining
    passports = (
        Passport.query
        .options(joinedload(Passport.user), joinedload(Passport.activity))
        .filter(
            Passport.activity_id == activity_id,
            or_(
                Passport.uses_remaining > 0,
                Passport.paid == False
            )
        )
        .order_by(Passport.created_dt.desc())
        .all()
    )

    return render_template(
        "activity_dashboard.html",
        activity=activity,
        signups=signups,
        passes=passports
    )





@app.template_filter("utc_to_local")
def jinja_utc_to_local_filter(dt):
    from utils import utc_to_local
    return utc_to_local(dt)






##
## - = - = - = - = - = - = - = - = - = - = - = - = - =
##
##    ROUTES THAT USING SEND_EMAIL FUNCTION
##
## - = - = - = - = - = - = - = - = - = - = - = - = - =
##



@app.route("/create-passport", methods=["GET", "POST"])
def create_passport():
    from models import Passport, User, AdminActionLog, Activity
    import time

    if "admin" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        # ✅ Get current admin
        current_admin = Admin.query.filter_by(email=session.get("admin")).first()

        # ✅ Gather form data
        user_name = request.form.get("user_name", "").strip()
        user_email = request.form.get("user_email", "").strip()
        phone_number = request.form.get("phone_number", "").strip()
        sold_amt = float(request.form.get("sold_amt", 50))
        sessions_qt = int(request.form.get("sessionsQt") or request.form.get("uses_remaining") or 4)
        paid = "paid_ind" in request.form
        activity_id = int(request.form.get("activity_id", 0))
        notes = request.form.get("notes", "").strip()

        # ✅ Always create a new user (even if same email is reused)
        user = User(name=user_name, email=user_email, phone_number=phone_number)
        db.session.add(user)
        db.session.flush()  # Assign user.id

        # ✅ Create Passport object
        passport = Passport(
            pass_code=generate_pass_code(),
            user_id=user.id,
            activity_id=activity_id,
            sold_amt=sold_amt,
            uses_remaining=sessions_qt,
            created_by=current_admin.id if current_admin else None,
            created_dt=datetime.now(timezone.utc),  # fresh datetime
            paid=paid,
            notes=notes
        )

        db.session.add(passport)
        db.session.commit()
        db.session.expire_all()

        # ✅ Log Admin Action (passport creation)
        activity_obj = db.session.get(Activity, activity_id)
        activity_name = activity_obj.name if activity_obj else "-"
        db.session.add(AdminActionLog(
            admin_email=session.get("admin", "unknown"),
            action=f"Passport created for {user.name} for activity '{activity_name}' by {session.get('admin', 'unknown')}"
        ))
        db.session.commit()

        # 💤 Small sleep to fix timestamp ordering
        time.sleep(0.5)

        # ✅ Refresh now_utc AFTER the passport and admin log are committed
        now_utc = datetime.now(timezone.utc)

        # ✅ Send confirmation email
        notify_pass_event(
            app=current_app._get_current_object(),
            event_type="pass_created",
            pass_data=passport,
            admin_email=session.get("admin"),
            timestamp=now_utc
        )

        flash("✅ Passport created and confirmation email sent.", "success")
        return redirect(url_for("dashboard"))

    # 👉 GET METHOD
    default_amt = get_setting("DEFAULT_PASS_AMOUNT", "50")
    default_qt = get_setting("DEFAULT_SESSION_QT", "4")
    activity_list = Activity.query.order_by(Activity.name).all()

    return render_template(
        "passport_form.html",
        passport=None,
        default_amt=default_amt,
        default_qt=default_qt,
        activity_list=activity_list
    )




# Store recent redemptions to prevent duplicate scans
recent_redemptions = {}

@app.route("/redeem/<pass_code>", methods=["POST"])
def redeem_passport(pass_code):
    from models import Passport, Redemption, AdminActionLog
    from utils import notify_pass_event
    from datetime import datetime, timezone
    import time

    if "admin" not in session:
        return redirect(url_for("login"))

    now_utc = datetime.now(timezone.utc)

    passport = Passport.query.filter_by(pass_code=pass_code).first()
    if not passport:
        flash("❌ Passport not found!", "error")
        return redirect(url_for("dashboard"))

    if passport.uses_remaining > 0:
        passport.uses_remaining -= 1
        db.session.add(passport)

        # ✅ Save Redemption for history tracking!
        redemption = Redemption(
            passport_id=passport.id,
            date_used=now_utc,
            redeemed_by=session.get("admin", "unknown")
        )
        db.session.add(redemption)

        db.session.commit()

        # ✅ Admin Action for activity_log
        db.session.add(AdminActionLog(
            admin_email=session.get("admin", "unknown"),
            action=f"Passport for {passport.user.name if passport.user else 'Unknown'} ({passport.pass_code}) was redeemed by {session.get('admin', 'unknown')}"
        ))
        db.session.commit()

        # ✅ Sleep to fix timestamp natural order
        time.sleep(0.5)

        # ✅ Fresh now_utc for email timestamp
        now_utc = datetime.now(timezone.utc)

        # ✅ Send confirmation email
        notify_pass_event(
            app=current_app._get_current_object(),
            event_type="pass_redeemed",
            pass_data=passport,
            admin_email=session.get("admin"),
            timestamp=now_utc
        )

        flash(f"Session redeemed! {passport.uses_remaining} uses left.", "success")
    else:
        flash("❌ No uses left on this passport!", "error")

    return redirect(url_for("activity_dashboard", activity_id=passport.activity_id))









@app.route("/mark-passport-paid/<int:passport_id>", methods=["POST"])
def mark_passport_paid(passport_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    from models import Passport, AdminActionLog
    import time
    from datetime import datetime, timezone

    passport = db.session.get(Passport, passport_id)
    if not passport:
        flash("❌ Passport not found!", "error")
        return redirect(url_for("dashboard2"))

    now_utc = datetime.now(timezone.utc)

    # ✅ Step 1: Mark Passport as Paid
    passport.paid = True
    passport.paid_date = now_utc
    passport.marked_paid_by = session.get("admin", "unknown")
    db.session.commit()

    # ✅ Step 2: Log Admin Action
    db.session.add(AdminActionLog(
        admin_email=session.get("admin", "unknown"),
        action=f"Passport for {passport.user.name if passport.user else 'Unknown'} ({passport.pass_code}) marked as PAID by {session.get('admin', 'unknown')}"
    ))
    db.session.commit()

    # ✅ Step 3: Sleep to separate timestamps naturally
    time.sleep(0.5)

    # ✅ Step 4: Refresh now_utc AFTER sleep
    now_utc = datetime.now(timezone.utc)

    # ✅ Step 5: Send confirmation email
    notify_pass_event(
        app=current_app._get_current_object(),
        event_type="payment_received",
        pass_data=passport,
        admin_email=session.get("admin"),
        timestamp=now_utc
    )

    flash(f" Passport {passport.pass_code} marked as paid. Email sent.", "success")
    return redirect(url_for("activity_dashboard", activity_id=passport.activity_id))







if __name__ == "__main__":
    env = os.environ.get("FLASK_ENV", "dev").lower()
    port = 8889 if env == "prod" else 8890
    print(f"🚀 Running on port {port} (env={env})")
    app.run(debug=(env != "prod"), port=port)

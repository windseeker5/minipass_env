# models.py (UPDATED - TIMEZONE AWARE)
import uuid
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone   
 


# ✅ Define db here (not in app.py)
db = SQLAlchemy()


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)


class AdminActionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    admin_email = db.Column(db.String(150))
    action = db.Column(db.Text)



# This should be deleted ....
class Pass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pass_code = db.Column(db.String(16), unique=True, nullable=False)
    user_name = db.Column(db.String(100), nullable=False)
    user_email = db.Column(db.String(100), nullable=False)
    sold_amt = db.Column(db.Float, default=50)
    games_remaining = db.Column(db.Integer, default=4)
    phone_number = db.Column(db.String(20), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("admin.id"))
    # pass_created_dt = db.Column(db.DateTime, default=datetime.now(timezone.utc))  # ✅ UTC-aware

    pass_created_dt = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)  # ✅ FIXED!
    )

    paid_ind = db.Column(db.Boolean, default=False)
    paid_date = db.Column(db.DateTime, nullable=True)  # ✅ manually set with UTC
    activity = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # in models.py (Pass model)
    marked_paid_by = db.Column(db.String(120), nullable=True)

 



# ✅ Generalized SaaS models (non-conflicting with current Pass logic)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    # email = db.Column(db.String(100), unique=True)

    phone_number = db.Column(db.String(20))

    signups = db.relationship("Signup", backref="user", lazy=True)
    passports = db.relationship("Passport", backref="user", lazy=True)




class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    type = db.Column(db.String(50))  # e.g., "hockey", "yoga"
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    image_filename = db.Column(db.String(255), nullable=True)  # 🆕 NEW FIELD
    sessions_included = db.Column(db.Integer, default=1)
    price_per_user = db.Column(db.Float, default=0.0)
    goal_users = db.Column(db.Integer, default=0)
    goal_revenue = db.Column(db.Float, default=0.0)
    cost_to_run = db.Column(db.Float, default=0.0)
    created_by = db.Column(db.Integer, db.ForeignKey("admin.id"))
    created_dt = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(50), default="active")
    payment_instructions = db.Column(db.Text)
    signups = db.relationship("Signup", backref="activity", lazy=True)
    passports = db.relationship("Passport", backref="activity", lazy=True)



class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey("activity.id"), nullable=False)
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.String(100))  # admin email or name
    receipt_filename = db.Column(db.String(255), nullable=True)

    activity = db.relationship("Activity", backref="expenses")






class Signup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey("activity.id"), nullable=False)
    subject = db.Column(db.String(200))
    description = db.Column(db.Text)
    form_url = db.Column(db.String(500))
    form_data = db.Column(db.Text)  # JSON string
    signed_up_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    paid = db.Column(db.Boolean, default=False)
    paid_at = db.Column(db.DateTime)
    passport_id = db.Column(db.Integer, db.ForeignKey("passport.id"))
    status = db.Column(db.String(50), default="pending")


class Passport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pass_code = db.Column(db.String(16), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey("activity.id"), nullable=False)
    sold_amt = db.Column(db.Float, default=0.0)
    uses_remaining = db.Column(db.Integer, default=0)
    created_by = db.Column(db.Integer, db.ForeignKey("admin.id"))
    created_dt = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    paid = db.Column(db.Boolean, default=False)
    paid_date = db.Column(db.DateTime)
    marked_paid_by = db.Column(db.String(120))
    notes = db.Column(db.Text)

    signups = db.relationship("Signup", backref="passport", lazy=True)



class Redemption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    passport_id = db.Column(db.Integer, db.ForeignKey("passport.id"), nullable=False)  # 🟢 FIXED
    date_used = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    redeemed_by = db.Column(db.String(100), nullable=True)



class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)


class EbankPayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))  # ✅ UTC-aware
    from_email = db.Column(db.String(150))
    subject = db.Column(db.Text)
    bank_info_name = db.Column(db.String(100))
    bank_info_amt = db.Column(db.Float)
    matched_pass_id = db.Column(db.Integer, db.ForeignKey("pass.id"), nullable=True)
    matched_name = db.Column(db.String(100))
    matched_amt = db.Column(db.Float)
    name_score = db.Column(db.Integer)
    result = db.Column(db.String(50))
    mark_as_paid = db.Column(db.Boolean, default=False)
    note = db.Column(db.Text, nullable=True)



class ReminderLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pass_id = db.Column(db.Integer, db.ForeignKey("pass.id"), nullable=False)
    reminder_sent_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class EmailLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    to_email = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    pass_code = db.Column(db.String(16), nullable=True)
    template_name = db.Column(db.String(100), nullable=True)
    context_json = db.Column(db.Text)
    result = db.Column(db.String(50))  # SENT or FAILED
    error_message = db.Column(db.Text, nullable=True)


# ✅ Place index right after the model class
db.Index('ix_signup_status', Signup.status)
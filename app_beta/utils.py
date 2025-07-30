import smtplib
import qrcode
import base64
import io
import socket
import traceback

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# from models import Setting, db, Pass, Redemption, Admin, EbankPayment, ReminderLog
from models import Setting, db, Passport, Redemption, Admin, EbankPayment, ReminderLog




import threading
import logging
from datetime import datetime
 
from flask import render_template, render_template_string, url_for, current_app, session


from pprint import pprint
from email.utils import parsedate_to_datetime
import imaplib
import email
import re

from rapidfuzz import fuzz
import imaplib


from datetime import datetime, timedelta, timezone  # ✅ Keep this for datetime.timezone
from pytz import timezone as pytz_timezone, utc      # ✅ This is for "America/Toronto"

import json
import os


from flask import render_template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib
import traceback
from premailer import transform
import os
import re
from flask import current_app
from models import Setting
import uuid



def utc_to_local(dt_utc):
    if not dt_utc:
        return None
    if dt_utc.tzinfo is None:
        dt_utc = utc.localize(dt_utc)

    eastern = pytz_timezone("America/Toronto")
    return dt_utc.astimezone(eastern)



def get_setting(key, default=""):
    with current_app.app_context():
        setting = Setting.query.filter_by(key=key).first()
        if setting and setting.value not in [None, ""]:
            return setting.value
    return default



def save_setting(key, value):
    with current_app.app_context():
        setting = Setting.query.filter_by(key=key).first()
        if setting:
            setting.value = value
        else:
            setting = Setting(key=key, value=value)
            db.session.add(setting)
        db.session.commit()



def generate_pass_code():
    """
    Securely generates a random Pass Code for passports.
    Example Output: MP-8ab94c7efb29
    """
    return f"MP-{str(uuid.uuid4()).replace('-', '')[:12]}"



def generate_qr_code(pass_code):
    qr = qrcode.make(pass_code)
    img_bytes = io.BytesIO()
    qr.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return base64.b64encode(img_bytes.read()).decode()



def generate_qr_code_image(pass_code):
    qr = qrcode.make(pass_code)
    img_bytes = io.BytesIO()
    qr.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return img_bytes



def get_pass_history_data(pass_code: str, fallback_admin_email=None) -> dict:
    """
    Builds the history log for a digital pass, converting UTC timestamps to local time (America/Toronto).
    Returns a dictionary including: created, paid, redemptions, expired, and who performed each action.

    Accepts fallback_admin_email for use in background tasks (outside of request context).
    """
    with current_app.app_context():
        from models import Admin, EbankPayment, Redemption, Pass, Passport
        DATETIME_FORMAT = "%Y-%m-%d %H:%M"

        # 🔍 Try both models
        hockey_pass = Pass.query.filter_by(pass_code=pass_code).first()
        passport_mode = False
        if not hockey_pass:
            hockey_pass = Passport.query.filter_by(pass_code=pass_code).first()
            passport_mode = True

        if not hockey_pass:
            return {"error": "Pass not found."}

        # 🔁 Fetch redemptions if using Pass
        redemptions = []
        if not passport_mode:
            redemptions = (
                Redemption.query
                .filter_by(pass_id=hockey_pass.id)
                .order_by(Redemption.date_used.asc())
                .all()
            )
        else:
            redemptions = (
                Redemption.query
                .filter_by(passport_id=hockey_pass.id)
                .order_by(Redemption.date_used.asc())
                .all()
            )



        # 📦 Initialize history structure
        history = {
            "created": None,
            "created_by": None,
            "paid": None,
            "paid_by": None,
            "redemptions": [],
            "expired": None
        }

        # 📅 Created
        created_dt = getattr(hockey_pass, "pass_created_dt", None) or getattr(hockey_pass, "created_dt", None)
        if created_dt:
            history["created"] = utc_to_local(created_dt).strftime(DATETIME_FORMAT)

        # 👤 Created by
        created_by = getattr(hockey_pass, "created_by", None)
        if created_by:
            admin = Admin.query.get(created_by)
            history["created_by"] = admin.email if admin else "-"


        # 💵 Payment info
        paid = getattr(hockey_pass, "paid_ind", None) if not passport_mode else getattr(hockey_pass, "paid", False)
        paid_date = getattr(hockey_pass, "paid_date", None)  # ✅ Always get paid_date

        if paid and paid_date:
            paid_dt = utc_to_local(paid_date)
            history["paid"] = paid_dt.strftime(DATETIME_FORMAT)

            if not passport_mode:
                ebank = (
                    EbankPayment.query
                    .filter_by(matched_pass_id=hockey_pass.id, mark_as_paid=True)
                    .order_by(EbankPayment.timestamp.desc())
                    .first()
                )

                if ebank:
                    history["paid_by"] = ebank.from_email
                else:
                    email = fallback_admin_email or "admin panel"
                    history["paid_by"] = email.split("@")[0] if "@" in email else email
            else:
                history["paid_by"] = fallback_admin_email or "admin"





        # 🎮 Redemptions
        for r in redemptions:
            local_used = utc_to_local(r.date_used)
            history["redemptions"].append({
                "date": local_used.strftime(DATETIME_FORMAT),
                "by": r.redeemed_by or "-"
            })

        # ❌ Expired if no games remaining
        games_remaining = getattr(hockey_pass, "games_remaining", None) or getattr(hockey_pass, "uses_remaining", None)
        if games_remaining == 0 and redemptions:
            history["expired"] = utc_to_local(redemptions[-1].date_used).strftime(DATETIME_FORMAT)

        return history



def extract_interac_transfers(gmail_user, gmail_password, mail=None):
    results = []

    try:
        # ✅ Always load these settings — even when mail is reused
        subject_keyword = get_setting("BANK_EMAIL_SUBJECT", "Virement Interac :")
        from_expected = get_setting("BANK_EMAIL_FROM", "notify@payments.interac.ca")

        if not mail:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(gmail_user, gmail_password)
            mail.select("inbox")

        status, data = mail.search(None, f'SUBJECT "{subject_keyword}"')
        if status != "OK":
            print(f"📭 No matching emails found for subject: {subject_keyword}")
            return results

        for num in data[0].split():
            # 📥 Fetch email content & UID
            status, msg_data = mail.fetch(num, "(BODY.PEEK[] UID)")
            if status != "OK":
                continue

            raw_email = msg_data[0][1]
            uid_line = msg_data[0][0].decode()
            uid_match = re.search(r"UID (\d+)", uid_line)
            uid = uid_match.group(1) if uid_match else None

            # 📦 Parse email headers
            msg = email.message_from_bytes(raw_email)
            from_email = email.utils.parseaddr(msg.get("From"))[1]
            subject_raw = msg["Subject"]
            subject = email.header.decode_header(subject_raw)[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode()

            # 🛡️ Validate subject and sender
            if not subject.lower().startswith(subject_keyword.lower()):
                continue
            if from_email.lower() != from_expected.lower():
                print(f"⚠️ Ignored email from unexpected sender: {from_email}")
                continue

            # 💰 Extract name & amount — support multiple Interac subject formats
            amount_match = re.search(r"reçu\s([\d,]+)\s*\$\s*de", subject)
            name_match = re.search(r"de\s(.+?)\set ce montant", subject)

            # 🔁 Fallback: e.g. "Remi Methot vous a envoyé 15,00 $"
            if not amount_match:
                amount_match = re.search(r"envoyé\s([\d,]+)\s*\$", subject)
            if not name_match:
                name_match = re.search(r":\s*(.*?)\svous a envoyé", subject)

            # 🛡️ Skip if we still can't match
            if not (amount_match and name_match):
                print(f"❌ Skipped unmatched subject: {subject}")
                continue

            # 💵 Final parsing
            amt_str = amount_match.group(1).replace(",", ".")
            name = name_match.group(1).strip()

            try:
                amount = float(amt_str)
            except ValueError:
                print(f"❌ Invalid amount format: {amt_str}")
                continue

            # ✅ Only append if parsing succeeded
            results.append({
                "bank_info_name": name,
                "bank_info_amt": amount,
                "subject": subject,
                "from_email": from_email,
                "uid": uid
            })

    except Exception as e:
        print(f"❌ Error reading Gmail: {e}")

    return results






def get_kpi_stats():
    from datetime import datetime, timedelta, timezone
    from models import Passport, Signup
    from flask import current_app

    with current_app.app_context():
        now = datetime.now(timezone.utc)

        def build_daily_series(model, date_attr, filter_fn=None, days=7):
            trend = []
            for i in reversed(range(days)):
                start = now - timedelta(days=i+1)
                end = now - timedelta(days=i)
                query = model.query.filter(getattr(model, date_attr) >= start, getattr(model, date_attr) < end)
                if filter_fn:
                    query = query.filter(filter_fn)
                trend.append(query.count())
            return trend

        ranges = {
            "7d": (now - timedelta(days=7), now, 7),
            "30d": (now - timedelta(days=30), now, 30),
            "90d": (now - timedelta(days=90), now, 30),
            "all": (datetime.min.replace(tzinfo=timezone.utc), now, 30),
        }
        previous_ranges = {
            "7d": (now - timedelta(days=14), now - timedelta(days=7)),
            "30d": (now - timedelta(days=60), now - timedelta(days=30)),
            "90d": (now - timedelta(days=180), now - timedelta(days=90)),
            "all": (datetime.min.replace(tzinfo=timezone.utc), now),
        }

        kpis = {}

        for label, (start, end, trend_days) in ranges.items():
            prev_start, prev_end = previous_ranges[label]

            current_passports = Passport.query.filter(Passport.created_dt >= start, Passport.created_dt <= end).all()
            previous_passports = Passport.query.filter(Passport.created_dt >= prev_start, Passport.created_dt <= prev_end).all()

            def total(passports): return sum(p.sold_amt for p in passports if p.paid)
            def created(passports): return len(passports)
            def active(passports): return len([p for p in passports if p.uses_remaining > 0])
            def pending_signups_count(): return Signup.query.filter(Signup.status == "pending", Signup.signed_up_at >= start, Signup.signed_up_at <= end).count()

            kpis[label] = {
                "revenue": round(total(current_passports), 2),
                "revenue_prev": round(total(previous_passports), 2),
                "pass_created": created(current_passports),
                "pass_created_prev": created(previous_passports),
                "active_users": active(current_passports),
                "active_users_prev": active(previous_passports),
                "pending_signups": pending_signups_count(),
                # Real trend arrays
                "revenue_trend": build_daily_series(Passport, "created_dt", lambda: Passport.paid == True, trend_days),
                "active_users_trend": build_daily_series(Passport, "created_dt", lambda: Passport.uses_remaining > 0, trend_days),
                "pass_created_trend": build_daily_series(Passport, "created_dt", None, trend_days),
                "pending_signups_trend": build_daily_series(Signup, "signed_up_at", lambda: Signup.status == "pending", trend_days)
            }

        return kpis





def send_unpaid_reminders(app):
    from utils import get_setting, notify_pass_event
    from models import ReminderLog, Passport, db
    from datetime import datetime, timedelta, timezone

    def ensure_utc_aware(dt):
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    with app.app_context():
        try:
            days = float(get_setting("CALL_BACK_DAYS", "15"))
        except ValueError:
            print("❌ Invalid CALL_BACK_DAYS value. Defaulting to 15.")
            days = 15

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        unpaid_passports = Passport.query.filter(
            Passport.paid == False,
            Passport.created_dt <= cutoff_date
        ).all()

        for p in unpaid_passports:
            recent_reminder = ReminderLog.query.filter_by(pass_id=p.id)\
                .order_by(ReminderLog.reminder_sent_at.desc())\
                .first()

            if recent_reminder and ensure_utc_aware(recent_reminder.reminder_sent_at) > datetime.now(timezone.utc) - timedelta(days=days):
                print(f"⏳ Skipping reminder: {p.user.name if p.user else '-'} (already reminded)")
                continue

            # ✅ Log the reminder FIRST
            db.session.add(ReminderLog(
                pass_id=p.id,
                reminder_sent_at=datetime.now(timezone.utc)
            ))
            db.session.commit()
            print(f"✅ Logged late reminder for: {p.user.name if p.user else '-'}")

            # ✅ THEN send reminder email
            print(f"📬 Sending reminder to: {p.user.email if p.user else 'N/A'}")
            notify_pass_event(
                app=app,
                event_type="payment_late",
                pass_data=p,  # using new models
                admin_email="auto-reminder@system",
                timestamp=datetime.now(timezone.utc)
            )





def match_gmail_payments_to_passes():
    from utils import extract_interac_transfers, get_setting, notify_pass_event
    from models import EbankPayment, Passport, db
    from datetime import datetime, timezone
    from flask import current_app
    from rapidfuzz import fuzz
    import imaplib

    with current_app.app_context():
        user = get_setting("MAIL_USERNAME")
        pwd = get_setting("MAIL_PASSWORD")

        if not user or not pwd:
            print("❌ MAIL_USERNAME or MAIL_PASSWORD is not set.")
            return

        threshold = int(get_setting("BANK_EMAIL_NAME_CONFIDANCE", "85"))
        gmail_label = get_setting("GMAIL_LABEL_FOLDER_PROCESSED", "InteractProcessed")

        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(user, pwd)
        mail.select("inbox")

        matches = extract_interac_transfers(user, pwd, mail)

        for match in matches:
            name = match["bank_info_name"]
            amt = match["bank_info_amt"]
            from_email = match.get("from_email")
            uid = match.get("uid")
            subject = match["subject"]

            best_score = 0
            best_passport = None
            unpaid_passports = Passport.query.filter_by(paid=False).all()

            for p in unpaid_passports:
                if not p.user:
                    continue  # Safety check
                score = fuzz.partial_ratio(name.lower(), p.user.name.lower())
                if score >= threshold and abs(p.sold_amt - amt) < 1:
                    if score > best_score:
                        best_score = score
                        best_passport = p

            if best_passport:
                now_utc = datetime.now(timezone.utc)
                best_passport.paid = True
                best_passport.paid_date = now_utc
                db.session.add(best_passport)

                db.session.add(EbankPayment(
                    from_email=from_email,
                    subject=subject,
                    bank_info_name=name,
                    bank_info_amt=amt,
                    matched_pass_id=best_passport.id,
                    matched_name=best_passport.user.name,
                    matched_amt=best_passport.sold_amt,
                    name_score=best_score,
                    result="MATCHED",
                    mark_as_paid=True,
                    note="Matched by Gmail Bot."
                ))

                db.session.commit()

                notify_pass_event(
                    app=current_app._get_current_object(),
                    event_type="payment_received",
                    pass_data=best_passport,  # ✅ update keyword
                    admin_email="gmail-bot@system",
                    timestamp=now_utc
                )

                if uid:
                    mail.uid("COPY", uid, gmail_label)
                    mail.uid("STORE", uid, "+FLAGS", "(\\Deleted)")
            else:
                db.session.add(EbankPayment(
                    from_email=from_email,
                    subject=subject,
                    bank_info_name=name,
                    bank_info_amt=amt,
                    name_score=0,
                    result="NO_MATCH",
                    mark_as_paid=False,
                    note="No matching passport found."
                ))

        db.session.commit()
        mail.expunge()
        mail.logout()




def strip_html_tags(html):
    return re.sub('<[^<]+?>', '', html)



# ✅ Log admin action centrally
def log_admin_action(action: str):
    from models import AdminActionLog, db
    from flask import session

    db.session.add(AdminActionLog(
        admin_email=session.get("admin", "unknown"),
        action=action
    ))
    db.session.commit()




def get_all_activity_logs():
    from models import Passport, Redemption, EmailLog, EbankPayment, ReminderLog, AdminActionLog, Signup
    from utils import utc_to_local
    from flask import current_app

    logs = []

    with current_app.app_context():
        # 🟢 Admin Actions (Passport Created, Activity Created, etc.)
        for a in AdminActionLog.query.all():
            action_text = a.action.lower()

            if "passport created" in action_text:
                log_type = "Passport Created"
            elif "passport" in action_text and "redeemed" in action_text:
                log_type = "Passport Redeemed"
            elif "marked" in action_text and "paid" in action_text:
                log_type = "Marked Paid"
            elif "approved" in action_text and "signup" in action_text:
                log_type = "Signup Approved"
            elif "rejected" in action_text and "signup" in action_text:
                log_type = "Signup Rejected"
            elif "cancelled" in action_text and "signup" in action_text:
                log_type = "Signup Cancelled"  # ✅ NEW detection for cancelled
            elif "activity created" in action_text:
                log_type = "Activity Created"
            else:
                log_type = "Admin Action"

            # ✅ Add "by admin" only if not already in the text
            if "by" not in a.action.lower():
                details = f"{a.action} by {a.admin_email or '-'}"
            else:
                details = a.action

            logs.append({
                "timestamp": a.timestamp,
                "type": log_type,
                "user": a.admin_email or "-",
                "details": details
            })

        # 🟠 Email Sent
        for e in EmailLog.query.all():
            pass_code_display = e.pass_code if e.pass_code else "App-Sent"
            logs.append({
                "timestamp": e.timestamp,
                "type": "Email Sent",
                "user": e.to_email,
                "details": f"To {e.to_email} — \"{e.subject}\" (Code: {pass_code_display})"
            })

        # 🔵 Payments
        for p in EbankPayment.query.all():
            if p.result == "MATCHED":
                log_type = "Interact Payment"
                details = f"From {p.matched_name}, Amount: {p.bank_info_amt:.2f}, Passport ID: {p.matched_pass_id}"
            else:
                log_type = "Payment No Match"
                details = f"From {p.bank_info_name}, Amount: {p.bank_info_amt:.2f}"

            logs.append({
                "timestamp": p.timestamp,
                "type": log_type,
                "user": p.from_email or "-",
                "details": details
            })


        # 🟣 Reminders
        for r in ReminderLog.query.all():
            from models import Passport
            passport = db.session.get(Passport, r.pass_id)

            user_name = passport.user.name if passport and passport.user else "-"
            activity_name = passport.activity.name if passport and passport.activity else "-"

            logs.append({
                "timestamp": r.reminder_sent_at,
                "type": "Late Reminder Detected",
                "user": "auto-reminder@system",
                "details": f"Late payment detected for {user_name} for Activity '{activity_name}' by App Bot"
            })



        # 🧡 User Signups
        for s in Signup.query.all():
            user_name = s.user.name if s.user else "-"
            activity_name = s.activity.name if s.activity else "-"
            logs.append({
                "timestamp": s.signed_up_at,
                "type": "Signup Submitted",
                "user": user_name,
                "details": f"User {user_name} signed up for Activity '{activity_name}' from online form"
            })

    # 📈 Sort newest first
    logs.sort(key=lambda x: x["timestamp"], reverse=True)
    return logs






##
## EMAIL STUFF
##

def safe_template(template_name: str) -> str:
    """
    Corrects template path.
    - If a compiled version exists, redirect to compiled/index.html.
    - Otherwise normal path.
    """

    template_name = template_name.lstrip("/")
    base_name = template_name.replace(".html", "")

    # Check if compiled version exists
    compiled_folder = os.path.join("app", "templates", "email_templates", f"{base_name}_compiled", "index.html")
    if os.path.exists(compiled_folder):
        return f"email_templates/{base_name}_compiled/index.html"

    # Otherwise fallback normal
    if not template_name.startswith("email_templates/"):
        return f"email_templates/{template_name}"
    return template_name


def render_and_send_email(
    app,
    *,
    user,
    subject_key,
    title_key,
    intro_key,
    conclusion_key,
    theme_key,
    context_extra=None,
    to_email=None,
    timestamp=None
):
    from utils import get_setting, send_email_async
    from flask import url_for, render_template_string
    from datetime import datetime, timezone
    import os
    import json
    import base64

    timestamp = timestamp or datetime.now(timezone.utc)

    subject = get_setting(subject_key)
    title = get_setting(title_key)
    intro = get_setting(intro_key)
    conclusion = get_setting(conclusion_key)

    template_name = get_setting(theme_key) or "confirmation.html"

    context = {
        "user_name": user.name,
        "user_email": user.email,
        "title": title,
        "intro_text": intro,
        "conclusion_text": conclusion,
    }

    if context_extra:
        context.update(context_extra)

    inline_images = {}
    final_html = None

    # 🧠 Detect compiled email (ex: signup)
    if template_name.endswith(".html"):
        compiled_folder = template_name.replace(".html", "_compiled")
        compiled_index_path = os.path.join("app", "templates", "email_templates", compiled_folder, "index.html")
        inline_images_json_path = os.path.join("app", "templates", "email_templates", compiled_folder, "inline_images.json")

        if os.path.exists(compiled_index_path):
            # ✅ Read and render compiled index.html
            with open(compiled_index_path, "r", encoding="utf-8") as f:
                raw_html = f.read()

            final_html = render_template_string(raw_html, **context)

            # ✅ Load compiled inline images if any
            if os.path.exists(inline_images_json_path):
                with open(inline_images_json_path, "r", encoding="utf-8") as f:
                    cid_map = json.load(f)
                for cid, img_base64 in cid_map.items():
                    inline_images[cid] = base64.b64decode(img_base64)

    # 🧠 Fallback for non-compiled (classic templates)
    if not final_html:
        logo_path = os.path.join("static", "uploads", "logo.png")
        if os.path.exists(logo_path):
            inline_images["logo_image"] = open(logo_path, "rb").read()
            context["logo_url"] = url_for("static", filename="uploads/logo.png")

    # 🛡️ Finally SEND

    if final_html:
        send_email_async(
            app=app,
            subject=subject,
            to_email=to_email or user.email,
            html_body=final_html,
            inline_images=inline_images if inline_images else None,
            timestamp_override=timestamp
        )
    else:
        send_email_async(
            app=app,
            subject=subject,
            to_email=to_email or user.email,
            template_name=template_name,
            context=context,
            inline_images=inline_images if inline_images else None,
            timestamp_override=timestamp
        )


def send_email(subject, to_email, template_name=None, context=None, inline_images=None, html_body=None, timestamp_override=None):
    from flask import render_template
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.image import MIMEImage
    from email.utils import formataddr
    from premailer import transform
    import logging
    from utils import get_setting, safe_template
    from datetime import datetime

    context = context or {}
    inline_images = inline_images or {}

    # 🛡️ FINAL FIX: Render properly depending on whether html_body is given
    if html_body:
        final_html = html_body
    else:
        if template_name and context:
            final_html = render_template(safe_template(template_name), **context)
        else:
            final_html = "No content."

    # 🧠 Inline CSS
    final_html = transform(final_html)

    # Build email
    msg = MIMEMultipart("related")
    msg["Subject"] = subject
    msg["To"] = to_email

    from_email = get_setting("MAIL_DEFAULT_SENDER") or "noreply@minipass.me"
    msg["From"] = formataddr(("Minipass", from_email))

    alt_part = MIMEMultipart("alternative")
    alt_part.attach(MIMEText("Votre passe numérique est prête.", "plain"))
    alt_part.attach(MIMEText(final_html, "html"))
    msg.attach(alt_part)

    for cid, img_data in inline_images.items():
        if img_data:
            try:
                part = MIMEImage(img_data)
                part.add_header("Content-ID", f"<{cid}>")
                part.add_header("Content-Disposition", "inline", filename=f"{cid}.png")
                msg.attach(part)
            except Exception as e:
                logging.error(f"❌ Image embed error for {cid}: {e}")

    try:
        smtp_host = get_setting("MAIL_SERVER")
        smtp_port = int(get_setting("MAIL_PORT", 587))
        smtp_user = get_setting("MAIL_USERNAME")
        smtp_pass = get_setting("MAIL_PASSWORD")
        use_tls = str(get_setting("MAIL_USE_TLS") or "true").lower() == "true"

        server = smtplib.SMTP(smtp_host, smtp_port)
        server.ehlo()
        if use_tls:
            server.starttls()
        if smtp_user and smtp_pass:
            server.login(smtp_user, smtp_pass)

        server.sendmail(from_email, [to_email], msg.as_string())
        server.quit()
        logging.info(f"✅ Email sent to {to_email} with subject '{subject}'")

    except Exception as e:
        logging.exception(f"❌ Failed to send email to {to_email}: {e}")


def send_email_async(app, **kwargs):
    import threading
    def send_in_thread():
        with app.app_context():
            try:
                from utils import send_email
                from models import EmailLog
                import json
                from datetime import datetime, timezone

                # --- Extract arguments ---
                subject = kwargs.get("subject")
                to_email = kwargs.get("to_email")
                template_name = kwargs.get("template_name")
                context = kwargs.get("context", {})
                inline_images = kwargs.get("inline_images", {})
                html_body = kwargs.get("html_body")
                timestamp_override = kwargs.get("timestamp_override")

                # ✅ FINAL SAFETY: If html_body exists, force clear template_name/context
                if html_body:
                    template_name = None
                    context = {}

                # --- Send the email ---
                send_email(
                    subject=subject,
                    to_email=to_email,
                    template_name=template_name,
                    context=context,
                    inline_images=inline_images,
                    html_body=html_body,
                    timestamp_override=timestamp_override
                )

                # --- Save EmailLog after successful send ---
                def format_dt(dt):
                    return dt.strftime('%Y-%m-%d %H:%M') if isinstance(dt, datetime) else dt

                db.session.add(EmailLog(
                    to_email=to_email,
                    subject=subject,
                    pass_code=context.get("hockey_pass", {}).get("pass_code") if context else None,
                    template_name=template_name or "",
                    context_json=json.dumps({
                        "user_name": context.get("hockey_pass", {}).get("user_name") if context else None,
                        "created_date": format_dt(context.get("hockey_pass", {}).get("pass_created_dt")) if context else None,
                        "remaining_games": context.get("hockey_pass", {}).get("games_remaining") if context else None,
                        "special_message": context.get("special_message", "") if context else ""
                    }),
                    result="SENT",
                    timestamp=timestamp_override or datetime.now(timezone.utc)
                ))
                db.session.commit()

            except Exception as e:
                import traceback
                traceback.print_exc()

                from models import EmailLog

                db.session.add(EmailLog(
                    to_email=kwargs.get("to_email"),
                    subject=kwargs.get("subject"),
                    pass_code=kwargs.get("context", {}).get("hockey_pass", {}).get("pass_code") if kwargs.get("context") else None,
                    template_name=kwargs.get("template_name") or "",
                    context_json=json.dumps({"error": str(e)}),
                    result="FAILED",
                    error_message=str(e),
                    timestamp=kwargs.get("timestamp_override") or datetime.now(timezone.utc)
                ))
                db.session.commit()

    thread = threading.Thread(target=send_in_thread)
    thread.start()


def notify_signup_event(app, *, signup, activity, timestamp=None):
    from utils import send_email_async, get_setting
    from flask import render_template_string, url_for
    import os
    import json
    import base64
    from datetime import datetime, timezone

    timestamp = timestamp or datetime.now(timezone.utc)

    # 🧠 Same logic as notify_pass_event
    subject = get_setting("SUBJECT_signup", "Confirmation d'inscription")
    title = get_setting("TITLE_signup", "Votre Inscription est Confirmée")
    intro_raw = get_setting("INTRO_signup", "")
    conclusion_raw = get_setting("CONCLUSION_signup", "")
    theme = get_setting("THEME_signup", "signup.html")

    # Render intro and conclusion manually
    intro = render_template_string(intro_raw, user_name=signup.user.name, activity_name=activity.name)
    conclusion = render_template_string(conclusion_raw, user_name=signup.user.name, activity_name=activity.name)

    # Build context
    context = {
        "user_name": signup.user.name,
        "user_email": signup.user.email,
        "phone_number": signup.user.phone_number,
        "activity_name": activity.name,
        "activity_price": f"${activity.price_per_user:.2f}",
        "sessions_included": activity.sessions_included,
        "payment_instructions": activity.payment_instructions,
        "title": title,
        "intro_text": intro,
        "conclusion_text": conclusion,
        "logo_url": url_for("static", filename="uploads/logo.png"),
    }

    # Find compiled template
    compiled_folder = os.path.join("templates/email_templates", theme.replace(".html", "_compiled"))
    index_path = os.path.join(compiled_folder, "index.html")
    json_path = os.path.join(compiled_folder, "inline_images.json")
    use_compiled = os.path.exists(index_path) and os.path.exists(json_path)

    inline_images = {}

    if use_compiled:
        with open(index_path, "r", encoding="utf-8") as f:
            raw_html = f.read()
        html_body = render_template_string(raw_html, **context)

        with open(json_path, "r", encoding="utf-8") as f:
            cid_map = json.load(f)
        for cid, img_base64 in cid_map.items():
            inline_images[cid] = base64.b64decode(img_base64)

        send_email_async(
            app=app,
            subject=subject,
            to_email=signup.user.email,
            html_body=html_body,
            inline_images=inline_images,
            timestamp_override=timestamp
        )

    else:
        # fallback if compiled missing
        send_email_async(
            app=app,
            subject=subject,
            to_email=signup.user.email,
            template_name=theme,
            context=context,
            timestamp_override=timestamp
        )


def notify_pass_event(app, *, event_type, pass_data, admin_email=None, timestamp=None):
    from utils import send_email_async, get_pass_history_data, generate_qr_code_image, get_setting
    from flask import render_template, render_template_string, url_for
    from datetime import datetime, timezone
    import json
    import base64
    import os

    timestamp = timestamp or datetime.now(timezone.utc)
    event_key = event_type.lower().replace(" ", "_")

    # ✅ Normalize theme_key prefix based on event type
    if event_key in ["pass_created", "pass_redeemed", "payment_received", "payment_late"]:
        theme_key = f"THEME_{event_key}"
        subject_key = f"SUBJECT_{event_key}"
        title_key = f"TITLE_{event_key}"
        intro_key = f"INTRO_{event_key}"
        conclusion_key = f"CONCLUSION_{event_key}"
    else:
        theme_key = f"THEME_pass_{event_key}"
        subject_key = f"SUBJECT_pass_{event_key}"
        title_key = f"TITLE_pass_{event_key}"
        intro_key = f"INTRO_pass_{event_key}"
        conclusion_key = f"CONCLUSION_pass_{event_key}"

    theme = get_setting(theme_key, "confirmation.html")
    print("🧪 Raw get_setting theme key:", theme_key)
    print("🧪 theme value from DB:", theme)

    subject = get_setting(subject_key, f"[Minipass] {event_type.title()} Notification")
    title = get_setting(title_key, f"{event_type.title()} Confirmation")
    intro_raw = get_setting(intro_key, "")
    conclusion_raw = get_setting(conclusion_key, "")

    # ✅ Normalize cross-model values
    games_remaining = getattr(pass_data, "games_remaining", None) or getattr(pass_data, "uses_remaining", 0)
    activity_display = getattr(pass_data, "activity", "")
    if hasattr(activity_display, "name"):
        activity_display = activity_display.name

    intro = render_template_string(intro_raw, pass_data=pass_data, default_qt=games_remaining, activity_list=activity_display)
    conclusion = render_template_string(conclusion_raw, pass_data=pass_data, default_qt=games_remaining, activity_list=activity_display)

    print("🔔 Email debug - subject:", subject)
    print("🔔 Email debug - title:", title)
    print("🔔 Email debug - intro:", intro[:80])

    qr_data = generate_qr_code_image(pass_data.pass_code).read()
    history = get_pass_history_data(pass_data.pass_code, fallback_admin_email=admin_email)

    context = {
        "pass_data": {
            "pass_code": pass_data.pass_code,
            "user_name": getattr(pass_data, "user_name", None) or getattr(getattr(pass_data, "user", None), "name", ""),
            "activity": activity_display,
            "games_remaining": games_remaining,
            "sold_amt": pass_data.sold_amt,
            "user_email": getattr(pass_data, "user_email", None) or getattr(getattr(pass_data, "user", None), "email", ""),
            "phone_number": getattr(pass_data, "phone_number", None) or getattr(getattr(pass_data, "user", None), "phone_number", ""),
            "pass_created_dt": getattr(pass_data, "pass_created_dt", getattr(pass_data, "created_dt", None)),
            "paid_ind": getattr(pass_data, "paid_ind", getattr(pass_data, "paid", False))
        },
        "title": title,
        "intro_text": intro,
        "conclusion_text": conclusion,
        "owner_html": render_template("email_blocks/owner_card_inline.html", pass_data=pass_data),
        "history_html": render_template("email_blocks/history_table_inline.html", history=history),
        "email_info": "",
        "logo_url": url_for("static", filename="uploads/logo.png"),
        "special_message": ""
    }

    compiled_folder = os.path.join("templates/email_templates", theme.replace(".html", "_compiled"))
    index_path = os.path.join(compiled_folder, "index.html")
    json_path = os.path.join(compiled_folder, "inline_images.json")
    use_compiled = os.path.exists(index_path) and os.path.exists(json_path)

    if use_compiled:
        with open(index_path, "r") as f:
            raw_html = f.read()
        html_body = render_template_string(raw_html, **context)

        with open(json_path, "r") as f:
            inline_images = {cid: base64.b64decode(data) for cid, data in json.load(f).items()}
        inline_images["qr_code"] = qr_data

        logo_path = os.path.join(compiled_folder.replace("_compiled", ""), "logo.png")
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as logo_file:
                inline_images["logo"] = logo_file.read()
        else:
            print("⚠️ logo.png not found in template folder.")

        send_email_async(
            app,
            subject=subject,
            to_email=getattr(pass_data, "user_email", None) or getattr(getattr(pass_data, "user", None), "email", None),
            html_body=html_body,
            inline_images=inline_images,
            timestamp_override=timestamp
        )
    else:
        inline_images = {
            "qr_code": qr_data,
            "logo_image": open("static/uploads/logo.png", "rb").read()
        }

        send_email_async(
            app,
            subject=subject,
            to_email=pass_data.user_email,
            template_name=theme,
            context=context,
            inline_images=inline_images,
            timestamp_override=timestamp
        )




import os
import re
import imaplib
import email
from flask import Flask
from models import db
from config import Config
from utils import get_setting

# === ⚙️ Setup minimal Flask app context ===
app = Flask(__name__)
env = os.environ.get("FLASK_ENV", "dev").lower()
db_path = os.path.join("instance", "dev_database.db" if env != "prod" else "prod_database.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config.from_object(Config)
db.init_app(app)

# === 🔍 Extract Interac Emails with Better Regex ===
def extract_all_interac_emails(gmail_user, gmail_password, mail=None):
    results = []

    try:
        subject_keyword = get_setting("BANK_EMAIL_SUBJECT", "Virement Interac :")

        if not mail:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(gmail_user, gmail_password)
            mail.select("inbox")

        status, data = mail.search(None, f'SUBJECT "{subject_keyword}"')
        if status != "OK":
            print(f"📭 No matching emails found for subject: {subject_keyword}")
            return results

        for num in data[0].split():
            status, msg_data = mail.fetch(num, "(BODY.PEEK[] UID)")
            if status != "OK":
                continue

            raw_email = msg_data[0][1]
            uid_line = msg_data[0][0].decode()
            uid_match = re.search(r"UID (\d+)", uid_line)
            uid = uid_match.group(1) if uid_match else None

            msg = email.message_from_bytes(raw_email)
            from_email = email.utils.parseaddr(msg.get("From"))[1]
            subject_raw = msg["Subject"]
            subject = email.header.decode_header(subject_raw)[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode(errors="replace")

            # 🔎 Attempt parsing using both primary and fallback patterns
            amount_match = re.search(r"reçu\s([\d,]+)\s*\$\s*de", subject)
            name_match = re.search(r"de\s(.+?)\set ce montant", subject)

            if not amount_match:
                amount_match = re.search(r"envoyé\s([\d,]+)\s*\$", subject)
            if not name_match:
                name_match = re.search(r":\s*(.*?)\svous a envoyé", subject)

            if amount_match and name_match:
                amt_str = amount_match.group(1).replace(",", ".")
                name = name_match.group(1).strip()

                try:
                    amount = float(amt_str)
                except ValueError:
                    print(f"⚠️ Could not convert amount to float: {amt_str}")
                    continue

                results.append({
                    "bank_info_name": name,
                    "bank_info_amt": amount,
                    "subject": subject,
                    "from_email": from_email,
                    "uid": uid
                })
            else:
                print("❌ Skipped unmatched subject:")
                print(f"    Subject: {subject}")
                print(f"    From:    {from_email}\n")

    except Exception as e:
        print(f"❌ Error reading Gmail: {e}")

    return results

# === 🧪 Main Test Function ===
def run_debug_email_test():
    with app.app_context():
        print("🔐 Loading email credentials from settings...")
        user = get_setting("MAIL_USERNAME")
        pwd = get_setting("MAIL_PASSWORD")
        subject_keyword = get_setting("BANK_EMAIL_SUBJECT", "Virement Interac :")

        if not user or not pwd:
            print("❌ MAIL_USERNAME or MAIL_PASSWORD missing in settings")
            return

        print(f"📬 Connecting to Gmail as: {user}")
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(user, pwd)
        mail.select("inbox")

        print(f"🔍 Scanning emails with subject: '{subject_keyword}' (no sender filtering)")
        matches = extract_all_interac_emails(user, pwd, mail)

        print(f"\n📦 Found {len(matches)} successfully parsed Interac emails:\n")
        for idx, match in enumerate(matches, 1):
            print(f"--- Email #{idx} ---")
            print(f"From:    {match.get('from_email')}")
            print(f"Subject: {match.get('subject')}")
            print(f"Name:    {match.get('bank_info_name')}")
            print(f"Amount:  ${match.get('bank_info_amt')}")
            print(f"UID:     {match.get('uid')}")
            print("----------------------------\n")

        mail.logout()

# === Run ===
if __name__ == "__main__":
    run_debug_email_test()

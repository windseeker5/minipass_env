#!/usr/bin/env python3
"""
Simple test to check if Flask-Mail is working at all
"""

from flask import Flask
from flask_mail import Message, Mail
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
app.config['MAIL_PORT'] = int(os.getenv("MAIL_PORT", 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_DEFAULT_SENDER", "info@minipass.me")

mail = Mail(app)

with app.app_context():
    msg = Message(
        subject="Simple Test Email",
        recipients=["kdresdell@gmail.com"],
        body="This is a plain text test email to verify Flask-Mail is working.",
        html="<h1>Test Email</h1><p>This is a simple HTML test.</p>"
    )

    print("Sending simple test email...")
    print(f"Config: {app.config['MAIL_SERVER']}:{app.config['MAIL_PORT']}")
    print(f"From: {app.config['MAIL_DEFAULT_SENDER']}")
    print(f"To: kdresdell@gmail.com")

    mail.send(msg)
    print("✅ Simple email sent!")

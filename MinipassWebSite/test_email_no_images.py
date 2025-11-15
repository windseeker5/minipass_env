#!/usr/bin/env python3
"""
Test deployment email WITHOUT image attachments
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
        subject="🎉 Test WITHOUT images",
        recipients=["kdresdell@gmail.com"],
        body="Test without attachments",
        html="<h1>Test</h1><p>This email has NO image attachments</p>"
    )

    print("Sending email WITHOUT images...")
    mail.send(msg)
    print("✅ Sent!")

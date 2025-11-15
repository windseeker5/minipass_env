#!/usr/bin/env python3
"""
Test deployment email with ONLY welcom3.jpg
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
        subject="🎉 Test with ONE image (welcom3.jpg)",
        recipients=["kdresdell@gmail.com"],
        body="Test with one image",
        html='<h1>Test</h1><img src="cid:welcom3.jpg" />'
    )

    # Attach welcom3.jpg
    hero_path = os.path.join("static", "image", "welcom3.jpg")
    print(f"Attaching: {hero_path}")
    with open(hero_path, "rb") as f:
        msg.attach(
            filename="welcom3.jpg",
            content_type="image/jpeg",
            data=f.read(),
            disposition="inline",
            headers={"Content-ID": "<welcom3.jpg>"}
        )

    print("Sending email with ONE image...")
    mail.send(msg)
    print("✅ Sent!")

#!/usr/bin/env python3
"""
Test deployment email with BOTH images
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
        subject="🎉 Test with TWO images",
        recipients=["kdresdell@gmail.com"],
        body="Test with two images",
        html='<h1>Test</h1><img src="cid:welcom3.jpg" /><br><img src="cid:youtube-thumbnail.jpg" />'
    )

    # Attach welcom3.jpg
    hero_path = os.path.join("static", "image", "welcom3.jpg")
    print(f"Attaching 1: {hero_path}")
    with open(hero_path, "rb") as f:
        msg.attach(
            filename="welcom3.jpg",
            content_type="image/jpeg",
            data=f.read(),
            disposition="inline",
            headers={"Content-ID": "<welcom3.jpg>"}
        )

    # Attach YouTube thumbnail
    thumbnail_path = os.path.join("static", "image", "youtube-thumbnail.jpg")
    print(f"Attaching 2: {thumbnail_path}")
    with open(thumbnail_path, "rb") as f:
        msg.attach(
            filename="youtube-thumbnail.jpg",
            content_type="image/jpeg",
            data=f.read(),
            disposition="inline",
            headers={"Content-ID": "<youtube-thumbnail.jpg>"}
        )

    print("Sending email with TWO images...")
    mail.send(msg)
    print("✅ Sent!")

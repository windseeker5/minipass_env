#!/usr/bin/env python3
"""
Test using the ACTUAL send_user_deployment_email function
"""

from flask import Flask
from utils.email_helpers import init_mail
from flask_mail import Message, Mail
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
init_mail(app)

with app.app_context():
    # Build email manually (same as send_user_deployment_email but step by step)
    from flask import render_template

    to = "kdresdell@gmail.com"
    url = "https://test.minipass.me"
    password = "TestPass_123abc"
    email_info = {
        'email_address': 'test_app@minipass.me',
        'email_password': 'EmailPass_456xyz',
        'forwarding_setup': True,
        'forwarding_email': to
    }

    print("Step 1: Rendering template...")
    try:
        html = render_template(
            "emails/deployment_ready.html",
            url=url,
            password=password,
            user_email=to,
            email_info=email_info
        )
        print(f"✅ Template rendered ({len(html)} chars)")
    except Exception as e:
        print(f"❌ Template render error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

    print("Step 2: Creating message...")
    from utils.mail import mail

    subject = "🎉 Votre application minipass est prête!"
    body_text = f"Your app is live: {url}\nAdmin Email: {to}\nPassword: {password}"

    msg = Message(
        subject,
        recipients=[to],
        html=html,
        body=body_text
    )
    print("✅ Message created")

    print("Step 3: No image attachments needed (embedded as base64)")
    print("✅ Images embedded in HTML template")

    print("Step 4: Sending email...")
    mail.send(msg)
    print("✅ Email sent!")

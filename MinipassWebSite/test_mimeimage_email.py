#!/usr/bin/env python3
"""
Test the FIXED send_user_deployment_email function with MIMEImage
"""

from flask import Flask
from utils.email_helpers import init_mail, send_user_deployment_email
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
init_mail(app)

with app.app_context():
    to = "kdresdell@gmail.com"
    url = "https://test.minipass.me"
    password = "TestPass_123abc"
    email_info = {
        'email_address': 'test_app@minipass.me',
        'email_password': 'EmailPass_456xyz',
        'forwarding_setup': True,
        'forwarding_email': to
    }

    print("🚀 Testing send_user_deployment_email with MIMEImage...")
    print(f"   To: {to}")
    print(f"   Images: welcom4.jpg + thumb-youtube.jpg")
    print()

    try:
        send_user_deployment_email(to, url, password, email_info)
        print("✅ Email sent successfully!")
        print()
        print("📧 Check your Gmail inbox:")
        print("   - Hero image should display (BIENVENUE fox)")
        print("   - YouTube thumbnail should display (GETTING STARTED)")
        print("   - NO attachments should be visible")
        print("   - All text should be in French")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

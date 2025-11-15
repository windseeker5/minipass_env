#!/usr/bin/env python3
"""
Test script to send deployment email without full deployment process.
Usage: python test_deployment_email.py [email_address]
"""

import sys
import os
from flask import Flask
from utils.email_helpers import init_mail, send_user_deployment_email

def send_test_email(recipient_email=None):
    """Send a test deployment email with mock data."""

    # Use provided email or default to your email
    if not recipient_email:
        recipient_email = "kdresdell@gmail.com"

    print(f"📧 Sending test deployment email to: {recipient_email}")

    # Initialize Flask app (required for Flask-Mail)
    app = Flask(__name__)
    app.config['TESTING'] = True

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Initialize mail
    init_mail(app)

    # Mock data for testing
    test_url = "https://test.minipass.me"
    test_password = "TestPass_123abc"

    # Mock email info (optional - comment out to test without email account)
    test_email_info = {
        'email_address': 'test_app@minipass.me',
        'email_password': 'EmailPass_456xyz',
        'forwarding_setup': True
    }

    # To test WITHOUT email account info, uncomment this line:
    # test_email_info = None

    with app.app_context():
        try:
            print(f"🔧 Mail server: {app.config['MAIL_SERVER']}:{app.config['MAIL_PORT']}")
            print(f"🔧 Sender: {app.config['MAIL_DEFAULT_SENDER']}")
            print(f"🔧 Using TLS: {app.config.get('MAIL_USE_TLS', False)}")

            send_user_deployment_email(
                to=recipient_email,
                url=test_url,
                password=test_password,
                email_info=test_email_info
            )
            print("\n✅ Test email sent successfully!")
            print(f"\n📋 Test data used:")
            print(f"   URL: {test_url}")
            print(f"   Admin Email: {recipient_email}")
            print(f"   Admin Password: {test_password}")
            if test_email_info:
                print(f"   Email Account: {test_email_info['email_address']}")
                print(f"   Email Password: {test_email_info['email_password']}")
                print(f"   Forwarding: {test_email_info['forwarding_setup']}")

            print(f"\n📬 Check your inbox at: {recipient_email}")
            print("💡 If not received, check your spam/junk folder")

        except Exception as e:
            print(f"\n❌ Error sending email: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    # Get email from command line argument or use default
    email = sys.argv[1] if len(sys.argv) > 1 else None
    send_test_email(email)

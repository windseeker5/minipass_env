#!/usr/bin/env python3
"""Preview email template in browser"""
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def preview():
    return render_template(
        "emails/deployment_ready.html",
        url="https://test.minipass.me",
        password="TestPass_123abc",
        user_email="test@example.com",
        email_info={
            'email_address': 'test_app@minipass.me',
            'email_password': 'EmailPass_456xyz',
            'forwarding_setup': True,
            'forwarding_email': 'test@example.com'
        }
    )

if __name__ == '__main__':
    print("\n🌐 Opening email preview at: http://localhost:5555")
    print("Press Ctrl+C to stop\n")
    app.run(port=5555, debug=True)

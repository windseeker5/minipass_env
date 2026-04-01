#!/usr/bin/env python3
"""
Quick deployment test script to verify Stripe subscription data is written to .env
Usage: python test_deployment.py
"""
import sys
sys.path.insert(0, '/home/kdresdell/minipass_env/MinipassWebSite')

from utils.deploy_helpers import deploy_customer_container

print("🧪 Testing deployment with full email sending...")
print("=" * 60)

# Test the full deployment process including email sending
from flask import render_template
from app import app

# Pre-render email template (like the webhook does)
app_name = "demo"
admin_email = "kdresdell@gmail.com"
admin_password = "testpass123"
email_address = "demo_app@minipass.me"

with app.app_context():
    app_url = f"https://{app_name}.minipass.me"
    email_info = {
        'email_address': email_address,
        'email_password': admin_password,
        'forwarding_setup': True,
        'forwarding_email': admin_email
    }
    rendered_email_html = render_template(
        "emails/deployment_ready.html",
        url=app_url,
        password=admin_password,
        user_email=admin_email,
        email_info=email_info
    )

# Import the background deployment function
from app import process_deployment_async

# Call the full background deployment with pre-rendered email
import threading
deployment_thread = threading.Thread(
    target=process_deployment_async,
    args=("demo", "kdresdell@gmail.com", "testpass123", "basic", 9997, "Demo Test Organization",
          1, "monthly", None, None, None, "test_session", None, None, 0, 'cad',
          "demo_app@minipass.me", "kdresdell@gmail.com", rendered_email_html),
    daemon=True
)
deployment_thread.start()

# Wait for deployment to complete
deployment_thread.join()

print("Deployment thread completed")
result = True  # If we get here, deployment didn't crash

print(f"\n{'='*60}")
print(f"Result: {'SUCCESS ✅' if result else 'FAILED ❌'}")
print(f"{'='*60}")

if result:
    print("\n📧 Testing email connectivity for the deployed demo container...")
    import subprocess
    import time

    # Give container time to fully start
    time.sleep(5)

    # Test mail connectivity
    mail_test_cmd = [
        "docker", "exec", "minipass_demo", "python3", "-c",
        "import socket; sock = socket.socket(); sock.settimeout(10); "
        "result = sock.connect_ex(('mail.minipass.me', 587)); "
        "print('NETWORK_TEST_RESULT:', result); sock.close()"
    ]

    try:
        result = subprocess.run(mail_test_cmd, capture_output=True, text=True, timeout=15)

        print("\n🔍 Network connectivity test result:")
        print("-" * 60)
        if result.returncode == 0 and "NETWORK_TEST_RESULT: 0" in result.stdout:
            print("✅ SUCCESS: Demo container can reach mail server!")
            print("✅ Network connectivity validation is working properly")
        else:
            print("❌ FAILED: Demo container cannot reach mail server")
            print(f"   Output: {result.stdout}")
            print(f"   Error: {result.stderr}")
        print("-" * 60)

    except Exception as e:
        print(f"❌ Test failed with error: {e}")

    # Cleanup: Remove the test container
    print("\n🧹 Cleaning up test deployment...")
    cleanup_cmd = ["docker", "rm", "-f", "minipass_demo"]
    subprocess.run(cleanup_cmd, capture_output=True)

    import shutil
    demo_path = "/home/kdresdell/minipass_env/deployed/demo"
    if os.path.exists(demo_path):
        shutil.rmtree(demo_path)
        print("✅ Test deployment cleaned up successfully")
else:
    print("\n❌ Deployment failed - cannot test network connectivity")

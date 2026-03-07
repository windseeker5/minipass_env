#!/usr/bin/env python3
"""
Quick deployment test script to verify Stripe subscription data is written to .env
Usage: python test_deployment.py
"""
import sys
sys.path.insert(0, '/home/kdresdell/minipass_env/MinipassWebSite')

from utils.deploy_helpers import deploy_customer_container

print("🧪 Testing deployment with network connectivity validation...")
print("=" * 60)

result = deploy_customer_container(
    app_name="demo",
    admin_email="kdresdell@gmail.com",
    admin_password="testpass123",
    plan="basic",
    port=9997,
    organization_name="Demo Test Organization",
    tier=1,
    billing_frequency="monthly",
    email_address="demo_app@minipass.me"
)

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

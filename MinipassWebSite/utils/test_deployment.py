#!/usr/bin/env python3
"""
Quick deployment test script
Usage: python test_deployment.py
"""
import sys
sys.path.insert(0, '/home/kdresdell/Documents/DEV/minipass_env/MinipassWebSite')

from utils.deploy_helpers import deploy_customer_container

print("🧪 Testing deployment...")
result = deploy_customer_container(
    app_name="test_deploy",
    admin_email="test@example.com",
    admin_password="test_password_123",
    plan="pro",
    port=9999,
    organization_name="Test Organization",
    tier=2,
    billing_frequency="monthly",
    email_address="test_app@minipass.me"
)

print(f"\n{'='*60}")
print(f"Result: {'SUCCESS ✅' if result else 'FAILED ❌'}")
print(f"{'='*60}")

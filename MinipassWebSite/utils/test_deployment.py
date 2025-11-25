#!/usr/bin/env python3
"""
Quick deployment test script to verify Stripe subscription data is written to .env
Usage: python test_deployment.py
"""
import sys
sys.path.insert(0, '/home/kdresdell/minipass_env/MinipassWebSite')

from utils.deploy_helpers import deploy_customer_container

print("🧪 Testing deployment with Stripe subscription data...")
print("=" * 60)

result = deploy_customer_container(
    app_name="test_stripe",
    admin_email="test@example.com",
    admin_password="test_password_123",
    plan="pro",
    port=9998,
    organization_name="Test Stripe Organization",
    tier=2,
    billing_frequency="monthly",
    email_address="test_stripe_app@minipass.me"
)

print(f"\n{'='*60}")
print(f"Result: {'SUCCESS ✅' if result else 'FAILED ❌'}")
print(f"{'='*60}")

if result:
    print("\n📋 Checking deployed .env file for Stripe configuration...")
    import os
    env_path = "/home/kdresdell/minipass_env/deployed/test_stripe/app/.env"

    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            env_content = f.read()

        print("\n🔍 Stripe-related fields in .env:")
        print("-" * 60)
        for line in env_content.split('\n'):
            if 'STRIPE' in line or 'PAYMENT_AMOUNT' in line or 'SUBSCRIPTION_RENEWAL' in line or 'SECRET_KEY' in line:
                print(f"  {line}")
        print("-" * 60)
    else:
        print(f"❌ .env file not found at {env_path}")

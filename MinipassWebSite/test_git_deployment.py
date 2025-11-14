#!/usr/bin/env python3
"""
Test script for Git-based deployment process
Tests the new git clone deployment without requiring Stripe payment
"""

import sys
import os

# Add the MinipassWebSite directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.deploy_helpers import deploy_customer_container

def test_deployment():
    """
    Test deployment with git clone approach
    """
    print("=" * 80)
    print("GIT-BASED DEPLOYMENT TEST")
    print("=" * 80)
    print()

    # Test parameters
    test_params = {
        "app_name": "test-git-deploy",
        "admin_email": "test@minipass.me",
        "admin_password": "TestPassword123!",
        "plan": "basic",
        "port": 9999,  # Test port
        "organization_name": "Test Organization",
        "tier": 1,
        "billing_frequency": "monthly"
    }

    print("Test Parameters:")
    for key, value in test_params.items():
        if key == "admin_password":
            print(f"  {key}: {'*' * len(value)}")
        else:
            print(f"  {key}: {value}")
    print()

    print("Starting deployment test...")
    print("-" * 80)
    print()

    try:
        result = deploy_customer_container(**test_params)

        print()
        print("=" * 80)
        if result:
            print("✅ DEPLOYMENT TEST SUCCESSFUL!")
            print()
            print("Verification steps:")
            print("1. Check container: docker ps | grep minipass_test-git-deploy")
            print("2. Check logs: docker logs minipass_test-git-deploy")
            print("3. Access app: https://test-git-deploy.minipass.me")
            print("4. Check deployment dir: ls -la /home/kdresdell/Documents/DEV/minipass_env/deployed/test-git-deploy/")
            print()
            print("To clean up:")
            print("  cd /home/kdresdell/Documents/DEV/minipass_env/deployed/test-git-deploy")
            print("  docker-compose down")
            print("  cd .. && rm -rf test-git-deploy")
        else:
            print("❌ DEPLOYMENT TEST FAILED")
            print()
            print("Check the logs at: ./subscribed_app.log")
        print("=" * 80)

        return result

    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ DEPLOYMENT TEST FAILED WITH EXCEPTION")
        print(f"Error: {str(e)}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_deployment()
    sys.exit(0 if success else 1)

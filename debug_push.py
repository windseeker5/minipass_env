#!/usr/bin/env python3
"""
Debug script to test push notifications step by step
"""
import os
import sys

# Change to app directory
os.chdir('/app')

def test_push_notifications():
    from app import app
    from models import PushSubscription
    from utils import send_push_notification_to_admins, get_or_create_vapid_keys
    from pywebpush import webpush, WebPushException
    import json

    with app.app_context():
        print("🔍 PUSH NOTIFICATION DEBUG TEST")
        print("=" * 50)

        # 1. Check VAPID keys
        print("\n1. Testing VAPID keys...")
        try:
            vapid_keys = get_or_create_vapid_keys()
            print(f"✅ VAPID keys OK - Public: {vapid_keys['public_key'][:20]}...")
        except Exception as e:
            print(f"❌ VAPID keys failed: {e}")
            return

        # 2. Check subscriptions
        print("\n2. Checking push subscriptions...")
        subscriptions = PushSubscription.query.all()
        print(f"📱 Found {len(subscriptions)} subscriptions:")

        for i, sub in enumerate(subscriptions, 1):
            print(f"  Subscription {i}:")
            print(f"    - ID: {sub.id}")
            print(f"    - Admin ID: {sub.admin_id}")
            print(f"    - Endpoint: {sub.endpoint}")
            print(f"    - Created: {sub.created_dt}")
            print(f"    - Last used: {sub.last_used_dt}")
            print(f"    - P256DH length: {len(sub.p256dh_key)}")
            print(f"    - Auth length: {len(sub.auth_key)}")

        if not subscriptions:
            print("❌ No push subscriptions found! You need to subscribe first.")
            return

        # 3. Test individual subscriptions
        print("\n3. Testing each subscription individually...")

        payload = json.dumps({
            'title': '🔧 DIRECT TEST',
            'body': 'Testing individual subscription - if you see this, it works!',
            'url': '/',
            'tag': 'direct_test',
            'icon': '/static/icons/icon-192x192.png',
            'badge': '/static/favicon.png'
        })

        vapid_claims_email = "mailto:admin@minipass.me"

        for i, sub in enumerate(subscriptions, 1):
            print(f"\n  Testing subscription {i} (ID: {sub.id}):")

            subscription_info = {
                'endpoint': sub.endpoint,
                'keys': {
                    'p256dh': sub.p256dh_key,
                    'auth': sub.auth_key
                }
            }

            print(f"    - Endpoint: {subscription_info['endpoint']}")
            print(f"    - Keys present: p256dh={bool(subscription_info['keys']['p256dh'])}, auth={bool(subscription_info['keys']['auth'])}")

            try:
                response = webpush(
                    subscription_info=subscription_info,
                    data=payload,
                    vapid_private_key=vapid_keys['private_key'],
                    vapid_claims={'sub': vapid_claims_email},
                    timeout=30
                )
                print(f"    ✅ SUCCESS: Push sent! Response: {response}")

                # Update last_used timestamp
                from datetime import datetime, timezone
                sub.last_used_dt = datetime.now(timezone.utc)

            except WebPushException as e:
                print(f"    ❌ WebPushException: {e}")
                if hasattr(e, 'response') and e.response:
                    print(f"       Status: {e.response.status_code}")
                    print(f"       Body: {e.response.text}")
            except Exception as e:
                print(f"    ❌ Unexpected error: {e}")
                import traceback
                traceback.print_exc()

        # 4. Test the main function
        print("\n4. Testing main send_push_notification_to_admins function...")
        try:
            sent_count = send_push_notification_to_admins(
                title='🎯 FINAL TEST',
                body='This is the final test using the main function',
                url='/',
                tag='final_test'
            )
            print(f"✅ Main function sent to {sent_count} devices")
        except Exception as e:
            print(f"❌ Main function failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_push_notifications()
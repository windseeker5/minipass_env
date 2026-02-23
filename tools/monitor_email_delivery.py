#!/usr/bin/env python3
"""
Email Delivery Monitor for Minipass
Monitors mail server logs and queue for delivery status
"""

import subprocess
import re
import json
from datetime import datetime
from collections import defaultdict

def get_mail_queue_status():
    """Get current mail queue status"""
    try:
        result = subprocess.run(
            ["docker-compose", "exec", "-T", "mailserver", "postqueue", "-p"],
            capture_output=True, text=True, cwd="/home/kdresdell/minipass_env"
        )

        queue_emails = []
        gmail_blocked = 0
        other_blocked = 0

        for line in result.stdout.split('\n'):
            if '@gmail.com' in line:
                gmail_blocked += 1
            elif '@' in line and 'gmail.com' not in line:
                other_blocked += 1

        return {
            'gmail_blocked': gmail_blocked,
            'other_blocked': other_blocked,
            'total_queue': gmail_blocked + other_blocked
        }
    except Exception as e:
        return {'error': str(e)}

def get_recent_mail_logs():
    """Get recent mail server delivery logs"""
    try:
        result = subprocess.run(
            ["docker-compose", "exec", "-T", "mailserver", "tail", "-50", "/var/log/mail/mail.log"],
            capture_output=True, text=True, cwd="/home/kdresdell/minipass_env"
        )

        deliveries = []
        bounces = []
        gmail_issues = []

        for line in result.stdout.split('\n'):
            if 'status=sent' in line:
                # Successful delivery
                match = re.search(r'to=<([^>]+)>', line)
                if match:
                    email = match.group(1)
                    deliveries.append({
                        'email': email,
                        'status': 'delivered',
                        'time': datetime.now().strftime('%H:%M:%S')
                    })

            elif 'status=bounced' in line or '4.7.28' in line or 'rate limit' in line.lower():
                # Failed delivery
                match = re.search(r'to=<([^>]+)>', line)
                if match:
                    email = match.group(1)
                    if '@gmail.com' in email:
                        gmail_issues.append({
                            'email': email,
                            'issue': 'Gmail rate limit' if '4.7.28' in line else 'Bounced',
                            'time': datetime.now().strftime('%H:%M:%S')
                        })
                    else:
                        bounces.append({
                            'email': email,
                            'issue': 'Bounced',
                            'time': datetime.now().strftime('%H:%M:%S')
                        })

        return {
            'successful_deliveries': deliveries[-10:],  # Last 10
            'gmail_issues': gmail_issues[-5:],          # Last 5
            'other_bounces': bounces[-5:]               # Last 5
        }
    except Exception as e:
        return {'error': str(e)}

def check_email_reputation():
    """Check basic email server reputation indicators"""
    try:
        # Check if DKIM/SPF/DMARC are configured
        result = subprocess.run(
            ["docker-compose", "exec", "-T", "mailserver", "cat", "/tmp/docker-mailserver/opendkim/keys/minipass.me/mail.txt"],
            capture_output=True, text=True, cwd="/home/kdresdell/minipass_env"
        )

        dkim_configured = "DKIM1" in result.stdout

        return {
            'dkim_configured': dkim_configured,
            'server_status': 'running' if result.returncode == 0 else 'issues'
        }
    except Exception as e:
        return {'error': str(e)}

def main():
    """Main monitoring function"""
    print("🔍 Minipass Email Delivery Monitor")
    print("=" * 50)
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Queue Status
    print("📬 Mail Queue Status:")
    queue = get_mail_queue_status()
    if 'error' in queue:
        print(f"   ❌ Error: {queue['error']}")
    else:
        print(f"   Gmail blocked: {queue['gmail_blocked']}")
        print(f"   Other blocked: {queue['other_blocked']}")
        print(f"   Total in queue: {queue['total_queue']}")
    print()

    # Recent Deliveries
    print("📊 Recent Email Activity (Last hour):")
    logs = get_recent_mail_logs()
    if 'error' in logs:
        print(f"   ❌ Error: {logs['error']}")
    else:
        print(f"   ✅ Successful deliveries: {len(logs['successful_deliveries'])}")
        for delivery in logs['successful_deliveries']:
            provider = delivery['email'].split('@')[1] if '@' in delivery['email'] else 'unknown'
            print(f"      • {delivery['email']} ({provider}) - {delivery['time']}")

        print(f"   ❌ Gmail issues: {len(logs['gmail_issues'])}")
        for issue in logs['gmail_issues']:
            print(f"      • {issue['email']} - {issue['issue']} - {issue['time']}")

        print(f"   ⚠️ Other bounces: {len(logs['other_bounces'])}")
        for bounce in logs['other_bounces']:
            print(f"      • {bounce['email']} - {bounce['time']}")
    print()

    # Reputation Check
    print("🔒 Email Server Health:")
    reputation = check_email_reputation()
    if 'error' in reputation:
        print(f"   ❌ Error: {reputation['error']}")
    else:
        print(f"   DKIM configured: {'✅' if reputation['dkim_configured'] else '❌'}")
        print(f"   Server status: {'✅' if reputation['server_status'] == 'running' else '❌'}")
    print()

    # Recommendations
    gmail_blocked = queue.get('gmail_blocked', 0) if 'error' not in queue else 0
    if gmail_blocked > 0:
        print("🚨 RECOMMENDATIONS:")
        print("   • Gmail rate limit still active")
        print("   • Wait another 12-24 hours")
        print("   • Monitor this script every few hours")
    else:
        print("✅ GOOD NEWS:")
        print("   • No Gmail emails in queue")
        print("   • Rate limit may have cleared")
        print("   • Ready for new customer emails")

if __name__ == "__main__":
    main()
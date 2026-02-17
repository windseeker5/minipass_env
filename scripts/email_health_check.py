#!/usr/bin/env python3
"""
Email Health Check Script
Monitors email delivery health and alerts on issues
"""

import sqlite3
from datetime import datetime, timedelta
import sys

# Database path
DB_PATH = "/home/kdresdell/minipass_env/app/instance/minipass.db"

def check_email_health():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get emails from last 24 hours
    yesterday = datetime.now() - timedelta(days=1)

    # Total emails sent
    cursor.execute("""
        SELECT COUNT(*) FROM email_log
        WHERE timestamp >= ?
    """, (yesterday,))
    total_sent = cursor.fetchone()[0]

    # Failed emails
    cursor.execute("""
        SELECT COUNT(*) FROM email_log
        WHERE timestamp >= ? AND result = 'FAILED'
    """, (yesterday,))
    failed_count = cursor.fetchone()[0]

    # Success rate
    success_rate = ((total_sent - failed_count) / total_sent * 100) if total_sent > 0 else 0

    # Gmail-specific failures
    cursor.execute("""
        SELECT COUNT(*) FROM email_log
        WHERE timestamp >= ?
        AND result = 'FAILED'
        AND to_email LIKE '%@gmail.com'
    """, (yesterday,))
    gmail_failures = cursor.fetchone()[0]

    print("╔════════════════════════════════════════════════════════════════╗")
    print("║          Minipass Email Health Report (24 hours)              ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print(f"\n📊 Total Emails Sent: {total_sent}")
    print(f"✅ Successfully Delivered: {total_sent - failed_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"📈 Success Rate: {success_rate:.1f}%")
    print(f"🎯 Gmail Failures: {gmail_failures}")

    # Alert conditions
    alerts = []
    if success_rate < 95:
        alerts.append(f"⚠️  Low success rate: {success_rate:.1f}% (target: >95%)")

    if gmail_failures > 5:
        alerts.append(f"⚠️  High Gmail failure count: {gmail_failures} (investigate!)")

    if total_sent == 0:
        alerts.append("⚠️  No emails sent in last 24 hours (expected?)")

    if alerts:
        print("\n🚨 ALERTS:")
        for alert in alerts:
            print(f"   {alert}")
        sys.exit(1)  # Non-zero exit for monitoring
    else:
        print("\n✅ All systems healthy!")
        sys.exit(0)

    conn.close()

if __name__ == "__main__":
    check_email_health()

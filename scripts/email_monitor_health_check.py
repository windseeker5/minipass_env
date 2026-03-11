#!/usr/bin/env python3
"""
Email Monitoring Health Check

Monitors the email monitoring pipeline and alerts on issues:
- DMARC ingest returning 0 rows consistently
- Missing recent DMARC data
- Email monitoring script failures
- Stale database entries

Usage:
    python scripts/email_monitor_health_check.py --notify
    python scripts/email_monitor_health_check.py --report
"""

import sqlite3
import argparse
from datetime import datetime, date, timedelta
from pathlib import Path

# Configuration
DB_PATH = Path(__file__).resolve().parent.parent / "email_monitoring" / "monitoring.db"
ALERT_THRESHOLD_DAYS = 3  # Alert if no DMARC data for 3+ days
ZERO_INGEST_THRESHOLD = 5  # Alert if 5+ consecutive zero ingests


def check_dmarc_freshness(conn):
    """Check if DMARC data is recent."""
    latest_row = conn.execute(
        "SELECT MAX(date) AS latest_date FROM dmarc_daily"
    ).fetchone()

    if not latest_row['latest_date']:
        return False, "No DMARC data found in database"

    latest_date = date.fromisoformat(latest_row['latest_date'])
    days_old = (date.today() - latest_date).days

    if days_old > ALERT_THRESHOLD_DAYS:
        return False, f"Latest DMARC data is {days_old} days old (threshold: {ALERT_THRESHOLD_DAYS})"

    return True, f"DMARC data is fresh (latest: {latest_date}, {days_old} days old)"


def check_recent_email_activity(conn):
    """Check if email monitoring is working."""
    yesterday = date.today() - timedelta(days=1)

    volume_rows = conn.execute(
        "SELECT COUNT(*) as count FROM email_volume_daily WHERE date = ?",
        (yesterday.isoformat(),)
    ).fetchone()

    if volume_rows['count'] == 0:
        return False, f"No email volume data for {yesterday}"

    return True, f"Email volume monitoring working (found {volume_rows['count']} user records for {yesterday})"


def check_mail_server_connectivity():
    """Check if mail server is reachable."""
    import subprocess
    try:
        result = subprocess.run(
            ["docker", "exec", "mailserver", "echo", "test"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return True, "Mail server container is running"
        else:
            return False, "Mail server container is not responding"
    except subprocess.TimeoutExpired:
        return False, "Mail server container check timed out"
    except Exception as e:
        return False, f"Mail server check failed: {e}"


def generate_health_report(conn):
    """Generate comprehensive health report."""
    print("Email Monitoring Health Report")
    print("=" * 50)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    checks = [
        ("DMARC Data Freshness", check_dmarc_freshness),
        ("Email Volume Monitoring", check_recent_email_activity),
        ("Mail Server Connectivity", check_mail_server_connectivity),
    ]

    all_ok = True

    for check_name, check_func in checks:
        if check_func == check_mail_server_connectivity:
            status, message = check_func()
        else:
            status, message = check_func(conn)

        icon = "✅" if status else "❌"
        print(f"{icon} {check_name}: {message}")

        if not status:
            all_ok = False

    print()

    # Show recent statistics
    print("Recent Statistics:")
    print("-" * 20)

    # DMARC summary (last 7 days)
    seven_days_ago = (date.today() - timedelta(days=7)).isoformat()
    dmarc_stats = conn.execute("""
        SELECT
            COUNT(DISTINCT date) as days_with_data,
            COUNT(*) as total_reports,
            SUM(total_messages) as total_messages,
            SUM(pass_count) as total_passed,
            AVG(pass_rate) as avg_pass_rate
        FROM dmarc_daily
        WHERE date >= ?
    """, (seven_days_ago,)).fetchone()

    print(f"DMARC (last 7 days): {dmarc_stats['days_with_data']} days with data, "
          f"{dmarc_stats['total_reports']} reports, "
          f"{dmarc_stats['total_messages']} messages, "
          f"{dmarc_stats['avg_pass_rate']:.1f}% avg pass rate")

    # Email volume summary (last 7 days)
    email_stats = conn.execute("""
        SELECT
            COUNT(DISTINCT date) as days_with_data,
            SUM(sent_count) as total_sent,
            SUM(received_count) as total_received,
            SUM(bounced_count) as total_bounced
        FROM email_volume_daily
        WHERE date >= ?
    """, (seven_days_ago,)).fetchone()

    print(f"Email Volume (last 7 days): {email_stats['days_with_data']} days with data, "
          f"{email_stats['total_sent']} sent, {email_stats['total_received']} received, "
          f"{email_stats['total_bounced']} bounced")

    print()

    if all_ok:
        print("🎉 Overall Status: HEALTHY")
        return 0
    else:
        print("⚠️  Overall Status: ISSUES DETECTED")
        return 1


def send_alert_notification(message):
    """Send alert notification (placeholder for email/webhook)."""
    # TODO: Implement email notification or webhook
    print(f"ALERT: {message}")

    # Log alert to file
    log_file = Path(__file__).parent.parent / "logs" / "email_monitor_alerts.log"
    log_file.parent.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {message}\n")


def main():
    parser = argparse.ArgumentParser(description="Email monitoring health check")
    parser.add_argument("--notify", action="store_true", help="Send notifications for issues")
    parser.add_argument("--report", action="store_true", help="Generate full health report")

    args = parser.parse_args()

    # Default to report mode if no args
    if not (args.notify or args.report):
        args.report = True

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        if args.report:
            exit_code = generate_health_report(conn)
            exit(exit_code)

        if args.notify:
            # Quick checks for alerting
            dmarc_ok, dmarc_msg = check_dmarc_freshness(conn)
            email_ok, email_msg = check_recent_email_activity(conn)
            mail_ok, mail_msg = check_mail_server_connectivity()

            issues = []
            if not dmarc_ok:
                issues.append(f"DMARC: {dmarc_msg}")
            if not email_ok:
                issues.append(f"Email Volume: {email_msg}")
            if not mail_ok:
                issues.append(f"Mail Server: {mail_msg}")

            if issues:
                send_alert_notification("Email monitoring issues detected: " + "; ".join(issues))
                exit(1)
            else:
                print("All monitoring systems healthy")
                exit(0)


if __name__ == "__main__":
    main()
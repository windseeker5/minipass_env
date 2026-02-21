#!/usr/bin/env python3
"""
Bulk Email Monitoring Backfill
------------------------------
Backfills email monitoring data for multiple dates by reading both current
and rotated mail logs.

Usage:
    python scripts/bulk_email_backfill.py --start 2026-02-14 --end 2026-02-21
    python scripts/bulk_email_backfill.py --days 7  # Last 7 days
    python scripts/bulk_email_backfill.py --all     # All available dates
"""

import argparse
import subprocess
from datetime import date, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def run_command(cmd):
    """Run shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running: {cmd}")
        print(f"Error: {e.stderr}")
        return None

def get_available_date_range():
    """Check what date range is available in mail logs"""
    print("Checking available date range in mail logs...")

    # Check oldest date in rotated log
    oldest_line = run_command("docker exec mailserver head -1 /var/log/mail/mail.log.1 2>/dev/null")
    newest_line = run_command("docker exec mailserver tail -1 /var/log/mail/mail.log 2>/dev/null")

    oldest_date = None
    newest_date = None

    if oldest_line:
        # Parse ISO format: 2026-02-14T11:44:32.787789+00:00
        if oldest_line.startswith("202"):
            oldest_date = oldest_line[:10]  # Extract YYYY-MM-DD

    if newest_line:
        if newest_line.startswith("202"):
            newest_date = newest_line[:10]

    # Fallback to checking current log if rotated log doesn't exist
    if not oldest_date:
        oldest_line = run_command("docker exec mailserver head -1 /var/log/mail/mail.log 2>/dev/null")
        if oldest_line and oldest_line.startswith("202"):
            oldest_date = oldest_line[:10]

    return oldest_date, newest_date

def create_enhanced_monitor_script():
    """Create a temporary enhanced version that reads both logs"""
    enhanced_script = BASE_DIR / "scripts" / "temp_enhanced_monitor.py"

    # Read the original script
    with open(BASE_DIR / "scripts" / "email_monitor_to_db.py", 'r') as f:
        original_content = f.read()

    # Replace the log collection method to read both files
    enhanced_content = original_content.replace(
        'def collect_postfix_logs(self) -> str:\n        """Fetch the live mail.log from the running mailserver container."""\n        out = _run("docker exec mailserver cat /var/log/mail/mail.log")',
        '''def collect_postfix_logs(self) -> str:
        """Fetch mail logs from both current and rotated log files."""
        # Read rotated log first (older entries)
        rotated_out = _run("docker exec mailserver cat /var/log/mail/mail.log.1 2>/dev/null") or ""
        # Read current log (newer entries)
        current_out = _run("docker exec mailserver cat /var/log/mail/mail.log 2>/dev/null") or ""

        combined_logs = rotated_out + "\\n" + current_out if rotated_out else current_out

        if not combined_logs.strip():
            print("  [warn] could not read any mail logs — Postfix section skipped")
            return ""
        return combined_logs'''
    )

    # Write enhanced script
    with open(enhanced_script, 'w') as f:
        f.write(enhanced_content)

    # Make it executable
    enhanced_script.chmod(0o755)
    return enhanced_script

def backfill_date_range(start_date, end_date):
    """Backfill email monitoring data for a date range"""
    print(f"Starting bulk backfill from {start_date} to {end_date}")

    # Create enhanced script that reads both log files
    enhanced_script = create_enhanced_monitor_script()

    try:
        current = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)

        processed = 0
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            print(f"\nProcessing {date_str}...")

            # Run the enhanced script for this date
            cmd = f"python3 {enhanced_script} --date {date_str}"
            result = run_command(cmd)

            if result is not None:
                print(f"  ✅ Processed {date_str}")
                processed += 1
            else:
                print(f"  ❌ Failed {date_str}")

            current += timedelta(days=1)

        print(f"\nBackfill complete: {processed} days processed")

    finally:
        # Clean up temporary script
        if enhanced_script.exists():
            enhanced_script.unlink()

def main():
    parser = argparse.ArgumentParser(description="Bulk backfill email monitoring data")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--start", help="Start date (YYYY-MM-DD)")
    group.add_argument("--days", type=int, help="Last N days")
    group.add_argument("--all", action="store_true", help="All available dates")

    parser.add_argument("--end", help="End date (YYYY-MM-DD, only with --start)")

    args = parser.parse_args()

    if args.all:
        oldest, newest = get_available_date_range()
        if not oldest or not newest:
            print("Could not determine available date range")
            return
        print(f"Available range: {oldest} to {newest}")
        backfill_date_range(oldest, newest)

    elif args.days:
        end_date = date.today().strftime("%Y-%m-%d")
        start_date = (date.today() - timedelta(days=args.days-1)).strftime("%Y-%m-%d")
        backfill_date_range(start_date, end_date)

    elif args.start:
        end_date = args.end or args.start
        backfill_date_range(args.start, end_date)

if __name__ == "__main__":
    main()
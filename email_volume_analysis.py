#!/usr/bin/env python3
"""
Minipass Email Volume Analysis Script
Analyzes 8-12 months of email traffic from docker-mailserver logs
"""

import re
import gzip
import csv
import subprocess
import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from pathlib import Path

class EmailVolumeAnalyzer:
    def __init__(self):
        self.log_files = []
        self.sent_emails = []
        self.received_emails = []
        self.bounced_emails = []
        self.data_summary = defaultdict(lambda: defaultdict(int))

    def discover_log_files(self):
        """Discover all available mail log files"""
        try:
            # Get log files from mailserver container
            result = subprocess.run([
                "docker-compose", "exec", "-T", "mailserver",
                "ls", "-la", "/var/log/mail/"
            ], capture_output=True, text=True, cwd="/home/kdresdell/minipass_env")

            log_files = []
            for line in result.stdout.split('\n'):
                if 'mail.log' in line and not 'fail2ban' in line:
                    # Extract filename
                    parts = line.split()
                    if len(parts) >= 9:
                        filename = parts[-1]
                        log_files.append(f"/var/log/mail/{filename}")

            return sorted(log_files)
        except Exception as e:
            print(f"Error discovering log files: {e}")
            return []

    def read_log_file(self, log_path):
        """Read log file from container, handling gzip compression"""
        try:
            if log_path.endswith('.gz'):
                # Handle compressed logs
                result = subprocess.run([
                    "docker-compose", "exec", "-T", "mailserver",
                    "zcat", log_path
                ], capture_output=True, text=True, cwd="/home/kdresdell/minipass_env")
            else:
                # Handle regular logs
                result = subprocess.run([
                    "docker-compose", "exec", "-T", "mailserver",
                    "cat", log_path
                ], capture_output=True, text=True, cwd="/home/kdresdell/minipass_env")

            if result.returncode == 0:
                return result.stdout
            else:
                print(f"Error reading {log_path}: {result.stderr}")
                return ""
        except Exception as e:
            print(f"Error reading {log_path}: {e}")
            return ""

    def parse_log_line(self, line):
        """Parse individual log line for email events"""
        try:
            # Extract timestamp
            timestamp_match = re.match(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', line)
            if not timestamp_match:
                return None

            timestamp_str = timestamp_match.group(1)
            timestamp = datetime.fromisoformat(timestamp_str)

            # Parse successful deliveries (status=sent)
            if 'status=sent' in line:
                # Extract sender and recipient
                to_match = re.search(r'to=<([^>]+)>', line)

                if to_match:
                    to_email = to_match.group(1)

                    # For external deliveries (sent emails), extract from address from queue line
                    if '@minipass.me' not in to_email:
                        # This is an external delivery - look for from= in previous context
                        # Get from address from the log line itself or use pattern matching
                        from_match = re.search(r'from=<([^>]+)>', line)
                        if from_match:
                            from_email = from_match.group(1)
                        else:
                            # Try to infer from the relay or service
                            if 'relay=' in line:
                                relay_match = re.search(r'relay=([^\[,\s]+)', line)
                                if relay_match and 'gmail' in relay_match.group(1):
                                    # This is likely an outbound email
                                    from_email = 'minipass.me'  # Will be refined later
                                else:
                                    from_email = 'unknown'
                            else:
                                from_email = 'unknown'

                        return {
                            'timestamp': timestamp,
                            'type': 'sent',
                            'from': from_email,
                            'to': to_email,
                            'domain': to_email.split('@')[-1] if '@' in to_email else 'unknown'
                        }
                    else:
                        # Local delivery (received email)
                        from_match = re.search(r'from=<([^>]+)>', line)
                        from_email = from_match.group(1) if from_match else 'external'

                        return {
                            'timestamp': timestamp,
                            'type': 'received',
                            'from': from_email,
                            'to': to_email,
                            'domain': from_email.split('@')[-1] if '@' in from_email else 'unknown'
                        }

            # Parse bounces and deferrals
            elif 'status=bounced' in line or 'status=deferred' in line:
                to_match = re.search(r'to=<([^>]+)>', line)

                if to_match:
                    to_email = to_match.group(1)
                    from_match = re.search(r'from=<([^>]+)>', line)
                    from_email = from_match.group(1) if from_match else 'unknown'
                    status = 'bounced' if 'status=bounced' in line else 'deferred'

                    return {
                        'timestamp': timestamp,
                        'type': status,
                        'from': from_email,
                        'to': to_email,
                        'domain': to_email.split('@')[-1] if '@' in to_email else 'unknown'
                    }

            # Also capture "from=" patterns for better source tracking
            elif 'from=<' in line and 'to=<' in line and 'minipass.me' in line:
                # This captures routing information that helps identify sender
                to_match = re.search(r'to=<([^>]+)>', line)
                from_match = re.search(r'from=<([^>]+)>', line)

                if to_match and from_match:
                    to_email = to_match.group(1)
                    from_email = from_match.group(1)

                    # Only capture if it's an outbound email (from minipass.me to external)
                    if '@minipass.me' in from_email and '@minipass.me' not in to_email:
                        return {
                            'timestamp': timestamp,
                            'type': 'routing',  # Special type for routing info
                            'from': from_email,
                            'to': to_email,
                            'domain': to_email.split('@')[-1] if '@' in to_email else 'unknown'
                        }

            return None

        except Exception as e:
            return None

    def analyze_logs(self):
        """Analyze all discovered log files"""
        print("🔍 Discovering mail log files...")
        log_files = self.discover_log_files()
        print(f"Found {len(log_files)} log files: {log_files}")

        all_events = []

        for log_file in log_files:
            print(f"📖 Processing {log_file}...")
            content = self.read_log_file(log_file)

            line_count = 0
            event_count = 0

            for line in content.split('\n'):
                line_count += 1
                if line.strip():
                    event = self.parse_log_line(line)
                    if event:
                        all_events.append(event)
                        event_count += 1

            print(f"   Processed {line_count} lines, found {event_count} email events")

        print(f"📊 Total email events found: {len(all_events)}")
        return all_events

    def generate_summary_stats(self, events):
        """Generate summary statistics from events"""
        stats = {
            'total_events': len(events),
            'by_type': Counter(),
            'by_domain': Counter(),
            'by_month': defaultdict(lambda: {'sent': 0, 'received': 0, 'bounced': 0, 'deferred': 0}),
            'by_week': defaultdict(lambda: {'sent': 0, 'received': 0, 'bounced': 0, 'deferred': 0}),
            'by_address': defaultdict(lambda: {'sent': 0, 'received': 0, 'bounced': 0, 'deferred': 0}),
            'date_range': {'start': None, 'end': None}
        }

        for event in events:
            event_type = event['type']
            domain = event['domain']
            timestamp = event['timestamp']

            # Update date range
            if stats['date_range']['start'] is None or timestamp < stats['date_range']['start']:
                stats['date_range']['start'] = timestamp
            if stats['date_range']['end'] is None or timestamp > stats['date_range']['end']:
                stats['date_range']['end'] = timestamp

            # Count by type (convert routing to sent for stats)
            counted_type = 'sent' if event_type == 'routing' else event_type
            stats['by_type'][counted_type] += 1

            # Count by domain (for external emails)
            if event_type in ['sent', 'bounced', 'deferred', 'routing']:
                stats['by_domain'][domain] += 1

            # Count by month
            month_key = timestamp.strftime('%Y-%m')
            stats['by_month'][month_key][counted_type] += 1

            # Count by week (ISO week)
            week_key = f"{timestamp.year}-W{timestamp.isocalendar()[1]:02d}"
            stats['by_week'][week_key][counted_type] += 1

            # Count by address
            if event_type in ['sent', 'bounced', 'deferred', 'routing']:
                # Sent emails - count by from address
                from_addr = event['from']
                if '@minipass.me' in from_addr:
                    stats['by_address'][from_addr][counted_type] += 1
            else:
                # Received emails - count by to address
                to_addr = event['to']
                if '@minipass.me' in to_addr:
                    stats['by_address'][to_addr][counted_type] += 1

        return stats

    def save_csv_report(self, events, filename='email_volume_report.csv'):
        """Save detailed CSV report"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['timestamp', 'type', 'from_address', 'to_address', 'domain', 'date', 'month', 'week']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for event in sorted(events, key=lambda x: x['timestamp']):
                writer.writerow({
                    'timestamp': event['timestamp'].isoformat(),
                    'type': event['type'],
                    'from_address': event['from'],
                    'to_address': event['to'],
                    'domain': event['domain'],
                    'date': event['timestamp'].strftime('%Y-%m-%d'),
                    'month': event['timestamp'].strftime('%Y-%m'),
                    'week': f"{event['timestamp'].year}-W{event['timestamp'].isocalendar()[1]:02d}"
                })

        print(f"📄 CSV report saved: {filename}")

    def save_summary_report(self, stats, filename='email_summary_report.txt'):
        """Save human-readable summary report"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("📧 MINIPASS EMAIL VOLUME ANALYSIS REPORT\n")
            f.write("=" * 50 + "\n\n")

            # Date range
            if stats['date_range']['start'] and stats['date_range']['end']:
                f.write(f"📅 Analysis Period: {stats['date_range']['start'].strftime('%Y-%m-%d')} to {stats['date_range']['end'].strftime('%Y-%m-%d')}\n")
                days = (stats['date_range']['end'] - stats['date_range']['start']).days
                f.write(f"📊 Total Days Analyzed: {days}\n\n")

            # Overall totals
            f.write("📈 OVERALL VOLUME SUMMARY:\n")
            f.write("-" * 30 + "\n")
            for event_type, count in stats['by_type'].items():
                f.write(f"  {event_type.title()}: {count:,}\n")
            f.write(f"\nTotal Email Events: {stats['total_events']:,}\n\n")

            # By email address
            f.write("📫 VOLUME BY MINIPASS EMAIL ADDRESS:\n")
            f.write("-" * 40 + "\n")
            for address, counts in sorted(stats['by_address'].items()):
                total = sum(counts.values())
                f.write(f"  {address}:\n")
                f.write(f"    Sent: {counts['sent']:,}, Received: {counts['received']:,}, Failed: {counts['bounced'] + counts['deferred']:,}\n")
                f.write(f"    Total: {total:,}\n\n")

            # Top destination domains
            f.write("🌐 TOP DESTINATION DOMAINS (for sent emails):\n")
            f.write("-" * 45 + "\n")
            top_domains = stats['by_domain'].most_common(10)
            for domain, count in top_domains:
                f.write(f"  {domain}: {count:,}\n")
            f.write("\n")

            # Monthly trends
            f.write("📅 MONTHLY EMAIL VOLUME:\n")
            f.write("-" * 25 + "\n")
            f.write(f"{'Month':<8} {'Sent':<8} {'Received':<10} {'Failed':<8} {'Total':<8}\n")
            f.write("-" * 50 + "\n")

            for month in sorted(stats['by_month'].keys()):
                counts = stats['by_month'][month]
                total = sum(counts.values())
                failed = counts['bounced'] + counts['deferred']
                f.write(f"{month:<8} {counts['sent']:<8} {counts['received']:<10} {failed:<8} {total:<8}\n")

            f.write("\n")

            # Key insights
            f.write("🔍 KEY INSIGHTS:\n")
            f.write("-" * 15 + "\n")

            total_sent = stats['by_type']['sent']
            total_received = stats['by_type']['received']
            total_failed = stats['by_type']['bounced'] + stats['by_type']['deferred']

            if total_sent > 0:
                failure_rate = (total_failed / (total_sent + total_failed)) * 100
                f.write(f"  • Email failure rate: {failure_rate:.1f}%\n")

            if stats['date_range']['start'] and stats['date_range']['end']:
                days = (stats['date_range']['end'] - stats['date_range']['start']).days
                if days > 0:
                    avg_sent_per_day = total_sent / days
                    avg_received_per_day = total_received / days
                    f.write(f"  • Average emails sent per day: {avg_sent_per_day:.1f}\n")
                    f.write(f"  • Average emails received per day: {avg_received_per_day:.1f}\n")

            # Gmail specific analysis
            gmail_count = stats['by_domain']['gmail.com']
            if gmail_count > 0:
                gmail_percentage = (gmail_count / total_sent) * 100 if total_sent > 0 else 0
                f.write(f"  • Emails sent to Gmail: {gmail_count:,} ({gmail_percentage:.1f}% of total sent)\n")

            # Top email addresses
            top_senders = sorted([(addr, counts['sent']) for addr, counts in stats['by_address'].items()],
                               key=lambda x: x[1], reverse=True)
            if top_senders:
                f.write(f"  • Most active sending address: {top_senders[0][0]} ({top_senders[0][1]:,} sent)\n")

        print(f"📄 Summary report saved: {filename}")

def main():
    print("🚀 Starting Minipass Email Volume Analysis...")
    print("=" * 50)

    analyzer = EmailVolumeAnalyzer()

    # Analyze all log files
    events = analyzer.analyze_logs()

    if not events:
        print("❌ No email events found in logs!")
        return

    # Generate statistics
    print("\n📊 Generating statistics...")
    stats = analyzer.generate_summary_stats(events)

    # Save reports
    print("\n💾 Saving reports...")
    analyzer.save_csv_report(events)
    analyzer.save_summary_report(stats)

    print("\n✅ Analysis complete!")
    print(f"📧 Total email events analyzed: {len(events):,}")
    if stats['date_range']['start'] and stats['date_range']['end']:
        print(f"📅 Date range: {stats['date_range']['start'].strftime('%Y-%m-%d')} to {stats['date_range']['end'].strftime('%Y-%m-%d')}")

if __name__ == "__main__":
    main()
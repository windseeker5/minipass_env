#!/usr/bin/env python3
"""
DMARC Report Auto-Fetcher
Automatically downloads DMARC reports from mail server via IMAP and analyzes them.

This script connects to the mail.minipass.me server, fetches DMARC reports from
known senders (Google, Outlook, etc.), saves them to disk, and optionally analyzes
them using the existing dmarc_analyzer.py tool.

Usage:
    # Fetch and auto-analyze (default)
    export MAIL_PASSWORD="your_password"
    python scripts/fetch_dmarc_reports.py

    # Fetch with AI-powered analysis
    python scripts/fetch_dmarc_reports.py --ai

    # Download only (skip analysis)
    python scripts/fetch_dmarc_reports.py --no-analyze

    # Fetch from specific mailbox
    python scripts/fetch_dmarc_reports.py --mailbox "DMARC"

Environment Variables:
    MAIL_PASSWORD - Password for kdresdell@minipass.me (required)
    MAIL_SERVER - Mail server hostname (default: mail.minipass.me)
    MAIL_USERNAME - Username for IMAP login (default: kdresdell@minipass.me)
"""

import imaplib
import email
import os
import sys
from datetime import datetime
from pathlib import Path
from email.header import decode_header
import argparse


class DMARCReportFetcher:
    """Fetches DMARC reports from mail server via IMAP."""

    # Known DMARC report senders
    DMARC_SENDERS = [
        "noreply-dmarc-support@google.com",
        "dmarcreport@microsoft.com",
        "noreply@dmarc.yahoo.com",
        "dmarc@messaging.microsoft.com",
        "postmaster@yahoo.com",
        "postmaster@amazonses.com",  # Added missing Amazon SES sender
    ]

    def __init__(
        self,
        mail_server: str = "mail.minipass.me",
        username: str = "kdresdell@minipass.me",
        password: str = None,
        output_dir: str = None
    ):
        """
        Initialize the DMARC report fetcher.

        Args:
            mail_server: IMAP server hostname
            username: Email account username
            password: Email account password
            output_dir: Directory to save downloaded reports
        """
        self.mail_server = mail_server
        self.username = username
        self.password = password or os.getenv("MAIL_PASSWORD")

        if not self.password:
            raise ValueError("Password not provided. Set MAIL_PASSWORD environment variable.")

        # Set output directory to email_monitoring/dmarc_reports by default
        if output_dir is None:
            script_dir = Path(__file__).resolve().parent.parent
            output_dir = script_dir / "email_monitoring" / "dmarc_reports"

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.mail = None
        self.stats = {
            'total_searched': 0,
            'total_found': 0,
            'total_downloaded': 0,
            'errors': 0
        }

    def connect(self):
        """Connect to mail server via IMAP."""
        print(f"🔌 Connecting to {self.mail_server}...")

        try:
            # Try SSL connection first (port 993)
            self.mail = imaplib.IMAP4_SSL(self.mail_server, 993)
            print("   ✓ Connected via SSL (port 993)")
        except Exception as e_ssl:
            try:
                # Fallback to TLS (port 143)
                self.mail = imaplib.IMAP4(self.mail_server, 143)
                self.mail.starttls()
                print("   ✓ Connected via TLS (port 143)")
            except Exception as e_tls:
                raise ConnectionError(
                    f"Failed to connect to mail server:\n"
                    f"  SSL (port 993): {e_ssl}\n"
                    f"  TLS (port 143): {e_tls}"
                )

        # Login
        try:
            self.mail.login(self.username, self.password)
            print(f"   ✓ Logged in as {self.username}\n")
        except Exception as e:
            raise ConnectionError(f"Login failed: {e}")

    def disconnect(self):
        """Disconnect from mail server."""
        if self.mail:
            try:
                self.mail.close()
                self.mail.logout()
            except:
                pass

    def decode_filename(self, filename):
        """Decode email attachment filename."""
        if filename:
            decoded_parts = decode_header(filename)
            decoded_filename = ""
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    decoded_filename += part.decode(encoding or 'utf-8', errors='ignore')
                else:
                    decoded_filename += part
            return decoded_filename
        return None

    def fetch_dmarc_reports(self, mailbox: str = "INBOX", mark_as_read: bool = True, limit: int = None, include_read: bool = False):
        """
        Fetch DMARC reports from specified mailbox.

        Args:
            mailbox: IMAP mailbox to search (default: INBOX)
            mark_as_read: Mark processed emails as read
            limit: Maximum number of reports to download (None = no limit)
            include_read: Include already read emails in search (default: False)

        Returns:
            List of downloaded file paths
        """
        print(f"📬 Searching for DMARC reports in {mailbox}...")

        try:
            status, _ = self.mail.select(mailbox)
            if status != 'OK':
                print(f"   ❌ Could not select mailbox '{mailbox}'")
                return []
        except Exception as e:
            print(f"   ❌ Error selecting mailbox: {e}")
            return []

        downloaded_files = []

        # Search for each known DMARC sender
        for sender in self.DMARC_SENDERS:
            print(f"   🔍 Searching for emails from: {sender}")
            self.stats['total_searched'] += 1

            try:
                # Search for emails from this sender (include read emails if requested)
                search_criteria = f'(FROM "{sender}")'
                if not include_read:
                    search_criteria = f'(FROM "{sender}" UNSEEN)'

                status, data = self.mail.search(None, search_criteria)

                if status != 'OK':
                    print(f"      ⚠️  Search failed for {sender}")
                    continue

                msg_ids = data[0].split()

                if not msg_ids:
                    print(f"      ✓ No new reports from {sender}")
                    continue

                print(f"      ✓ Found {len(msg_ids)} new report(s)")
                self.stats['total_found'] += len(msg_ids)

                # Process each message
                for msg_id in msg_ids:
                    if limit and len(downloaded_files) >= limit:
                        print(f"      ⏹️  Reached download limit ({limit})")
                        break

                    try:
                        files = self._process_message(msg_id, sender, mark_as_read)
                        downloaded_files.extend(files)
                    except Exception as e:
                        print(f"      ❌ Error processing message {msg_id}: {e}")
                        self.stats['errors'] += 1

            except Exception as e:
                print(f"      ❌ Error searching {sender}: {e}")
                self.stats['errors'] += 1
                continue

        return downloaded_files

    def _process_message(self, msg_id, sender: str, mark_as_read: bool):
        """Process a single email message and extract attachments."""
        downloaded_files = []

        try:
            # Fetch the email
            status, msg_data = self.mail.fetch(msg_id, '(RFC822)')
            if status != 'OK':
                return downloaded_files

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Get email date
            email_date = msg.get('Date', 'Unknown')

            # Extract attachments
            attachment_count = 0
            for part in msg.walk():
                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename()

                    if filename:
                        filename = self.decode_filename(filename)

                        # Only process DMARC report files
                        if any(ext in filename.lower() for ext in ['.xml', '.zip', '.gz']):
                            attachment_count += 1

                            # Save attachment
                            filepath = self.output_dir / filename

                            # Check if file already exists
                            if filepath.exists():
                                print(f"         ⏭️  Skipped (already exists): {filename}")
                                continue

                            try:
                                with open(filepath, 'wb') as f:
                                    f.write(part.get_payload(decode=True))

                                print(f"         ✅ Downloaded: {filename}")
                                downloaded_files.append(str(filepath))
                                self.stats['total_downloaded'] += 1
                            except Exception as e:
                                print(f"         ❌ Failed to save {filename}: {e}")
                                self.stats['errors'] += 1

            if attachment_count == 0:
                print(f"         ⚠️  No XML attachments found in message from {sender}")

            # Mark as read if requested
            if mark_as_read and downloaded_files:
                try:
                    self.mail.store(msg_id, '+FLAGS', '\\Seen')
                except:
                    pass  # Ignore errors marking as read

        except Exception as e:
            print(f"         ❌ Error processing message: {e}")
            self.stats['errors'] += 1

        return downloaded_files

    def print_summary(self):
        """Print summary statistics."""
        print("\n" + "=" * 70)
        print("📊 FETCH SUMMARY")
        print("=" * 70)
        print(f"Senders searched:     {self.stats['total_searched']}")
        print(f"Reports found:        {self.stats['total_found']}")
        print(f"Reports downloaded:   {self.stats['total_downloaded']}")
        print(f"Errors:               {self.stats['errors']}")
        print(f"Output directory:     {self.output_dir}")
        print("=" * 70 + "\n")

    def analyze_reports(self, files, use_ai: bool = False):
        """
        Process downloaded reports with dmarc_analyzer.

        Args:
            files: List of file paths to analyze
            use_ai: Enable AI-powered analysis with Google Gemini
        """
        if not files:
            print("⏭️  No reports to analyze\n")
            return

        print("=" * 70)
        print("📊 ANALYZING DMARC REPORTS")
        print("=" * 70)
        print()

        # Import the analyzer
        try:
            # Import from app/tools (where dmarc_analyzer.py lives)
            app_tools_dir = Path(__file__).resolve().parent.parent / "app" / "tools"
            sys.path.insert(0, str(app_tools_dir))
            from dmarc_analyzer import DMARCReportAnalyzer
        except ImportError as e:
            print(f"❌ Could not import dmarc_analyzer: {e}")
            print(f"   Make sure dmarc_analyzer.py exists in app/tools/")
            return

        # Create analyzer
        analyzer = DMARCReportAnalyzer(use_ai=use_ai)

        # Set output directory for analysis reports
        reports_output_dir = Path(__file__).resolve().parent.parent / "email_monitoring" / "reports"

        # Process each file
        for filepath in files:
            try:
                analyzer.process_report_file(filepath, output_dir=str(reports_output_dir))
            except Exception as e:
                print(f"❌ Error analyzing {filepath}: {e}\n")

        print("=" * 70)
        print(f"✅ Analysis complete")
        print(f"📁 Reports saved in: {self.output_dir / 'reports'}/")
        print("=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fetch DMARC reports from mail server and analyze them",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch and auto-analyze (default)
  python scripts/fetch_dmarc_reports.py

  # Fetch with AI-powered analysis
  python scripts/fetch_dmarc_reports.py --ai

  # Download only (skip analysis)
  python scripts/fetch_dmarc_reports.py --no-analyze

  # Fetch from specific mailbox
  python scripts/fetch_dmarc_reports.py --mailbox "DMARC"

Environment Variables:
  MAIL_PASSWORD - Password for mail account (required)
  MAIL_SERVER - Mail server hostname (default: mail.minipass.me)
  MAIL_USERNAME - Username for IMAP (default: kdresdell@minipass.me)
        """
    )

    parser.add_argument(
        '--no-analyze',
        action='store_true',
        help='Download reports only, skip analysis'
    )
    parser.add_argument(
        '--ai',
        action='store_true',
        help='Enable AI-powered analysis with Google Gemini'
    )
    parser.add_argument(
        '--mailbox',
        default='INBOX',
        help='IMAP mailbox to search (default: INBOX)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Maximum number of reports to download'
    )
    parser.add_argument(
        '--no-mark-read',
        action='store_true',
        help='Do not mark emails as read after downloading'
    )
    parser.add_argument(
        '--include-read',
        action='store_true',
        help='Include already read emails in search (useful for recovery)'
    )

    args = parser.parse_args()

    # Print header
    print()
    print("=" * 70)
    print("🔍 DMARC Report Auto-Fetcher")
    print("=" * 70)
    print()

    # Initialize fetcher
    try:
        fetcher = DMARCReportFetcher(
            mail_server=os.getenv("MAIL_SERVER", "mail.minipass.me"),
            username=os.getenv("MAIL_USERNAME", "kdresdell@minipass.me"),
            password=os.getenv("MAIL_PASSWORD")
        )
    except ValueError as e:
        print(f"❌ {e}")
        print("\nSet the password using:")
        print("  export MAIL_PASSWORD='your_password'")
        print()
        sys.exit(1)

    # Connect and fetch
    try:
        fetcher.connect()

        downloaded_files = fetcher.fetch_dmarc_reports(
            mailbox=args.mailbox,
            mark_as_read=not args.no_mark_read,
            limit=args.limit,
            include_read=args.include_read
        )

        fetcher.print_summary()

        # Analyze reports (unless --no-analyze flag)
        if not args.no_analyze:
            fetcher.analyze_reports(downloaded_files, use_ai=args.ai)
        else:
            print("⏭️  Skipping analysis (--no-analyze flag)\n")

        # Disconnect
        fetcher.disconnect()

        # Exit with appropriate code
        if fetcher.stats['errors'] > 0:
            print(f"⚠️  Completed with {fetcher.stats['errors']} error(s)\n")
            sys.exit(2)
        elif fetcher.stats['total_downloaded'] == 0:
            print("ℹ️  No new reports to download\n")
            sys.exit(0)
        else:
            print(f"✅ Successfully downloaded {fetcher.stats['total_downloaded']} report(s)\n")
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        fetcher.disconnect()
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}\n")
        fetcher.disconnect()
        sys.exit(1)


if __name__ == "__main__":
    main()

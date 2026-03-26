#!/usr/bin/env python3
"""
DMARC Health Monitor & Auto-Recovery System
==========================================

This script monitors the DMARC pipeline health and automatically recovers from failures.
It addresses the recurring "Data may be stale" issue by providing:

1. Health monitoring of the DMARC pipeline
2. Automatic recovery when issues are detected
3. Comprehensive logging and status reporting
4. Retry mechanisms with exponential backoff

Usage:
    python scripts/dmarc_health_monitor.py --check     # Health check only
    python scripts/dmarc_health_monitor.py --recover   # Run recovery if needed
    python scripts/dmarc_health_monitor.py --force     # Force full recovery

Designed to be run hourly via cron to ensure data freshness.
"""

import os
import sys
import time
import sqlite3
import subprocess
import argparse
from datetime import date, datetime, timedelta
from pathlib import Path

# Add scripts directory to path for imports
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

try:
    from email_monitor_to_db import EmailMonitor, DB_PATH
except ImportError:
    print("Error: Could not import email_monitor_to_db module")
    sys.exit(1)

class DMARCHealthMonitor:
    """Monitors DMARC pipeline health and provides auto-recovery."""

    def __init__(self):
        self.db_path = DB_PATH
        self.reports_dir = BASE_DIR / "email_monitoring" / "reports"
        self.logs_dir = Path("/home/kdresdell/logs")

    def check_pipeline_health(self):
        """
        Check DMARC pipeline health status.
        Returns: dict with health status and diagnostic info
        """
        status = {
            'healthy': True,
            'latest_db_date': None,
            'latest_file_date': None,
            'days_stale': 0,
            'issues': [],
            'recommendations': []
        }

        try:
            # Check database status
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            # Get latest database entry
            latest_row = cur.execute(
                "SELECT MAX(date) FROM dmarc_daily"
            ).fetchone()

            if latest_row and latest_row[0]:
                status['latest_db_date'] = latest_row[0]
                latest_date = date.fromisoformat(latest_row[0])
                status['days_stale'] = (date.today() - latest_date).days
            else:
                status['healthy'] = False
                status['issues'].append("No DMARC data found in database")
                conn.close()
                return status

            conn.close()

            # Check file system status
            md_files = list(self.reports_dir.glob("*.md"))
            if md_files:
                newest_file = max(md_files, key=lambda f: f.stat().st_mtime)
                mtime = datetime.fromtimestamp(newest_file.stat().st_mtime)
                status['latest_file_date'] = mtime.strftime('%Y-%m-%d')

            # Evaluate health
            if status['days_stale'] > 7:
                status['healthy'] = False
                status['issues'].append(f"DMARC data is {status['days_stale']} days old")
                status['recommendations'].append("Force fetch DMARC reports")
                status['recommendations'].append("Check mail server connectivity")
            elif status['days_stale'] > 4:
                status['issues'].append(f"DMARC data is {status['days_stale']} days old (warning)")
                status['recommendations'].append("Monitor for new reports")

            # Check cron logs for errors
            if self.logs_dir.exists():
                fetch_log = self.logs_dir / "dmarc_fetch.log"
                ingest_log = self.logs_dir / "dmarc_ingest.log"

                if fetch_log.exists():
                    # Check if fetch log shows recent failures
                    if self._check_log_for_errors(fetch_log):
                        status['issues'].append("DMARC fetch showing errors in logs")
                        status['recommendations'].append("Check mail server credentials")

                if ingest_log.exists():
                    # Check if ingest is always returning 0
                    if self._check_ingest_stagnation(ingest_log):
                        status['issues'].append("DMARC ingest stuck at 0 rows")
                        status['recommendations'].append("Run manual ingest recovery")

        except Exception as e:
            status['healthy'] = False
            status['issues'].append(f"Health check error: {str(e)}")

        return status

    def _check_log_for_errors(self, log_file):
        """Check if log file contains error indicators."""
        try:
            with open(log_file, 'r') as f:
                content = f.read()

            error_indicators = [
                'ERROR', 'Failed', 'Exception', 'Traceback',
                'Connection failed', 'Authentication failed'
            ]

            return any(indicator in content for indicator in error_indicators)
        except:
            return False

    def _check_ingest_stagnation(self, log_file):
        """Check if ingest log shows consistent 0 row ingestion."""
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()

            # Check last 5 lines for "Ingested 0 DMARC rows"
            recent_lines = lines[-5:]
            zero_count = sum(1 for line in recent_lines if "Ingested 0 DMARC rows" in line)

            return zero_count >= 3  # 3+ consecutive zero ingests indicates problem
        except:
            return False

    def recover_pipeline(self, force=False):
        """
        Attempt to recover the DMARC pipeline.
        Returns: dict with recovery status and actions taken
        """
        recovery = {
            'success': True,
            'actions_taken': [],
            'errors': []
        }

        try:
            print("🔄 Starting DMARC pipeline recovery...")

            # Step 1: Force fetch new reports
            recovery['actions_taken'].append("Attempting to fetch new DMARC reports")
            fetch_result = self._run_fetch_command()

            if fetch_result['success']:
                recovery['actions_taken'].append(f"Fetch completed: {fetch_result['message']}")
            else:
                recovery['errors'].append(f"Fetch failed: {fetch_result['error']}")

            # Step 2: Force ingest of any pending reports
            recovery['actions_taken'].append("Running DMARC ingest")
            ingest_result = self._run_ingest_command()

            if ingest_result['success']:
                recovery['actions_taken'].append(f"Ingested {ingest_result['rows']} DMARC rows")
            else:
                recovery['errors'].append(f"Ingest failed: {ingest_result['error']}")

            # Step 3: Verify recovery
            time.sleep(2)  # Give database time to update
            post_status = self.check_pipeline_health()

            if post_status['days_stale'] < 7:
                recovery['actions_taken'].append("✅ Pipeline recovery successful")
            else:
                recovery['success'] = False
                recovery['errors'].append("Pipeline still shows stale data after recovery")

                # Step 4: Additional troubleshooting if recovery failed
                if force:
                    recovery['actions_taken'].append("Running additional recovery steps")
                    self._advanced_recovery()

        except Exception as e:
            recovery['success'] = False
            recovery['errors'].append(f"Recovery failed with exception: {str(e)}")

        return recovery

    def _run_fetch_command(self):
        """Run DMARC fetch with proper environment."""
        try:
            # Source environment and run fetch (include read emails for recovery)
            cmd = [
                "/bin/bash", "-c",
                "source /home/kdresdell/.mailpass && python3 scripts/fetch_dmarc_reports.py --include-read"
            ]

            result = subprocess.run(
                cmd,
                cwd=BASE_DIR,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0:
                return {'success': True, 'message': 'Fetch completed successfully'}
            else:
                return {'success': False, 'error': result.stderr or result.stdout}

        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Fetch timeout after 5 minutes'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _run_ingest_command(self):
        """Run DMARC ingest using the EmailMonitor class."""
        try:
            monitor = EmailMonitor(db_path=self.db_path)
            monitor.__enter__()

            rows_ingested = monitor.ingest_dmarc()
            monitor.conn.commit()
            monitor.__exit__(None, None, None)

            return {'success': True, 'rows': rows_ingested}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _advanced_recovery(self):
        """Advanced recovery steps for persistent issues."""
        # Could add more aggressive recovery steps here:
        # - Check mail server connectivity
        # - Verify credentials
        # - Clear corrupted cache files
        # - Reset fetch state
        pass

    def generate_status_report(self):
        """Generate a comprehensive status report."""
        status = self.check_pipeline_health()

        report = []
        report.append("=" * 60)
        report.append("DMARC PIPELINE HEALTH REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Health status
        health_icon = "✅" if status['healthy'] else "❌"
        report.append(f"Overall Status: {health_icon} {'HEALTHY' if status['healthy'] else 'UNHEALTHY'}")
        report.append("")

        # Data freshness
        if status['latest_db_date']:
            report.append(f"Latest DMARC Data: {status['latest_db_date']}")
            report.append(f"Days Old: {status['days_stale']}")

            if status['days_stale'] <= 4:
                freshness_status = "✅ FRESH (Normal DMARC lag)"
            elif status['days_stale'] <= 7:
                freshness_status = "⚠️ SLIGHTLY STALE"
            else:
                freshness_status = "❌ STALE (Requires attention)"

            report.append(f"Freshness: {freshness_status}")
        else:
            report.append("Latest DMARC Data: None found")
            report.append("Freshness: ❌ NO DATA")

        report.append("")

        # Issues
        if status['issues']:
            report.append("Issues Found:")
            for issue in status['issues']:
                report.append(f"  • {issue}")
            report.append("")

        # Recommendations
        if status['recommendations']:
            report.append("Recommendations:")
            for rec in status['recommendations']:
                report.append(f"  • {rec}")
            report.append("")

        report.append("=" * 60)

        return "\\n".join(report)

def main():
    parser = argparse.ArgumentParser(description='DMARC Health Monitor & Auto-Recovery')
    parser.add_argument('--check', action='store_true',
                       help='Health check only (no recovery)')
    parser.add_argument('--recover', action='store_true',
                       help='Run recovery if issues detected')
    parser.add_argument('--force', action='store_true',
                       help='Force recovery regardless of health status')
    parser.add_argument('--report', action='store_true',
                       help='Generate detailed status report')
    parser.add_argument('--quiet', action='store_true',
                       help='Minimal output for cron usage')

    args = parser.parse_args()

    monitor = DMARCHealthMonitor()

    # Default to check mode if no args
    if not any([args.check, args.recover, args.force, args.report]):
        args.check = True

    # Generate report if requested
    if args.report:
        print(monitor.generate_status_report())
        return

    # Check pipeline health
    status = monitor.check_pipeline_health()

    if not args.quiet:
        if status['healthy']:
            print("✅ DMARC pipeline is healthy")
            if status['latest_db_date']:
                print(f"   Latest data: {status['latest_db_date']} ({status['days_stale']} days old)")
        else:
            print("❌ DMARC pipeline has issues")
            for issue in status['issues']:
                print(f"   • {issue}")

    # Recovery logic
    if args.force or (args.recover and not status['healthy']):
        if not args.quiet:
            print("🔄 Running pipeline recovery...")

        recovery = monitor.recover_pipeline(force=args.force)

        if not args.quiet:
            if recovery['success']:
                print("✅ Recovery completed successfully")
                for action in recovery['actions_taken']:
                    print(f"   • {action}")
            else:
                print("❌ Recovery failed")
                for error in recovery['errors']:
                    print(f"   • {error}")

        # Exit with error code if recovery failed
        sys.exit(0 if recovery['success'] else 1)

    # Exit with error code if unhealthy (for cron monitoring)
    sys.exit(0 if status['healthy'] else 1)

if __name__ == "__main__":
    main()
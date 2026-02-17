#!/usr/bin/env python3
"""
Email Monitor to DB
-------------------
Collects email system health metrics and stores them in SQLite.

Usage:
    python scripts/email_monitor_to_db.py              # Parse yesterday
    python scripts/email_monitor_to_db.py --date 2026-02-15  # Specific date
    python scripts/email_monitor_to_db.py --report     # Show 7-day summary

Cron (6 AM daily, after docker-mailserver midnight log rotation):
    0 6 * * * cd /home/kdresdell/minipass_env && source /home/kdresdell/.mailpass && \
      /usr/bin/python3 scripts/email_monitor_to_db.py >> /var/log/email_monitor.log 2>&1
"""

import re
import sys
import sqlite3
import argparse
import subprocess
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR    = Path(__file__).resolve().parent.parent
DB_PATH     = BASE_DIR / "email_monitoring" / "monitoring.db"
REPORTS_DIR = BASE_DIR / "email_monitoring" / "reports"

# ---------------------------------------------------------------------------
# Regex patterns  (reused from email_volume_analysis.py lines 86, 95, 132-138)
# ---------------------------------------------------------------------------
RE_FROM = re.compile(r'from=<([^>]+)>')
RE_TO   = re.compile(r'to=<([^>]+)>')

# DMARC .md parsing patterns
RE_PERIOD = re.compile(r'\*\*Period:\*\* (\d{4}-\d{2}-\d{2})')
RE_TOTAL  = re.compile(r'Total Messages Reported:\*\* (\d+)')
RE_PASSED = re.compile(r'Both DKIM & SPF Passed:\*\* (\d+)')

# ---------------------------------------------------------------------------
# Schema (all CREATE statements are idempotent)
# ---------------------------------------------------------------------------
SCHEMA_STMTS = [
    """CREATE TABLE IF NOT EXISTS email_volume_daily (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        date           TEXT NOT NULL,
        user_email     TEXT NOT NULL,
        sent_count     INTEGER DEFAULT 0,
        bounced_count  INTEGER DEFAULT 0,
        deferred_count INTEGER DEFAULT 0,
        received_count INTEGER DEFAULT 0,
        created_at     TEXT DEFAULT (datetime('now'))
    )""",
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_evd_date_user ON email_volume_daily (date, user_email)",

    """CREATE TABLE IF NOT EXISTS email_failures (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp     TEXT NOT NULL,
        from_user     TEXT,
        to_address    TEXT NOT NULL,
        subject       TEXT,
        error_message TEXT,
        status        TEXT NOT NULL,
        created_at    TEXT DEFAULT (datetime('now'))
    )""",
    "CREATE INDEX IF NOT EXISTS ix_ef_timestamp ON email_failures (timestamp)",

    """CREATE TABLE IF NOT EXISTS mail_queue_log (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp           TEXT NOT NULL,
        queue_size          INTEGER NOT NULL,
        oldest_age_minutes  REAL,
        created_at          TEXT DEFAULT (datetime('now'))
    )""",

    """CREATE TABLE IF NOT EXISTS mailbox_sizes (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        date         TEXT NOT NULL,
        user_email   TEXT NOT NULL,
        size_mb      REAL NOT NULL,
        created_at   TEXT DEFAULT (datetime('now'))
    )""",
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_ms_date_user ON mailbox_sizes (date, user_email)",

    """CREATE TABLE IF NOT EXISTS dmarc_daily (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        date           TEXT NOT NULL,
        reporter       TEXT NOT NULL,
        total_messages INTEGER NOT NULL,
        pass_count     INTEGER NOT NULL,
        fail_count     INTEGER NOT NULL,
        pass_rate      REAL NOT NULL,
        created_at     TEXT DEFAULT (datetime('now'))
    )""",
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_dd_date_reporter ON dmarc_daily (date, reporter)",
]

# Schema migrations - add new columns to existing tables
MIGRATION_STMTS = [
    "ALTER TABLE email_volume_daily ADD COLUMN received_count INTEGER DEFAULT 0",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(cmd: str) -> str | None:
    """Run a shell command, return stdout string or None on error."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            print(f"  [warn] command failed: {cmd!r}")
            if result.stderr.strip():
                print(f"         {result.stderr.strip()[:200]}")
            return None
        return result.stdout
    except subprocess.TimeoutExpired:
        print(f"  [warn] command timed out: {cmd!r}")
        return None


def _parse_size_mb(size_str: str) -> float:
    """Convert du size string (e.g. '1.2M', '500K', '2.1G') to MB."""
    size_str = size_str.strip().upper()
    if size_str.endswith('G'):
        return float(size_str[:-1]) * 1024
    if size_str.endswith('M'):
        return float(size_str[:-1])
    if size_str.endswith('K'):
        return float(size_str[:-1]) / 1024
    # Bare bytes
    return float(size_str) / (1024 * 1024)


def _decode_srs_address(address: str) -> str:
    """
    Decode SRS (Sender Rewriting Scheme) addresses to extract original sender.

    SRS format: SRS0=hash=TT=domain.com=localpart@forwarder.com
    - hash: 4-character hash
    - TT: timestamp (base32)
    - domain.com: original sender domain
    - localpart: original sender local part

    Returns the reconstructed original address, or the input if not SRS.
    """
    if not address.startswith('SRS0='):
        return address

    try:
        # Extract the SRS part before @ symbol
        local_part, domain = address.split('@', 1)

        # Parse SRS0 format: SRS0=hash=TT=original_domain=original_localpart
        parts = local_part.split('=')
        if len(parts) >= 5 and parts[0] == 'SRS0':
            # Reconstruct: original_localpart@original_domain
            original_domain = parts[3]
            original_localpart = '='.join(parts[4:])  # Handle localparts with = in them

            # Clean up the decoded address - some SRS implementations double-encode
            decoded = f"{original_localpart}@{original_domain}"
            # If the decoded address still contains SRS-like patterns, try to clean further
            if '=' in original_localpart and original_domain:
                # Handle nested SRS encoding
                if original_localpart.count('=') >= 3:
                    try:
                        inner_parts = original_localpart.split('=')
                        if len(inner_parts) >= 4:
                            # Extract the actual original parts
                            actual_local = '='.join(inner_parts[3:])
                            decoded = f"{actual_local}@{original_domain}"
                    except:
                        pass

            return decoded
    except (ValueError, IndexError):
        pass

    # If we can't decode it, return as-is but clean it up for display
    return address


def _extract_postfix_timestamp(line: str, target_date: date) -> str:
    """
    Extract a sortable timestamp string from a Postfix syslog line.
    Syslog format: 'Feb 15 06:25:01 ...' -> '2026-02-15 06:25:01'
    ISO format:    '2026-02-15T06:25:01 ...' -> '2026-02-15 06:25:01'
    Returns date-only string as fallback.
    """
    # ISO prefix
    if line[:4].isdigit() and len(line) > 19:
        ts = line[:19].replace('T', ' ')
        return ts

    # Syslog: 'Feb 15 06:25:01' (positions 0-14)
    if len(line) >= 15:
        try:
            time_str = line[7:15].strip()   # 'HH:MM:SS' (may be ' 6:25:01' with leading space)
            # Normalise: strip any leftover spaces
            time_str = time_str.strip()
            return f"{target_date.isoformat()} {time_str}"
        except Exception:
            pass

    return target_date.isoformat()


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class EmailMonitor:
    def __init__(self, db_path: Path = DB_PATH, compose_dir: Path = BASE_DIR):
        self.db_path     = Path(db_path)
        self.compose_dir = Path(compose_dir)
        self.conn: sqlite3.Connection | None = None

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
        return self

    def __exit__(self, *args):
        if self.conn:
            self.conn.commit()
            self.conn.close()

    def _init_schema(self):
        for stmt in SCHEMA_STMTS:
            self.conn.execute(stmt)

        # Apply migrations (these will fail silently if column already exists)
        for stmt in MIGRATION_STMTS:
            try:
                self.conn.execute(stmt)
            except sqlite3.OperationalError:
                pass  # Column likely already exists

        self.conn.commit()

    # ------------------------------------------------------------------
    # 1. Postfix log parsing
    # ------------------------------------------------------------------

    def collect_postfix_logs(self) -> str:
        """Fetch the live mail.log from the running mailserver container."""
        out = _run("docker exec mailserver cat /var/log/mail/mail.log")
        if out is None:
            print("  [warn] could not read mail log — Postfix section skipped")
            return ""
        return out

    def parse_day(self, content: str, target_date: date):
        """
        Filter log content to target_date and parse sent/bounced/deferred.

        Postfix logs from=<> on a qmgr line tied to a queue ID, while
        status=sent/bounced/deferred appear on smtp/lmtp lines with the same
        queue ID but no from=.  We do two passes:
          Pass 1 — build {queue_id: sender} from any line containing from=<>
          Pass 2 — resolve sender via queue ID when processing delivery lines

        Supported log date formats:
          ISO:    '2026-02-15T06:25:01.123456+00:00 mail postfix/...'
          Syslog: 'Feb 15 06:25:01 mail postfix/...'

        Returns:
            aggregates: {user_email: {'sent': n, 'bounced': n, 'deferred': n, 'received': n}}
            failures:   [{'timestamp', 'from_user', 'to_address', 'error_message', 'status'}, ...]
        """
        # Build both filter prefixes
        iso_prefix     = target_date.isoformat()          # '2026-02-15'
        month_abbr     = target_date.strftime("%b")        # 'Feb'
        day_padded     = str(target_date.day).rjust(2)    # '15' or ' 5'
        syslog_prefix  = f"{month_abbr} {day_padded}"     # 'Feb 15'

        # Queue ID pattern: appears as ']: QUEUEID:' in every Postfix log line
        # Classic IDs: uppercase hex ~11 chars; long IDs: alphanumeric ~18 chars
        RE_QUEUE_ID = re.compile(r'postfix/\w+\[\d+\]: ([A-Za-z0-9]{8,}):')

        # --- Pass 1: build queue_id -> sender_email map ---
        queue_sender: dict[str, str] = {}
        for line in content.splitlines():
            if not (line.startswith(iso_prefix) or line.startswith(syslog_prefix)):
                continue
            if 'from=<' not in line:
                continue
            qid_m  = RE_QUEUE_ID.search(line)
            from_m = RE_FROM.search(line)
            if qid_m and from_m:
                qid    = qid_m.group(1)
                sender = from_m.group(1) or '<>'   # empty = null sender (DSN/bounce)
                sender = _decode_srs_address(sender)  # Decode SRS addresses
                queue_sender.setdefault(qid, sender)   # first seen wins

        # --- Pass 2: aggregate delivery statuses ---
        aggregates: dict = defaultdict(lambda: {'sent': 0, 'bounced': 0, 'deferred': 0, 'received': 0})
        failures: list   = []

        for line in content.splitlines():
            # Fast date filter
            if not (line.startswith(iso_prefix) or line.startswith(syslog_prefix)):
                continue
            if 'status=' not in line:
                continue

            to_m  = RE_TO.search(line)
            qid_m = RE_QUEUE_ID.search(line)

            # Prefer queue-ID lookup; fall back to inline from= on same line
            from_email = None
            if qid_m:
                from_email = queue_sender.get(qid_m.group(1))
            if not from_email:
                from_m     = RE_FROM.search(line)
                from_email = (from_m.group(1) if from_m else None) or 'unknown'

            # Apply SRS decoding to the final from_email
            if from_email and from_email != 'unknown':
                from_email = _decode_srs_address(from_email)

            if 'status=sent' in line:
                aggregates[from_email]['sent'] += 1

            elif 'status=bounced' in line:
                aggregates[from_email]['bounced'] += 1
                status_idx = line.find('status=')
                failures.append({
                    'timestamp':     _extract_postfix_timestamp(line, target_date),
                    'from_user':     from_email,
                    'to_address':    to_m.group(1) if to_m else 'unknown',
                    'subject':       None,
                    'error_message': line[status_idx:status_idx + 500] if status_idx >= 0 else line[-500:],
                    'status':        'bounced',
                })

            elif 'status=deferred' in line:
                aggregates[from_email]['deferred'] += 1
                status_idx = line.find('status=')
                failures.append({
                    'timestamp':     _extract_postfix_timestamp(line, target_date),
                    'from_user':     from_email,
                    'to_address':    to_m.group(1) if to_m else 'unknown',
                    'subject':       None,
                    'error_message': line[status_idx:status_idx + 500] if status_idx >= 0 else line[-500:],
                    'status':        'deferred',
                })

        # --- Pass 3: aggregate received emails (LMTP deliveries to local mailboxes) ---
        for line in content.splitlines():
            # Fast date filter
            if not (line.startswith(iso_prefix) or line.startswith(syslog_prefix)):
                continue

            # Look for LMTP deliveries to local mailboxes: postfix/lmtp[...]: ... to=<user@minipass.me> ... status=sent
            if 'postfix/lmtp[' not in line or 'status=sent' not in line or '@minipass.me>' not in line:
                continue

            to_m = RE_TO.search(line)
            if to_m:
                recipient = to_m.group(1)
                # Only count deliveries to our domain
                if recipient.endswith('@minipass.me'):
                    aggregates[recipient]['received'] += 1

        return aggregates, failures

    def store_volume(self, target_date: date, aggregates: dict) -> int:
        date_str = target_date.isoformat()
        count = 0
        for user_email, counts in aggregates.items():
            self.conn.execute("""
                INSERT OR REPLACE INTO email_volume_daily
                    (date, user_email, sent_count, bounced_count, deferred_count, received_count)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (date_str, user_email, counts['sent'], counts['bounced'], counts['deferred'], counts['received']))
            count += 1
        return count

    def store_failures(self, failures: list) -> int:
        count = 0
        for f in failures:
            self.conn.execute("""
                INSERT INTO email_failures
                    (timestamp, from_user, to_address, subject, error_message, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (f['timestamp'], f['from_user'], f['to_address'],
                  f['subject'], f['error_message'], f['status']))
            count += 1
        return count

    # ------------------------------------------------------------------
    # 2. Mail queue snapshot
    # ------------------------------------------------------------------

    def check_queue(self) -> tuple[int, float | None]:
        """
        Run postqueue -p inside mailserver container.
        Returns (queue_size, oldest_age_minutes).
        oldest_age_minutes is None when queue is empty or can't be parsed.
        """
        out = _run("docker exec mailserver postqueue -p")
        if out is None:
            return 0, None

        if 'Mail queue is empty' in out:
            return 0, None

        # Each queued message block starts with a queue ID (alphanumeric, ≥ 10 chars)
        # followed by size and an RFC 2822-style date.
        # Example line:
        #   3F8A81234AB*    1024 Mon Feb 10 06:02:09  sender@example.com
        queue_id_re = re.compile(r'^[0-9A-F]{10,}[*!]?\s+\d+\s+(\w{3} \w{3}\s+\d+ \d+:\d+:\d+)',
                                 re.IGNORECASE)
        now_dt     = datetime.now()
        queue_size = 0
        oldest_dt  = None

        for line in out.splitlines():
            m = queue_id_re.match(line)
            if not m:
                continue
            queue_size += 1
            # Parse arrival timestamp: 'Mon Feb 10 06:02:09' (no year!)
            try:
                arrival = datetime.strptime(
                    f"{m.group(1).strip()} {now_dt.year}",
                    "%a %b %d %H:%M:%S %Y"
                )
                # If parsed date is in the future (year wrap), subtract a year
                if arrival > now_dt:
                    arrival = arrival.replace(year=arrival.year - 1)
                if oldest_dt is None or arrival < oldest_dt:
                    oldest_dt = arrival
            except ValueError:
                pass

        oldest_age = None
        if oldest_dt is not None:
            oldest_age = (now_dt - oldest_dt).total_seconds() / 60

        return queue_size, oldest_age

    def store_queue(self, queue_size: int, oldest_age: float | None):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.conn.execute("""
            INSERT INTO mail_queue_log (timestamp, queue_size, oldest_age_minutes)
            VALUES (?, ?, ?)
        """, (ts, queue_size, oldest_age))

    # ------------------------------------------------------------------
    # 3. Mailbox sizes
    # ------------------------------------------------------------------

    def check_mailboxes(self) -> list[tuple[str, float]]:
        """
        Return [(user_email, size_mb), ...] from du inside mailserver.
        Maildir root is /var/mail/minipass.me/<user>/
        """
        # Use sh -c so the glob expands inside the container, not on the host
        out = _run("docker exec mailserver sh -c 'du -sh /var/mail/minipass.me/*/'")
        if out is None:
            # Fallback: try without trailing slash in case some distros need it
            out = _run("docker exec mailserver sh -c 'du -sh /var/mail/minipass.me/*'")
        if out is None:
            return []

        results = []
        for line in out.strip().splitlines():
            parts = line.split(None, 1)   # split on first whitespace
            if len(parts) < 2:
                continue
            size_str, path = parts
            try:
                user      = path.rstrip('/').split('/')[-1]
                size_mb   = _parse_size_mb(size_str)
                results.append((f"{user}@minipass.me", size_mb))
            except (ValueError, IndexError):
                continue
        return results

    def store_mailboxes(self, target_date: date, mailboxes: list) -> int:
        date_str = target_date.isoformat()
        count = 0
        for user_email, size_mb in mailboxes:
            self.conn.execute("""
                INSERT OR REPLACE INTO mailbox_sizes (date, user_email, size_mb)
                VALUES (?, ?, ?)
            """, (date_str, user_email, size_mb))
            count += 1
        return count

    # ------------------------------------------------------------------
    # 4. DMARC .md ingestion
    # ------------------------------------------------------------------

    def ingest_dmarc(self) -> int:
        """
        Parse all .md files in REPORTS_DIR.
        Reporter is extracted from the filename (e.g. 'google.com' from
        'google.com!minipass.me!…_report.md') — authoritative and consistent.
        Skip (date, reporter) pairs already in the DB.
        """
        md_files = sorted(REPORTS_DIR.glob("*.md"))
        new_rows = 0

        for md_path in md_files:
            # Reporter = everything before the first '!'
            reporter = md_path.name.split('!')[0]

            content = md_path.read_text(errors='replace')

            period_m = RE_PERIOD.search(content)
            if not period_m:
                continue
            report_date = period_m.group(1)

            # Idempotent: skip already-ingested pairs
            exists = self.conn.execute(
                "SELECT 1 FROM dmarc_daily WHERE date=? AND reporter=?",
                (report_date, reporter)
            ).fetchone()
            if exists:
                continue

            total_m  = RE_TOTAL.search(content)
            passed_m = RE_PASSED.search(content)
            if not total_m:
                continue

            total     = int(total_m.group(1))
            passed    = int(passed_m.group(1)) if passed_m else 0
            failed    = total - passed
            pass_rate = round(passed / total * 100, 2) if total > 0 else 0.0

            self.conn.execute("""
                INSERT OR REPLACE INTO dmarc_daily
                    (date, reporter, total_messages, pass_count, fail_count, pass_rate)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (report_date, reporter, total, passed, failed, pass_rate))
            new_rows += 1

        return new_rows

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------

    def run(self, target_date: date):
        print(f"Email Monitor — {target_date}")
        print("=" * 50)

        # 1. Postfix logs
        print("\n[1/4] Parsing Postfix logs...")
        log_content = self.collect_postfix_logs()
        aggregates, failures = self.parse_day(log_content, target_date)
        vol_count  = self.store_volume(target_date, aggregates)
        fail_count = self.store_failures(failures)
        total_sent     = sum(v['sent']     for v in aggregates.values())
        total_bounced  = sum(v['bounced']  for v in aggregates.values())
        total_deferred = sum(v['deferred'] for v in aggregates.values())
        total_received = sum(v['received'] for v in aggregates.values())
        print(f"  Unique users   : {vol_count}")
        print(f"  Sent           : {total_sent}")
        print(f"  Received       : {total_received}")
        print(f"  Bounced        : {total_bounced}")
        print(f"  Deferred       : {total_deferred}")
        print(f"  Failures stored: {fail_count}")

        # 2. Mail queue
        print("\n[2/4] Checking mail queue...")
        queue_size, oldest_age = self.check_queue()
        self.store_queue(queue_size, oldest_age)
        age_str = f"{oldest_age:.1f} min" if oldest_age is not None else "n/a"
        print(f"  Queue size: {queue_size}, Oldest: {age_str}")
        if queue_size > 10:
            print(f"  [ALERT] Queue has {queue_size} messages — investigate!")

        # 3. Mailbox sizes
        print("\n[3/4] Checking mailbox sizes...")
        mailboxes = self.check_mailboxes()
        mb_count  = self.store_mailboxes(target_date, mailboxes)
        if mailboxes:
            for user, size_mb in mailboxes:
                print(f"  {user}: {size_mb:.1f} MB")
        else:
            print("  No mailboxes found (or docker unavailable)")

        # 4. DMARC
        print("\n[4/4] Ingesting DMARC reports...")
        dmarc_count = self.ingest_dmarc()
        print(f"  New DMARC rows ingested: {dmarc_count}")

        self.conn.commit()
        print("\nDone.")

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------

    def report(self, days: int = 7):
        since = (date.today() - timedelta(days=days)).isoformat()

        print(f"\nEmail Monitor — Last {days} days (since {since})")
        print("=" * 60)

        # Volume summary
        print("\n## Email Volume (per user)")
        rows = self.conn.execute("""
            SELECT date, user_email, sent_count, bounced_count, deferred_count, received_count
            FROM email_volume_daily
            WHERE date >= ?
            ORDER BY date DESC, COALESCE(sent_count, 0) + COALESCE(received_count, 0) DESC
        """, (since,)).fetchall()
        if rows:
            print(f"  {'Date':<12} {'User':<35} {'Sent':>5} {'Rcvd':>5} {'Bnc':>5} {'Def':>5}")
            print(f"  {'-'*12} {'-'*35} {'-'*5} {'-'*5} {'-'*5} {'-'*5}")
            for r in rows:
                rcvd_count = r['received_count'] if r['received_count'] is not None else 0
                print(f"  {r['date']:<12} {r['user_email']:<35} "
                      f"{r['sent_count']:>5} {rcvd_count:>5} {r['bounced_count']:>5} {r['deferred_count']:>5}")
        else:
            print("  No data")

        # Failures
        print("\n## Recent Failures (last 5)")
        rows = self.conn.execute("""
            SELECT timestamp, from_user, to_address, status
            FROM email_failures
            ORDER BY timestamp DESC
            LIMIT 5
        """).fetchall()
        if rows:
            for r in rows:
                print(f"  [{r['status'].upper():<8}] {r['timestamp']}  "
                      f"{r['from_user']} -> {r['to_address']}")
        else:
            print("  No failures recorded")

        # Queue history
        print("\n## Mail Queue Snapshots (last 5)")
        rows = self.conn.execute("""
            SELECT timestamp, queue_size, oldest_age_minutes
            FROM mail_queue_log
            ORDER BY timestamp DESC
            LIMIT 5
        """).fetchall()
        if rows:
            for r in rows:
                age = f"{r['oldest_age_minutes']:.1f} min" if r['oldest_age_minutes'] else "empty"
                print(f"  {r['timestamp']}  size={r['queue_size']}  oldest={age}")
        else:
            print("  No queue snapshots")

        # Mailbox sizes
        print("\n## Mailbox Sizes (latest)")
        rows = self.conn.execute("""
            SELECT ms.date, ms.user_email, ms.size_mb
            FROM mailbox_sizes ms
            INNER JOIN (
                SELECT user_email, MAX(date) AS max_date
                FROM mailbox_sizes
                GROUP BY user_email
            ) latest ON ms.user_email = latest.user_email AND ms.date = latest.max_date
            ORDER BY ms.size_mb DESC
        """).fetchall()
        if rows:
            for r in rows:
                print(f"  {r['user_email']:<35} {r['size_mb']:>8.1f} MB  (as of {r['date']})")
        else:
            print("  No mailbox data")

        # DMARC
        print("\n## DMARC (last 7 days)")
        rows = self.conn.execute("""
            SELECT date, reporter, total_messages, pass_count, fail_count, pass_rate
            FROM dmarc_daily
            WHERE date >= ?
            ORDER BY date DESC, reporter
        """, (since,)).fetchall()
        if rows:
            print(f"  {'Date':<12} {'Reporter':<40} {'Total':>6} {'Pass':>5} {'Fail':>5} {'Rate':>7}")
            print(f"  {'-'*12} {'-'*40} {'-'*6} {'-'*5} {'-'*5} {'-'*7}")
            for r in rows:
                rate_str = f"{r['pass_rate']:.1f}%"
                print(f"  {r['date']:<12} {r['reporter']:<40} "
                      f"{r['total_messages']:>6} {r['pass_count']:>5} {r['fail_count']:>5} {rate_str:>7}")
        else:
            print("  No DMARC data")

        print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Email monitoring — aggregate stats to SQLite"
    )
    parser.add_argument(
        "--date",
        help="Target date YYYY-MM-DD (default: yesterday)",
        default=None,
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Print 7-day summary from DB and exit",
    )
    parser.add_argument(
        "--db",
        help=f"Override DB path (default: {DB_PATH})",
        default=str(DB_PATH),
    )
    args = parser.parse_args()

    db_path = Path(args.db)

    with EmailMonitor(db_path=db_path) as monitor:
        if args.report:
            monitor.report()
            return

        if args.date:
            try:
                target_date = date.fromisoformat(args.date)
            except ValueError:
                print(f"[error] Invalid date format: {args.date!r}  (expected YYYY-MM-DD)")
                sys.exit(1)
        else:
            target_date = date.today() - timedelta(days=1)

        monitor.run(target_date)


if __name__ == "__main__":
    main()

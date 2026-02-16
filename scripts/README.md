# Email Monitoring Scripts

This directory contains automated scripts for email system monitoring, DMARC compliance checking, and health checks.

## Scripts Overview

### 1. `fetch_dmarc_reports.py` — DMARC Report Auto-Fetcher

**Purpose:** Automatically downloads DMARC reports from mailbox and analyzes them.

**What it does:**
- Connects to `mail.minipass.me` via IMAP (SSL/TLS)
- Searches for DMARC reports from Google, Outlook, Yahoo, and other providers
- Downloads XML report attachments to `app/tools/` directory
- Optionally analyzes reports with `dmarc_analyzer.py` (default: enabled)
- Generates Markdown reports with authentication statistics
- Marks processed emails as read (optional)

**Prerequisites:**
```bash
# Required environment variable
export MAIL_PASSWORD="your_password_here"

# Optional: for AI-powered analysis
pip install google-generativeai python-dotenv
export GEMINI_API_KEY="your_api_key"
```

**Usage:**

```bash
# Fetch and auto-analyze (recommended)
python scripts/fetch_dmarc_reports.py

# Fetch with AI-powered recommendations
python scripts/fetch_dmarc_reports.py --ai

# Download only (skip analysis)
python scripts/fetch_dmarc_reports.py --no-analyze

# Fetch from specific mailbox
python scripts/fetch_dmarc_reports.py --mailbox "DMARC"

# Limit downloads (useful for testing)
python scripts/fetch_dmarc_reports.py --limit 5

# Don't mark emails as read
python scripts/fetch_dmarc_reports.py --no-mark-read
```

**Automated Execution:**

Add to crontab for daily monitoring:
```bash
# Run daily at 10 AM
0 10 * * * cd /path/to/minipass_env && /path/to/venv/bin/python scripts/fetch_dmarc_reports.py >> /var/log/dmarc_fetch.log 2>&1
```

**Output:**
- Downloaded reports: `app/tools/*.xml.gz` or `*.zip`
- Analysis reports: `app/tools/reports/*_report.md`
- Console output shows:
  - Connection status
  - Number of reports found per sender
  - Download progress
  - Analysis summary (pass rates, authentication results)

**Exit Codes:**
- `0` - Success (reports downloaded)
- `1` - Fatal error (connection failure, import error)
- `2` - Completed with errors (some downloads failed)
- `130` - Interrupted by user (Ctrl+C)

---

### 2. `email_health_check.py` — Email Delivery Health Monitor

**Purpose:** Monitors email delivery success rates for the customer application.

**What it does:**
- Queries SQLite `email_log` table for last 24 hours
- Calculates overall success rate
- Tracks Gmail-specific failures
- Alerts if success rate < 95% or Gmail failures > 5

**Usage:**
```bash
python scripts/email_health_check.py
```

**Expected Output:**
```
📧 Email Delivery Health Check (Last 24 hours)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total emails sent: 150
Successful deliveries: 148 (98.7%)
Failed deliveries: 2 (1.3%)

Gmail deliveries: 75
Gmail failures: 1 (1.3%)

✅ Email system is healthy
```

**Automated Execution:**
```bash
# Run daily at 9 AM
0 9 * * * cd /path/to/minipass_env && /path/to/venv/bin/python scripts/email_health_check.py
```

---

### 3. `verify_email_rfc_compliance.sh` — RFC 5322 Compliance Checker

**Purpose:** Verifies email system compliance with RFC 5322 standards.

**What it checks:**
- DNS records (SPF, DKIM, DMARC)
- Mail server configuration
- Header formatting
- Authentication mechanisms

**Usage:**
```bash
./scripts/verify_email_rfc_compliance.sh
```

**Expected Output:**
- ✅ Pass: RFC 5322 compliant
- ❌ Fail: Non-compliant (with specific issues)

**When to run:**
- After mail server configuration changes
- Before deploying to production
- After DNS record updates

---

## Email Monitoring Ecosystem

These scripts work together to provide comprehensive email system monitoring:

```
┌─────────────────────────────────────────────────────────────┐
│  Email Monitoring & Compliance Stack                        │
└─────────────────────────────────────────────────────────────┘

1. RFC Compliance (Pre-deployment)
   └─> verify_email_rfc_compliance.sh
       ├─ Checks SPF, DKIM, DMARC DNS
       └─ Verifies mail server config

2. DMARC Monitoring (Daily)
   └─> fetch_dmarc_reports.py (automated)
       ├─ Downloads reports from mailbox
       └─> app/tools/dmarc_analyzer.py
           └─ Generates analysis reports

3. Delivery Health (Daily)
   └─> email_health_check.py
       ├─ Queries customer app database
       └─ Alerts on low success rates

4. Volume Analysis (Manual)
   └─> ../email_volume_analysis.py
       ├─ Analyzes docker-mailserver logs
       └─ Generates CSV/text reports

5. Real-Time Monitoring (On-demand)
   └─> ../monitor_email_delivery.py
       └─ Checks mail queue and logs
```

---

## Troubleshooting

### DMARC Fetcher Issues

**Problem:** `ValueError: Password not provided`
```bash
# Solution: Set environment variable
export MAIL_PASSWORD="your_password"
```

**Problem:** `ConnectionError: Failed to connect to mail server`
```bash
# Check mail server is running
docker ps | grep mailserver

# Check firewall allows IMAP (port 993 or 143)
sudo ufw status

# Test IMAP connection manually
telnet mail.minipass.me 993
```

**Problem:** `ImportError: No module named 'dmarc_analyzer'`
```bash
# Check file exists
ls -la app/tools/dmarc_analyzer.py

# Verify Python path
python -c "import sys; print(sys.path)"
```

**Problem:** No reports found (0 downloaded)
- Check mailbox has new DMARC reports
- Verify sender addresses are in `DMARC_SENDERS` list
- Try `--no-mark-read` flag to re-download previously read emails
- Check mailbox name (default is `INBOX`)

### Email Health Check Issues

**Problem:** `sqlite3.OperationalError: no such table: email_log`
```bash
# Check database exists
ls -la app/instance/minipass.db

# Verify schema
sqlite3 app/instance/minipass.db ".schema email_log"
```

---

## Security Notes

### Password Storage

**DO NOT hardcode passwords in scripts!**

✅ **Recommended:**
```bash
# Store in environment variable
export MAIL_PASSWORD="your_password"

# Or use .env file (never commit to git)
echo "MAIL_PASSWORD=your_password" >> .env
```

❌ **NEVER do this:**
```python
password = "my_password_123"  # WRONG!
```

### Cron Job Security

When setting up cron jobs, ensure:
1. Password is stored in secure location (e.g., `/root/.mailpass`)
2. File permissions restrict access: `chmod 600 /root/.mailpass`
3. Load password in cron script:
   ```bash
   source /root/.mailpass
   python scripts/fetch_dmarc_reports.py
   ```

---

## Adding New DMARC Senders

If you receive reports from additional providers:

1. Edit `scripts/fetch_dmarc_reports.py`
2. Add sender to `DMARC_SENDERS` list:
   ```python
   DMARC_SENDERS = [
       "noreply-dmarc-support@google.com",
       "dmarcreport@microsoft.com",
       "new_sender@example.com",  # Add here
   ]
   ```
3. Test: `python scripts/fetch_dmarc_reports.py --limit 1`

---

## Related Tools

### DMARC Analyzer (Core Tool)
**Location:** `app/tools/dmarc_analyzer.py`

**Direct usage:**
```bash
cd app/tools
python dmarc_analyzer.py
```

This processes all `.xml.gz`, `.zip`, and `.xml` files in `app/tools/` directory.

### Mail Management
**Location:** `mail_manager.py` (root directory)

Interactive mail server management and diagnostics.

### Volume Analysis
**Location:** `email_volume_analysis.py` (root directory)

Analyzes 8-12 months of email logs for volume trends.

---

## Support

For issues or questions:
- Check logs in `/var/log/` or script output
- Review DMARC reports in `app/tools/reports/`
- Consult main project documentation in `CLAUDE.md`
- Check email system documentation in `docs/EMAIL_TEMPLATE_SYSTEM.md`

---

## Future Enhancements (Deferred to Week 2-3)

### Mailbox Size Analytics (Planned)
**File:** `scripts/mailbox_analytics.py` (not yet implemented)

Will provide:
- Disk usage per user
- Email counts per mailbox
- Storage trends over time
- SQLite database for historical tracking

**Planned features:**
- Weekly automated reports
- Alert on mailbox quota approaching limits
- Integration with monitoring dashboard

**Target implementation:** Week 2-3 after Phase 1 stabilizes

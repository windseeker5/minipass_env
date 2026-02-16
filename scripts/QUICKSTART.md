# DMARC Auto-Fetcher Quick Start Guide

## 🚀 First Time Setup (5 minutes)

### Step 1: Set Your Password

**Option A: Environment Variable (Temporary - for testing)**
```bash
export MAIL_PASSWORD="your_actual_password"
```

**Option B: Update .env File (Persistent - recommended)**
```bash
# Edit the .env file in project root
nano .env

# Update this line:
MAIL_PASSWORD=your_actual_password

# Save and close (Ctrl+X, Y, Enter)
```

**Option C: Secure Password File (Production - most secure)**
```bash
# Create secure password file
echo "export MAIL_PASSWORD='your_actual_password'" > ~/.mailpass
chmod 600 ~/.mailpass

# Load password when needed
source ~/.mailpass
python scripts/fetch_dmarc_reports.py
```

### Step 2: Test the Script

**Dry run (check help):**
```bash
python scripts/fetch_dmarc_reports.py --help
```

**First fetch (download and analyze):**
```bash
# Make sure password is set
source .env  # Or: export MAIL_PASSWORD="..."

# Run fetcher
python scripts/fetch_dmarc_reports.py
```

**Expected output:**
```
======================================================================
🔍 DMARC Report Auto-Fetcher
======================================================================

🔌 Connecting to mail.minipass.me...
   ✓ Connected via SSL (port 993)
   ✓ Logged in as kdresdell@minipass.me

📬 Searching for DMARC reports in INBOX...
   🔍 Searching for emails from: noreply-dmarc-support@google.com
      ✓ Found 2 new report(s)
         ✅ Downloaded: google.com!minipass.me!1760400000!1760486399.zip
         ✅ Downloaded: google.com!minipass.me!1760486400!1760572799.zip
   🔍 Searching for emails from: dmarcreport@microsoft.com
      ✓ No new reports from dmarcreport@microsoft.com
   ...

======================================================================
📊 FETCH SUMMARY
======================================================================
Senders searched:     5
Reports found:        2
Reports downloaded:   2
Errors:               0
Output directory:     /path/to/minipass_env/app/tools
======================================================================

======================================================================
📊 ANALYZING DMARC REPORTS
======================================================================

📧 Processing: google.com!minipass.me!1760400000!1760486399.zip
   ✅ Report saved: /path/to/minipass_env/app/tools/reports/google.com!minipass.me!1760400000!1760486399_report.md
   ✅ All 150 messages passed authentication!

📧 Processing: google.com!minipass.me!1760486400!1760572799.zip
   ✅ Report saved: /path/to/minipass_env/app/tools/reports/google.com!minipass.me!1760486400!1760572799_report.md
   ⚠️  125 messages: 96.8% passed both checks

======================================================================
✅ Analysis complete
📁 Reports saved in: /path/to/minipass_env/app/tools/reports/
======================================================================

✅ Successfully downloaded 2 report(s)
```

### Step 3: Review the Reports

```bash
# List downloaded reports
ls -lh app/tools/*.{xml,zip,gz}

# List analysis reports
ls -lh app/tools/reports/*.md

# Read latest report
cat app/tools/reports/*.md | less
```

---

## 🧪 Testing Scenarios

### Test 1: Download Only (No Analysis)
```bash
python scripts/fetch_dmarc_reports.py --no-analyze
```
**Use case:** Just fetch reports for backup, analyze later

### Test 2: Limited Download
```bash
python scripts/fetch_dmarc_reports.py --limit 1
```
**Use case:** Test connection, download only 1 report

### Test 3: Don't Mark as Read
```bash
python scripts/fetch_dmarc_reports.py --no-mark-read
```
**Use case:** Re-download previously processed reports for testing

### Test 4: AI-Powered Analysis (If Gemini API Key Set)
```bash
# Set API key first
export GEMINI_API_KEY="your_gemini_api_key"

# Run with AI
python scripts/fetch_dmarc_reports.py --ai
```
**Use case:** Get AI-powered recommendations for improving email deliverability

### Test 5: Custom Mailbox
```bash
python scripts/fetch_dmarc_reports.py --mailbox "DMARC-Reports"
```
**Use case:** Fetch from specific folder if you filter DMARC emails

---

## 📅 Automated Daily Execution

### Setup Cron Job (Recommended)

**Step 1: Create wrapper script**
```bash
cat > ~/dmarc_fetch.sh << 'EOF'
#!/bin/bash
# DMARC Report Fetcher - Daily Automation

# Set working directory
cd /home/kdresdell/Documents/DEV/minipass_env || exit 1

# Load password securely
source ~/.mailpass 2>/dev/null || {
    echo "ERROR: ~/.mailpass not found"
    exit 1
}

# Run fetcher
/home/kdresdell/Documents/DEV/minipass_env/venv/bin/python \
    scripts/fetch_dmarc_reports.py

# Exit with script's exit code
exit $?
EOF

chmod +x ~/dmarc_fetch.sh
```

**Step 2: Add to crontab**
```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 10 AM)
0 10 * * * /home/kdresdell/dmarc_fetch.sh >> /var/log/dmarc_fetch.log 2>&1
```

**Step 3: Test cron job**
```bash
# Run manually
~/dmarc_fetch.sh

# Check logs
tail -f /var/log/dmarc_fetch.log
```

---

## 🔍 Troubleshooting

### Issue: "Password not provided"
```bash
# Solution 1: Check environment variable
echo $MAIL_PASSWORD

# Solution 2: Load from .env
source .env
python scripts/fetch_dmarc_reports.py
```

### Issue: "Connection refused" or "Connection timeout"
```bash
# Check mail server is running
docker ps | grep mailserver

# Test IMAP connection
telnet mail.minipass.me 993

# Check firewall
sudo ufw status | grep 993
```

### Issue: "Login failed: authentication failed"
```bash
# Verify password is correct
# Try logging in manually with webmail or Thunderbird

# Check username format
echo $MAIL_USERNAME  # Should be: kdresdell@minipass.me
```

### Issue: "No new reports to download"
This is normal! It means:
- No DMARC reports have arrived since last run
- All reports were already downloaded
- Reports were marked as read

**To re-download old reports:**
```bash
python scripts/fetch_dmarc_reports.py --no-mark-read
```

### Issue: Import error for dmarc_analyzer
```bash
# Check file exists
ls -la app/tools/dmarc_analyzer.py

# Verify Python can find it
python -c "import sys; sys.path.insert(0, 'app/tools'); from dmarc_analyzer import DMARCReportAnalyzer"
```

---

## 📊 Understanding DMARC Reports

### What to Look For

**✅ Good Report (100% pass rate):**
```markdown
📊 Total Messages Reported: 150
✅ DKIM Authentication: 150 (100.0%)
✅ SPF Authentication: 150 (100.0%)
✅ Both DKIM & SPF Passed: 150 (100.0%)
```
**Action:** None needed. Email system is working perfectly.

**⚠️ Warning Report (90-99% pass rate):**
```markdown
📊 Total Messages Reported: 125
⚠️ DKIM Authentication: 120 (96.0%)
✅ SPF Authentication: 125 (100.0%)
⚠️ Both DKIM & SPF Passed: 120 (96.0%)
```
**Action:** Investigate failed DKIM signatures. Check DKIM selector and DNS records.

**❌ Critical Report (<90% pass rate):**
```markdown
📊 Total Messages Reported: 200
❌ DKIM Authentication: 150 (75.0%)
❌ SPF Authentication: 160 (80.0%)
❌ Both DKIM & SPF Passed: 140 (70.0%)
```
**Action:** URGENT - Email deliverability is impacted. Review:
1. DNS records (SPF, DKIM, DMARC)
2. Mail server configuration
3. DKIM signing setup
4. Source IP reputation

### Common Issues in Reports

**Issue 1: DKIM Failed**
- **Cause:** DKIM signature invalid or missing
- **Fix:** Check `scripts/verify_email_rfc_compliance.sh` output
- **Command:** `./scripts/verify_email_rfc_compliance.sh`

**Issue 2: SPF Failed**
- **Cause:** Email sent from unauthorized IP
- **Fix:** Add IP to SPF record in DNS
- **Check:** `dig +short TXT minipass.me | grep spf`

**Issue 3: Multiple Source IPs**
- **Cause:** Email sent from different servers
- **Fix:** Ensure all sending IPs are in SPF record

---

## 🔐 Security Best Practices

### ✅ DO:
- Store password in secure location (`~/.mailpass` with `chmod 600`)
- Use environment variables for automation
- Review DMARC reports regularly
- Monitor authentication pass rates
- Keep logs for audit trail

### ❌ DON'T:
- Hardcode passwords in scripts
- Commit passwords to git
- Share credentials in Slack/email
- Ignore failed authentication reports
- Disable email verification

---

## 📚 Next Steps

1. **Review existing reports:** Check `app/tools/reports/*.md`
2. **Set up automation:** Add cron job for daily fetching
3. **Monitor trends:** Track pass rates over time
4. **Integrate alerts:** Add Slack/email notifications for failures
5. **Document findings:** Note any recurring issues

---

## 🆘 Getting Help

**If the script fails:**
1. Check password is set: `echo $MAIL_PASSWORD`
2. Test mail server: `telnet mail.minipass.me 993`
3. Review script output for specific errors
4. Check `scripts/README.md` for detailed troubleshooting

**If reports show failures:**
1. Run RFC compliance check: `./scripts/verify_email_rfc_compliance.sh`
2. Review DNS records: `dig +short TXT minipass.me`
3. Check mail server logs: `docker logs mailserver`
4. Consult DMARC report analysis in `app/tools/reports/*.md`

**For other issues:**
- Review main project docs: `CLAUDE.md`
- Check email system docs: `docs/EMAIL_TEMPLATE_SYSTEM.md`
- Inspect mail server config: `docker-compose.yml`

---

## 🎯 Success Criteria

You'll know the system is working when:
- ✅ Script runs without errors
- ✅ DMARC reports are downloaded automatically
- ✅ Analysis reports show 95%+ pass rate
- ✅ Cron job executes daily without manual intervention
- ✅ Reports are archived for historical tracking

**Target State:**
```
📊 WEEKLY SUMMARY (Last 7 days)
Reports fetched:      14 (2 per day from Google/Outlook)
Total messages:       2,450
Authentication rate:  99.8% (✅ Excellent)
Gmail failures:       0
Outlook failures:     0
```

# Action Plan: Achieve 100% Email Authentication Pass Rate

**Date:** February 16, 2026
**Current Status:** 96.9% pass rate (222/229 messages)
**Goal:** 100% pass rate
**Failed Messages:** 7 (2 fixable, 5 expected)

---

## 📊 Failure Analysis Summary

### Issue #1: System Emails with Wrong Domain (2 failures) ❌ **MUST FIX**

**Problem:**
- 2 emails sent with `From: mail.minipass.me` instead of `From: minipass.me`
- Both DKIM and SPF fail because authentication is configured for `minipass.me`, not `mail.minipass.me`

**Source:**
- Mail server hostname appears in From header
- Likely from system emails (postmaster, root, daemon)

**Impact:** 0.9% failure rate

---

### Issue #2: Forwarded Emails (5 failures) ✅ **EXPECTED BEHAVIOR**

**Problem:**
- 5 emails forwarded from external domains (telus.com, jfgoulet.com)
- Source IPs: 209.85.220.69, 209.85.220.41 (Google mail servers)
- SPF policy evaluation fails due to alignment mismatch

**Why This Happens:**
```
Original Email:
  From: user@telus.com
  SPF: telus.com (checks telus.com's SPF record)

Forwarded Through minipass.me:
  From: user@telus.com (header unchanged)
  SPF Domain Checked: telus.com
  SPF Actual IP: Google's servers (209.85.220.x)
  Result: SPF alignment fails (telus.com doesn't authorize Google IPs)

DKIM: Still passes (minipass.me re-signs with own DKIM key)
```

**This is EXPECTED:** Email forwarding always breaks SPF alignment. DKIM passes, which is sufficient.

**Impact:** 2.2% (not a real issue)

---

## 🔧 FIX FOR ISSUE #1: mail.minipass.me Domain

### Step 1: Check Current Postfix Configuration

```bash
# SSH to VPS
ssh user@vps

# Check current settings
docker exec mailserver postconf myhostname myorigin mydomain
```

**Expected output:**
```
myhostname = mail.minipass.me     ← PROBLEM (should be minipass.me)
myorigin = minipass.me            ← CORRECT
mydomain = minipass.me            ← CORRECT
```

---

### Step 2: Fix Postfix Origin Configuration

**The Fix:**
```bash
# Set correct origin for system emails
docker exec mailserver postconf -e "myorigin = minipass.me"

# Ensure myhostname doesn't leak into From headers
docker exec mailserver postconf -e "smtp_helo_name = minipass.me"

# Verify changes
docker exec mailserver postconf myorigin smtp_helo_name

# Restart mail server to apply
docker restart mailserver
```

**What this does:**
- `myorigin = minipass.me` → All locally generated emails use `@minipass.me`
- `smtp_helo_name = minipass.me` → SMTP HELO uses domain, not hostname

---

### Step 3: Check /etc/aliases for System Email Rewrites

```bash
# Check current aliases
docker exec mailserver cat /etc/aliases

# Look for entries like:
#   root: admin@minipass.me
#   postmaster: admin@minipass.me
```

**If NOT configured, add:**
```bash
docker exec mailserver bash -c 'cat >> /etc/aliases << EOF
# Forward system emails to admin
root: admin@minipass.me
postmaster: admin@minipass.me
abuse: admin@minipass.me
EOF'

# Rebuild alias database
docker exec mailserver newaliases
```

---

### Step 4: Check Application Email Configuration

**Check Flask app email configuration:**
```bash
# Check app/app.py for mail settings
grep -n "MAIL_DEFAULT_SENDER\|MAIL_SERVER" app/app.py
```

**Ensure:**
```python
app.config['MAIL_DEFAULT_SENDER'] = 'noreply@minipass.me'  # NOT mail.minipass.me
```

---

### Step 5: Verification (24-48 Hours Later)

```bash
# Fetch new DMARC reports
python scripts/fetch_dmarc_reports.py

# Run analysis
python scripts/analyze_dmarc_failures.py

# Expected result: No more mail.minipass.me failures
```

---

## 📈 Expected Results After Fix

### Before:
```
Total Messages:     229
Passed:             222 (96.9%)
Failed:             7 (3.1%)
  - mail.minipass.me: 2 failures
  - Forwarded emails: 5 failures
```

### After:
```
Total Messages:     ~250
Passed:             ~245 (98%+)
Failed:             ~5 (2%)
  - mail.minipass.me: 0 failures ✅
  - Forwarded emails: ~5 failures (expected)
```

**Why not 100%?**
- Email forwarding will always cause SPF alignment failures
- This is normal and doesn't impact deliverability
- DKIM passes, which is what Gmail primarily checks

---

## 🎯 Realistic Target: 98-99% Pass Rate

### Why This Is Excellent

1. **Gmail's Threshold:** Gmail requires EITHER SPF OR DKIM to pass (not both)
   - Your DKIM: 100% pass rate ✅
   - Your SPF: 100% pass rate (for direct emails) ✅
   - Forwarded emails: DKIM passes ✅ (sufficient!)

2. **Industry Standard:**
   - 95-98% pass rate is considered excellent
   - 100% is nearly impossible with email forwarding

3. **What Gmail Actually Checks:**
   - ✅ DKIM signature valid (you have this)
   - ✅ SPF record exists (you have this)
   - ✅ DMARC policy published (you have this)
   - ⚠️ SPF alignment (fails on forwards, but DKIM passes)

---

## 📋 Updated Monitoring Strategy

### Daily
```bash
# Automated DMARC report fetch
0 10 * * * cd /path/to/minipass_env && source ~/.mailpass && python scripts/fetch_dmarc_reports.py >> /var/log/dmarc_fetch.log 2>&1
```

### Weekly
```bash
# Comprehensive failure analysis
python scripts/analyze_dmarc_failures.py

# Check for new failure patterns (not forwarding-related)
```

### Monthly
```bash
# Review DMARC policy progression
# Current: p=none (monitor only)
# Target: p=quarantine (after 98%+ pass rate for 30 days)
# Goal: p=reject (after 99%+ pass rate for 90 days)
```

---

## 🚀 DMARC Policy Upgrade Path

### Current: `p=none` (Monitor Only)
```
v=DMARC1; p=none; rua=mailto:kdresdell@minipass.me
```
- All emails delivered regardless of authentication
- Reports sent for monitoring

### Step 2: `p=quarantine` (After Fix + 30 Days)
```
v=DMARC1; p=quarantine; pct=10; rua=mailto:kdresdell@minipass.me
```
- Start with 10% of failed emails quarantined
- Monitor impact for 2 weeks
- Increase to pct=50, then pct=100

### Step 3: `p=reject` (After 90 Days at Quarantine)
```
v=DMARC1; p=reject; rua=mailto:kdresdell@minipass.me; ruf=mailto:kdresdell@minipass.me
```
- Failed emails rejected outright
- Maximum protection against spoofing
- Requires 99%+ pass rate

**Timeline:**
- **Week 1:** Fix mail.minipass.me issue → 98% pass rate
- **Week 2-5:** Monitor stability at 98%
- **Week 6:** Upgrade to `p=quarantine; pct=10`
- **Week 8:** Increase to `pct=50`
- **Week 10:** Increase to `pct=100`
- **Week 20:** Upgrade to `p=reject` (if stable)

---

## 🔍 How to Identify Future Issues

### Red Flags (Run Daily):
```bash
python scripts/fetch_dmarc_reports.py
```

**Alert if:**
- Pass rate drops below 95%
- New failure pattern appears (not forwarding)
- Sudden increase in failed messages

### Logs to Check:
```bash
# Mail server logs
docker logs mailserver --tail 100 | grep -i "from=.*mail\.minipass\.me"

# Check for system emails with wrong domain
docker exec mailserver grep "From:.*mail\.minipass\.me" /var/log/mail.log
```

---

## ✅ Success Criteria

### Short-term (1 week):
- ✅ No more `mail.minipass.me` failures
- ✅ Pass rate: 98%+
- ✅ All direct emails pass authentication

### Medium-term (1 month):
- ✅ Pass rate stable at 98-99%
- ✅ DMARC policy upgraded to `p=quarantine; pct=10`
- ✅ No Gmail blocks or deliverability issues

### Long-term (3 months):
- ✅ DMARC policy at `p=reject`
- ✅ Zero spoofing attempts successful
- ✅ Email reputation: Excellent

---

## 📞 Support & Troubleshooting

### If Pass Rate Drops Suddenly:

1. **Check latest DMARC reports:**
   ```bash
   python scripts/analyze_dmarc_failures.py
   ```

2. **Look for new failure patterns:**
   - New source IPs
   - New domains
   - Different authentication results

3. **Check mail server logs:**
   ```bash
   docker logs mailserver --tail 500 | grep -i fail
   ```

4. **Verify DNS records:**
   ```bash
   ./scripts/verify_email_rfc_compliance.sh
   ```

### If Gmail Blocks Resume:

1. **Check DKIM/SPF for direct emails:**
   - Ensure 100% pass rate for non-forwarded emails

2. **Review sending volume:**
   ```bash
   python email_volume_analysis.py
   ```

3. **Check for spam complaints:**
   - Review DMARC reports for disposition: reject

---

## 🎓 Key Takeaways

1. **Forwarded emails will always fail SPF alignment** → This is expected
2. **DKIM is more important than SPF** → Gmail accepts either passing
3. **98% pass rate is excellent** → Industry standard for real-world usage
4. **Fix the mail.minipass.me issue** → This is the only real problem
5. **Monitor daily, adjust monthly** → Proactive > Reactive

---

## 📝 Implementation Checklist

**Today (VPS):**
- [ ] SSH to VPS
- [ ] Run: `docker exec mailserver postconf myorigin smtp_helo_name`
- [ ] Fix: `docker exec mailserver postconf -e "myorigin = minipass.me"`
- [ ] Fix: `docker exec mailserver postconf -e "smtp_helo_name = minipass.me"`
- [ ] Restart: `docker restart mailserver`
- [ ] Verify: `docker exec mailserver postconf myorigin smtp_helo_name`

**This Week:**
- [ ] Setup daily DMARC fetch cron job
- [ ] Monitor new reports for mail.minipass.me failures
- [ ] Verify pass rate increases to 98%+

**Next Month:**
- [ ] Review 30-day trend
- [ ] Upgrade DMARC policy to `p=quarantine; pct=10`
- [ ] Monitor for any deliverability impact

**Quarter 2:**
- [ ] Review 90-day stability
- [ ] Upgrade DMARC policy to `p=reject`
- [ ] Celebrate bulletproof email system! 🎉

---

**End of Action Plan**

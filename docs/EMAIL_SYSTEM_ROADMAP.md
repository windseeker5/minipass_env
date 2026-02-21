# Minipass Email System — Master Roadmap

**Last Updated:** February 19, 2026
**Branch:** `feature/email-infrastructure-overhaul` (merged to main: commit `92b0813`)

---

## Current Status: Phases 1, 2 & 3 Complete ✅ — Phase 4 Next

```
Pass Rate:    96.9% (222/229 messages)
DKIM:         100% ✅
SPF (direct): 100% ✅
DMARC policy: p=none (monitor only)
Gmail ban:    RESOLVED (Feb 12, 2026)
```

### Email Volume (Jan 11 – Feb 12, 2026)
- **62 emails/day** average outbound
- **74% go to Gmail** addresses (2,415 / 3,255 total)
- **lhgi@minipass.me** = 89% of outbound traffic (938 of 1,923 sent)
- During Gmail ban: 40.9% failure rate (now resolved)

---

## What's Done

### Phase 1 — RFC 5322 Compliance ✅
- `app/utils.py` — Added `Date`, `Return-Path`, `Auto-Submitted`, `Message-ID` headers + UTF-8 charset
- `MinipassWebSite/utils/email_helpers.py` — Same headers added to `send_user_deployment_email()` and `send_password_reset_email()`
- Both email systems are now fully RFC 5322 compliant

### DMARC Monitoring Infrastructure ✅
- `scripts/fetch_dmarc_reports.py` — Auto-fetches DMARC reports via IMAP from 5 providers (Google, Microsoft, Yahoo)
- `scripts/analyze_dmarc_failures.py` — Analyzes failures and generates Markdown reports
- `scripts/email_monitor_to_db.py` — SQLite persistence for email health metrics (running on VPS)
- Cron job on VPS: daily DMARC fetch at 10 AM
- Sieve filter on `kdresdell@minipass.me` — blocks DMARC reports from forwarding to Gmail (prevents the forwarding loop that caused the Feb 8 ban)

### Monitoring Scripts ✅
- `scripts/email_health_check.py` — Queries `email_log` table, alerts if success rate < 95%
- `scripts/verify_email_rfc_compliance.sh` — Verifies SPF, DKIM, DMARC, MX, PTR records

### Log Retention Enhancement ✅
- **Mail Queue**: Extended from 5d to 10d (`maximal_queue_lifetime` and `bounce_queue_lifetime`)
- **Log Files**: Extended from 4 to 8 weeks rotation (weekly rotation, 8 cycles retained)
- **Purpose**: Ensures 30+ days of historical data required for Phase 2 DMARC monitoring

---

## Failure Analysis (96.9% Pass Rate)

### Issue 1 — `mail.minipass.me` domain (2 failures) ❌ FIX THIS
System emails (postmaster, root) are sent with `From: mail.minipass.me` instead of `From: minipass.me`.
DKIM and SPF fail because authentication is configured for `minipass.me` only.

**Fix (run on VPS):**
```bash
docker exec mailserver postconf -e "myorigin = minipass.me"
docker exec mailserver postconf -e "smtp_helo_name = minipass.me"
docker restart mailserver
```

**Verify:**
```bash
docker exec mailserver postconf myorigin smtp_helo_name
```

### Issue 2 — Forwarded emails (5 failures) ✅ EXPECTED BEHAVIOR
Emails forwarded from external domains (telus.com, jfgoulet.com) always break SPF alignment.
DKIM passes, which is sufficient for Gmail delivery. This is industry-standard behavior, not a real problem.

### Expected after fix
```
Pass Rate:    98-99%
DKIM:         100% ✅
SPF (direct): 100% ✅
Forwarded:    ~2% SPF fail (expected, DKIM passes)
```

---

## Phase 2 — DMARC Policy Upgrade

**Prerequisite:** Fix `mail.minipass.me` issue above and confirm 98%+ pass rate for 30 days.

### Step 1: Quarantine (Week 6 from fix)
Change DNS TXT record for `_dmarc.minipass.me`:
```
v=DMARC1; p=quarantine; pct=10; rua=mailto:kdresdell@minipass.me
```
- Only 10% of failing emails get quarantined
- Monitor deliverability for 2 weeks
- Increase to `pct=50`, then `pct=100` over 4 weeks

### Step 2: Reject (Week 20 from fix, if stable)
```
v=DMARC1; p=reject; rua=mailto:kdresdell@minipass.me; ruf=mailto:kdresdell@minipass.me
```
- Maximum spoofing protection
- Only do this after 99%+ pass rate sustained for 90 days

### DMARC Upgrade Timeline
| Week | Action |
|------|--------|
| Now  | Fix `mail.minipass.me` issue |
| +1   | Confirm 98% pass rate |
| +2–5 | Monitor stability |
| +6   | `p=quarantine; pct=10` |
| +8   | `p=quarantine; pct=50` |
| +10  | `p=quarantine; pct=100` |
| +20  | `p=reject` (if stable) |

---

## Phase 3 — Hybrid Hosted Images ✅ Complete

**Status:** Complete (February 2026). Hero and owner logo images are served via hosted Flask routes. QR code remains CID-embedded as a functional element.

**Email size achieved:** ~8–10 KB per email (down from ~30–50 KB with full CID attachments — ~75–80% reduction)

### Why Hybrid (Not Fully Hosted)

The QR code is a **functional** element — it must always display, even in privacy-blocking email clients. Hero images and logos are **decorative** — the email is fully usable without them.

**Image client compatibility:**
| Client | External images | Notes |
|---|---|---|
| Gmail | ✅ Auto-loads | Google proxies and caches all external images |
| Apple Mail | ✅ Auto-loads | Apple Privacy Proxy fetches and caches |
| Outlook.com (web) | ✅ Usually loads | |
| Outlook Desktop | ⚠️ Blocked by default | User must click "Download Pictures" |

**Decision:** Outlook Desktop is the only real blocker. Activity managers are predominantly on mobile (Gmail / Apple Mail). The trade-off is acceptable. If an Outlook Desktop user blocks images: QR code still shows, transaction table still shows, CTA button still works. The email is functional — just missing decorative hero/logo.

### Image Delivery Strategy

| Image | Method | Reason |
|---|---|---|
| QR code | CID inline (unchanged) | Functional — must always display |
| Hero image | Hosted URL | Decorative — served via existing priority route |
| Owner logo | Hosted URL | Decorative — letter fallback already exists |
| Ticket decoration | Hosted URL (static file) | Tiny static asset, never changes |
| Interac logo | Hosted URL (static file) | Brand asset, always the same |

### Architecture — How It Works

The system already has all the infrastructure needed. The hero image route handles the full 3-tier priority:

```
Priority 1: Custom upload → static/uploads/{activity_id}_{template}_hero.png
Priority 2: Default      → templates/email_templates/{template}_original/inline_images.json
Priority 3: Fallback     → static/uploads/activity_images/{activity.image_filename}
                           (only when template has active customizations)
```

**Hero image URL** (existing route, just not wired to emails yet):
```
https://lhgi.minipass.me/activity/{activity_id}/hero-image/{template_type}
```

**Owner logo URL** (already web-accessible via Flask static serving):
```
https://lhgi.minipass.me/static/uploads/{activity_id}_owner_logo.png
```
When no custom logo exists: the letter-based fallback design is used (already implemented).

**Static decoration URLs** (one-time extraction from inline_images.json):
```
https://lhgi.minipass.me/static/images/email/ticket.png
https://lhgi.minipass.me/static/images/email/interac-logo.png
```

### What Does NOT Change

- `inline_images.json` files — still needed by the `/hero-image/` route for Priority 2
- `_original/` folder structure — unchanged
- The 3-tier priority logic — unchanged
- Reset flow — unchanged
- Upload flow — unchanged
- QR code delivery — stays CID inline

### Implementation Summary (What Was Done)

**Step 1 — Extract static decoration images**
- Decode `ticket.png` and `interac-logo.jpg` from their `inline_images.json`
- Save to `app/static/images/email/`
- These are small (~1–9 KB), global, never change

**Step 2 — Update compiled templates (7 templates + 7 originals)**
- Replace `<img src="cid:hero_image">` → `<img src="{{ hero_image_url }}">`
- Replace `<img src="cid:logo">` → `<img src="{{ owner_logo_url }}">`
- Replace `<img src="cid:ticket">` → `<img src="https://lhgi.minipass.me/static/images/email/ticket.png">`
- QR code `cid:qr_code` stays unchanged

**Step 3 — Update `get_email_context()` in `utils.py`**
- Add `hero_image_url` = `f"https://lhgi.minipass.me/activity/{activity.id}/hero-image/{template_type}"`
- Add `owner_logo_url` = `f"https://lhgi.minipass.me/static/uploads/{activity.id}_owner_logo.png"`
  - If no logo exists: set to a placeholder or handle in template

**Step 4 — Implement `use_hosted_images=True` in `send_email()` (utils.py:2090+)**
- When `use_hosted_images=True`: skip all MIME image attachment except QR code
- The `use_hosted_images` parameter already exists in the function signature — just not implemented

**Step 5 — Update all email function callers**
- `send_new_pass_email()`, `send_payment_received_email()`, `send_pass_redeemed_email()`
- `send_signup_email()`, `send_late_payment_email()`, `send_survey_invitation_email()`
- Pass `use_hosted_images=True`

**Step 6 — Update `compileEmailTemplate.py`**
- Add a mode that produces URL-referenced HTML output (in addition to current CID mode)
- Keep base64 JSON generation (still needed for `/hero-image/` route)

**Step 7 — Update preview and test-email functions (app.py)**

`email_preview_live()` currently does post-render string substitution:
replace `cid:X` → `data:image/...;base64,...` in the rendered HTML.

With URL-based templates, this changes to context-level substitution before rendering:
- If user uploaded a hero (unsaved): set `hero_image_url = data:image/png;base64,...` in context
- If hero is saved/default: set `hero_image_url = /activity/{id}/hero-image/{template_type}` (browser fetches)
- Logo: same pattern using `owner_logo_url`
- QR code: still handled via string substitution of `cid:qr_code` → data URI (unchanged)

`test_email_template()` currently loads all inline images as CID attachments.
With URL-based templates: only attach QR code as CID. Remove hero/logo attachment.
The template HTML already resolves to hosted URLs via context.

**Step 8 — Test**
- Send test emails for all 7 template types
- Verify images load in Gmail
- Verify QR code displays in all clients
- Verify custom hero override works (Priority 1)
- Verify reset restores correct image (Priority 2)
- Verify preview with unsaved uploaded hero shows correctly
- Verify preview with no logo shows letter fallback
- Verify print preview works

### Files Changed

| File | Change |
|---|---|
| `app/templates/email_templates/*_compiled/index.html` | Replace CID refs with URL refs (7 files) |
| `app/templates/email_templates/*_original/index.html` | Same update for originals (7 files) |
| `app/utils.py` | `get_email_context()` + `send_email()` implementation |
| `app/app.py` | `email_preview_live()` + `test_email_template()` image handling |
| `app/templates/email_templates/compileEmailTemplate.py` | Add URL mode |
| `app/static/images/email/` | New directory with 2–3 static decoration images |

**Actual effort:** ~6–8 hours

---

## Phase 4 — Email Analytics Dashboard ✅ COMPLETE

**Status (Updated Feb 20, 2026):** All Phase 4 components complete and operational ✅

### ✅ Data Layer Implementation Complete
**Enhanced monitoring script** with bulk backfill capability:
- **Root cause fixes applied**: Amavis line filtering + regex `from=<([^>]*)>` for bounces
- **Bulk backfill tool created**: `scripts/bulk_email_backfill.py` for historical data processing
- **Database populated**: 8 days of comprehensive data (Feb 14-21, 2026)
- **Data quality**: All customer emails properly identified, edge cases handled

### ✅ Production Cron Jobs Complete
**Optimized monitoring schedule** for real-time dashboard updates:
- **8 AM, 12 PM, 4 PM, 8 PM daily**: Today's data processing (4-hour intervals)
- **6 AM daily**: Yesterday's complete data for historical records
- **10 AM daily**: DMARC report fetching (existing)
- **Logs**: `/home/kdresdell/logs/` (user-writable permissions)

### Cron Job Backup (For Disaster Recovery)
**Current production cron configuration** (backup copy):
```bash
# DMARC fetch (daily at 10:00 AM)
0 10 * * * source /home/kdresdell/.mailpass && /usr/bin/python3 /home/kdresdell/minipass_env/scripts/fetch_dmarc_reports.py >> /home/kdresdell/logs/dmarc_fetch.log 2>&1

# Email monitoring - TODAY's data every 4 hours during business hours
0 8,12,16,20 * * * /usr/bin/python3 scripts/email_monitor_to_db.py --date $(date +%Y-%m-%d) >> /home/kdresdell/logs/email_monitor_today.log 2>&1

# Email monitoring - YESTERDAY's complete data (daily at 6 AM, after log rotation)
0 6 * * * cd /home/kdresdell/minipass_env && /usr/bin/python3 scripts/email_monitor_to_db.py >> /home/kdresdell/logs/email_monitor_yesterday.log 2>&1
```

**Restoration command**: `crontab -` then paste above content and press Ctrl+D

### ✅ Historical Data Backfill Complete
**Maximum available data range processed**:
- **Coverage**: Feb 14-21, 2026 (8 days) — complete mail server history
- **Volume**: 11-28 emails/day across multiple applications
- **Applications tracked**: `lhgi@minipass.me`, `kdc_app@minipass.me`, `demo_app@minipass.me`, `heq_app@minipass.me`, `support@minipass.me`
- **Edge cases included**: External senders, bounces, deferrals, DMARC reports

### Database Retrieval for Local Development
**Copy monitoring database from VPS to local dev system**:
```bash
# Copy main monitoring database (45KB SQLite file)
scp username@vps-ip:/home/kdresdell/minipass_env/email_monitoring/monitoring.db ./email_monitoring/

# Copy entire monitoring directory (optional - includes reports, analysis)
scp -r username@vps-ip:/home/kdresdell/minipass_env/email_monitoring/ ./

# Verify database size and recent data
ls -lh email_monitoring/monitoring.db
python3 scripts/email_monitor_to_db.py --report
```

**Purpose**: Work on dashboard locally while keeping customer data out of GitHub
**Database contents**: 8 days of email analytics (Feb 14-21) for dashboard development and testing
**Security**: Customer email data stays local, not committed to version control

### ✅ UI Layer Implementation Complete
**Dashboard accessible at** `/admin/mail-dashboard`:
- **Route**: Implemented in `MinipassWebSite/app.py` with admin authentication
- **Template**: `MinipassWebSite/templates/admin/mail_dashboard.html` created
- **Data source**: `email_monitoring/monitoring.db` (45KB SQLite database)
- **Features**: Volume cards, success rates, failure breakdown, Chart.js trends

### Dashboard Features Implemented

| Card | Data Source | Status |
|---|---|---|
| Email volume (today/week/month) | `email_volume_daily` table | ✅ |
| Success rate + 7-day trend | Calculated from sent/bounced/deferred | ✅ |
| Recent failures (last 10) | `email_failures` table | ✅ |
| Mail server health | Queue snapshots + mailbox sizes | ✅ |
| DMARC pass rate | DMARC reports integration | 🔄 Pending |

### 🔄 REMAINING WORK (Lower Priority):

**DMARC Analysis Integration**
- Current status: DMARC fetching works, analysis works, database integration missing
- Impact: Dashboard shows "No DMARC data" but email authentication is functional
- Effort: ~2 hours to connect existing DMARC analysis to monitoring database

---

## Phase 4 Summary ✅

**Achievement**: Complete email monitoring infrastructure with real-time dashboard
**Data coverage**: 8 days of comprehensive email analytics (maximum available history)
**Monitoring frequency**: Every 4 hours for current-day data + daily historical processing
**Dashboard status**: Fully implemented and ready for production use

**Next phase**: Dashboard validation and DMARC integration (optional)

---

## Phase 5 — Transactional Email Service (Only if Needed)

**Trigger:** Only consider if Gmail blocks resume after Phases 1–2, or volume exceeds 5,000 emails/day.

Current architecture (self-hosted docker-mailserver) is fine for current scale. Keep it.

| Service | Cost at ~1,900/mo | Cost at 186k/mo | Notes |
|---------|-------------------|-----------------|-------|
| Self-hosted | $0 | $0 | Current, requires maintenance |
| AWS SES | $0.19 | $18.60 | Best value at scale |
| SendGrid | $0 (free tier) | $89.95 | Easy setup |
| Postmark | $15 | $279 | Best deliverability reputation |

**Recommendation:** Stay self-hosted. AWS SES as fallback if deliverability problems persist.

---

## Monitoring Commands (Run on VPS)

```bash
# Daily DMARC fetch (already automated via cron)
source ~/.mailpass && python scripts/fetch_dmarc_reports.py

# Analyze failures
python scripts/analyze_dmarc_failures.py

# Email health check (queries email_log table)
python scripts/email_health_check.py

# Verify DNS/RFC compliance
bash scripts/verify_email_rfc_compliance.sh

# Check mail server logs
docker logs mailserver --tail 100

# Check queue
docker exec mailserver postqueue -p
```

---

## Phase 6 — Mail Server Stability & Operations (Future)

**Trigger:** After Phase 2 DMARC upgrade is stable and operational monitoring is needed.

**Goal:** Bulletproof mail server with backup/recovery strategy and operational dashboard.

### Backup Strategy (Simple MVP)

**Data to Backup (~31MB total):**
- **Configuration**: `./config/` (136KB), `./mailserver.env`, `docker-compose.yml`
- **Mailbox Data**: `./maildata/` (~29MB) - user emails and folders
- **Mail State**: `./mailstate/` (~1.9MB) - postfix queues, certificates
- **DNS Records**: SPF, DKIM, DMARC settings documentation

**Backup Method Options:**
1. **Simple rsync/SSH** (Recommended for MVP)
   - Daily automated rsync to remote server
   - Retention: 7 daily, 4 weekly, 6 monthly backups
   - Recovery time: ~30-60 minutes

2. **Docker Volume Backup** (Alternative)
   - `docker run --rm -v maildata:/data -v $(pwd):/backup alpine tar czf /backup/maildata.tar.gz /data`
   - Pros: Consistent snapshots, easy automation
   - Cons: Larger files, slower restore

### Recovery Strategy (Max 1-3 Hour Downtime)

**Option A: Manual Restore Scripts (MVP)**
```bash
# Emergency restore procedure
rsync -av backup-server:/minipass-backup/ ./
docker-compose down
docker-compose up -d
# Verify mail flow and DNS
```

**Option B: Docker Swarm Evaluation**
- **Simple 2-node setup** on same VPS provider
- **Automatic failover** with shared storage
- **Trade-off**: More complexity vs faster recovery
- **Decision**: Evaluate after manual backup is proven

**Recovery SLA:**
- **Detection**: < 15 minutes (monitoring alerts)
- **Restore**: < 2 hours (manual) or < 30 minutes (automated)
- **Verification**: < 30 minutes (test email flow)

### Enhanced Log Retention ✅

**Already Completed (Feb 17, 2026):**
- **Mail Queue**: Extended 5d → 10d (`maximal_queue_lifetime`, `bounce_queue_lifetime`)
- **Log Files**: Extended 4 weeks → 8 weeks rotation (weekly rotation, 8 cycles)
- **Purpose**: Minimum 1+ month historical data for troubleshooting and analysis
- **Implementation**: Postfix config + logrotate configuration updated

### Mail Server Dashboard (MinipassWebSite Integration)

**Integration Plan:**
- **Location**: Add to existing `MinipassWebSite/templates/admin/tools.html`
- **Data Source**: `email_monitoring/monitoring.db` (45KB SQLite database)
- **Access**: Same admin login as customer management

**Dashboard Features:**
- **Email Volume**: Daily/weekly sent, delivered, failed counts
- **Success Rate**: Current and historical trends (target: >95%)
- **DMARC Status**: Pass/fail rates, authentication alignment
- **Mail Server Health**: Queue size, recent errors, log alerts
- **Quick Actions**: View recent logs, restart services, test email

**Technical Implementation:**
- New Flask route: `/admin/mail-dashboard`
- Query existing monitoring database
- Simple charts (Chart.js or similar)
- Refresh every 5 minutes (auto-reload)

**UI Design:**
- Match existing admin tools styling
- Minimalist cards layout
- Red/green status indicators
- Mobile-responsive for phone monitoring

### Implementation Timeline & Effort

**Phase 6.1 — Basic Backup (Week 1-2)**
- Effort: ~4-6 hours
- Create rsync backup scripts
- Set up remote backup location
- Test restore procedures
- Document recovery steps

**Phase 6.2 — Dashboard Integration (Week 3-4)**
- Effort: ~6-8 hours
- Add mail dashboard route to MinipassWebSite
- Create admin template integration
- Query monitoring database
- Basic charts and status displays

**Phase 6.3 — Advanced Options (Week 5-6)**
- Effort: ~8-12 hours
- Docker Swarm evaluation and testing
- Automated failover setup (if chosen)
- Enhanced monitoring alerts
- Performance optimization

### Docker Swarm Evaluation Criteria

**Evaluate Docker Swarm if:**
- Manual backup/restore takes >2 hours in practice
- Downtime becomes business-critical issue
- Multiple mail server failures occur

**Docker Swarm Benefits:**
- **Automatic failover**: ~5-10 minute recovery
- **Load balancing**: Multiple mail server instances
- **Rolling updates**: Zero-downtime updates

**Docker Swarm Complexity:**
- **Network setup**: Overlay networks, load balancers
- **Storage**: Shared volumes or database replication
- **Monitoring**: Health checks and failure detection
- **Learning curve**: Docker Swarm concepts

**Decision Matrix:**
| Factor | Manual Backup | Docker Swarm |
|--------|---------------|--------------|
| Complexity | Simple ⭐ | Moderate ⭐⭐⭐ |
| Recovery Time | 1-2 hours | 5-10 minutes |
| Setup Effort | 4-6 hours | 12-20 hours |
| Maintenance | Low | Medium |
| **Recommendation** | **Start here** | Evaluate later |

---

## Files Reference

| File | Purpose |
|------|---------|
| `scripts/fetch_dmarc_reports.py` | IMAP auto-fetch DMARC reports |
| `scripts/analyze_dmarc_failures.py` | Parse and analyze failures |
| `scripts/email_monitor_to_db.py` | SQLite metrics persistence (VPS) |
| `scripts/email_health_check.py` | Delivery health monitoring |
| `scripts/verify_email_rfc_compliance.sh` | DNS/RFC verification |
| `app/utils.py` | Customer app email sending (RFC compliant) |
| `MinipassWebSite/utils/email_helpers.py` | Platform email sending (RFC compliant) |
| `docs/VPS_ARCHITECTURE_DIAGRAM.md` | Full VPS/container architecture |

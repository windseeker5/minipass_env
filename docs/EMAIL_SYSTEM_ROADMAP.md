# Minipass Email System — Master Roadmap

**Last Updated:** February 21, 2026
**Branch:** `main`

---

## Current Status: Phases 1–4 + Dashboard Intelligence Complete ✅ — VPS Deployment & Cleanup Pending

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

### Issue 1 — `mail.minipass.me` domain ✅ FIXED
System emails (postmaster, root) were sent with `From: mail.minipass.me` instead of `From: minipass.me`.
Fix applied: `myorigin = minipass.me` and `smtp_helo_name = minipass.me` set via postconf, mailserver restarted.

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

**Prerequisite:** Confirm 98%+ pass rate for 30 days (clock started after `mail.minipass.me` fix applied).

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
| Now  | ✅ `mail.minipass.me` fix applied |
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

### ✅ UI Layer Implementation Complete (Feb 21, 2026)
**Dashboard accessible at** `/admin/mail-dashboard`:
- **Route**: Implemented in `MinipassWebSite/app.py` with `@require_admin` decorator
- **Base layout**: `MinipassWebSite/templates/admin/admin_base.html` — DaisyUI 4 sidebar layout shared by all admin pages
- **Template**: `MinipassWebSite/templates/admin/mail_dashboard.html` — full analytics dashboard
- **Data source**: `email_monitoring/monitoring.db` (45KB SQLite database, read-only)
- **Other admin pages rebuilt**: `tools.html` and `promo_codes.html` now extend `admin_base.html`

### Unified Admin Layout (`admin_base.html`)
- **Stack**: DaisyUI 4 + Tailwind CSS CDN + Lucide Icons + Chart.js (admin-only, NOT loaded on main site)
- **Layout**: Responsive drawer sidebar (mobile hamburger + desktop always-open)
- **Nav items**: Customers (`/admin/tools`), Promo Codes (`/admin/promo-codes`), Email Analytics (`/admin/mail-dashboard`)
- **Active state**: Detected via `request.endpoint` — active item highlighted with `bg-primary text-primary-content`
- **Dark/light theme toggle**: Sun/moon button in both mobile and desktop headers; `localStorage` persistence; applied before render to avoid flash
- **CDN dependencies** (admin pages only):
  - `daisyui@4.12.14/dist/full.min.css`
  - `cdn.tailwindcss.com`
  - `unpkg.com/lucide@latest/dist/umd/lucide.min.js`
  - `cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js`

### Dashboard Features Implemented

| Feature | Data Source | Status |
|---|---|---|
| Email volume (today / 7-day) | `email_volume_daily` table | ✅ |
| Success rate % | `(sent - bounced - deferred) / sent × 100` | ✅ |
| Active failures count (7d) | `email_failures` WHERE last 7 days | ✅ |
| 7-day volume bar chart | `email_volume_daily` GROUP BY date | ✅ |
| 7-day success rate line chart | Calculated per day; Y-axis: 0–110%, stepSize 20 | ✅ |
| Recent failures table (200 records) | `email_failures` ORDER BY timestamp DESC LIMIT 200 | ✅ |
| — Search filter (client-side) | JS `applyFilter()` on all columns | ✅ |
| — Pagination (10/page) | JS `render()` with DaisyUI `join` buttons | ✅ |
| Per-sender breakdown table | `email_volume_daily` GROUP BY user_email | ✅ |
| Mail queue snapshot | `mail_queue_log` most recent record | ✅ |
| Mailbox sizes | `mailbox_sizes` most recent per user | ✅ |
| DMARC pass rate | `dmarc_daily` table integration | 🔄 Pending |

### ✅ BUGS FIXED (Feb 21, 2026)

**Bug 1 — `send_support_error_email` swapped arguments** ✅ FIXED
- Swapped args at all 3 call sites in `MinipassWebSite/app.py` (~lines 445, 480, 637)

**Bug 2 — Duplicate records in `email_failures` table** ✅ FIXED
- Added `UNIQUE(timestamp, from_user, to_address)` index to schema
- Changed `INSERT INTO` → `INSERT OR IGNORE INTO` in monitoring script
- Existing duplicates deduplicated on local DB (26 → 10 rows)

---

### ✅ Phase 4b — Dashboard Intelligence (Feb 21, 2026)

**New features added in this session:**

**1. Plain-English Error Classification + Hover Tooltip**
- `classify_error()` helper added to `MinipassWebSite/app.py` (above `mail_dashboard` route)
- Maps raw Postfix error strings to human-readable labels: Gmail rate limit, SPF/DMARC issue, recipient not found, spam filter rejection, temp/permanent bounce
- Error column in Recent Failures table now shows: bold plain-English reason + muted truncated raw error
- Hover over any error cell → floating tooltip shows full raw Postfix error string

**2. Deferred Resolution Badge**
- Each deferred failure now gets a `resolution` field computed at page-load time
- Queries `email_volume_daily`: if sender had `sent_count > 0` on any date after the deferral → `resolution = 'likely_delivered'`
- New "Resolved" column in Recent Failures table:
  - Bounced → `Permanent` (red badge)
  - Deferred + likely delivered → `✓ Delivered later` (green badge)
  - Deferred + unknown → `—` (ghost badge)
- Info icon `ⓘ` on "Failures (7d)" stat card explains deferrals still count as failures

**3. Per-Sender Drill-Down Modal**
- New Flask route: `GET /admin/mail-dashboard/sender-detail?sender=X` (JSON, `@require_admin`)
- Sender names in Per-Sender Breakdown table are now clickable buttons
- DaisyUI `<dialog>` modal shows:
  - Auto-generated plain-English summary (deferrals by date, bounce count, or "no failures")
  - Day-by-day table: Date | Sent | Bounced | Deferred
  - Recent failures sub-table (up to 50): Time | To | Reason | Status
- Loaded via `fetch()` — no page reload

**4. Fix "unknown" Sender in Monitoring Script**
- `scripts/email_monitor_to_db.py` Pass 2 fix:
  - Changed `if not from_email:` → `if from_email is None:` (prevents `'<>'` from triggering fallback)
  - Changed fallback `(from_m.group(1) if from_m else None) or 'unknown'` → `(from_m.group(1) or '<>') if from_m else 'unknown'`
  - Empty envelope senders (`from=<>`, used for DSNs/bounce notifications) now stored as `'<>'` instead of `'unknown'`
  - **Note**: Historical `'unknown'` rows in DB on VPS require manual cleanup (see VPS Deployment section below)

**Files changed in Phase 4b:**
| File | Change |
|------|--------|
| `MinipassWebSite/app.py` | Added `classify_error()`, failures enrichment (reason + resolution), new `/sender-detail` route |
| `MinipassWebSite/templates/admin/mail_dashboard.html` | Error tooltip UI, Resolution column, info icon, sender buttons, sender modal + JS |
| `scripts/email_monitor_to_db.py` | Fix `from=<>` stored as `'<>'` instead of `'unknown'` |

---

### 🚀 VPS DEPLOYMENT REQUIRED

**Context:** All changes above were developed and committed locally. The VPS has the old code and the live `monitoring.db`. The following steps must be run on the VPS after `git pull`.

**Step 1 — Pull latest code on VPS**
```bash
cd /home/kdresdell/minipass_env
git pull
```

**Step 2 — Restart Flask to pick up app.py + template changes**
```bash
# (however you restart the MinipassWebSite Flask app in production)
docker-compose restart lhgi   # or the relevant service
```
The new dashboard features (tooltips, resolution badges, sender modal) will work immediately — they read from the existing DB with no further action.

**Step 3 — Clean up historical "unknown" rows in monitoring.db**

⚠️ Re-running the monitoring script alone is NOT enough — old `'unknown'` rows and new `'<>'` rows have different `from_user` keys, so `INSERT OR IGNORE` would add duplicates. You must delete the old rows first.

```bash
cd /home/kdresdell/minipass_env
sqlite3 email_monitoring/monitoring.db
```

```sql
-- See what we're cleaning up
SELECT user_email, SUM(sent_count), SUM(deferred_count) FROM email_volume_daily WHERE user_email = 'unknown' GROUP BY user_email;
SELECT COUNT(*) FROM email_failures WHERE from_user = 'unknown';

-- Delete the old 'unknown' rows
DELETE FROM email_volume_daily WHERE user_email = 'unknown';
DELETE FROM email_failures WHERE from_user = 'unknown';

.quit
```

**Step 4 — Re-run monitoring script for affected dates**
```bash
cd /home/kdresdell/minipass_env
python3 scripts/email_monitor_to_db.py --date 2026-02-15
python3 scripts/email_monitor_to_db.py --date 2026-02-16
```
The 18 emails previously stored as `'unknown'` will now be stored as `'<>'` (empty envelope sender — DSNs/bounce notifications, all successful).

**Step 5 — Verify**
```bash
python3 scripts/email_monitor_to_db.py --report
```
The `'unknown'` row should be gone from the per-user breakdown. A `'<>'` row will appear with the 18 emails.

**Step 6 — Copy refreshed DB to local dev (optional)**
```bash
# Run from local machine
scp username@vps-ip:/home/kdresdell/minipass_env/email_monitoring/monitoring.db ./email_monitoring/
```

### 🔄 REMAINING WORK (Lower Priority)

**DMARC Analysis Integration**
- Current status: DMARC fetching works, analysis works, database integration missing
- Impact: Dashboard shows "No DMARC data" but email authentication is functional
- Effort: ~2 hours to connect existing DMARC analysis to monitoring database

---

## Phase 4 Summary ✅

**Achievement**: Complete email monitoring infrastructure with real-time dashboard + unified admin layout
**Data coverage**: 8 days of comprehensive email analytics (maximum available history)
**Monitoring frequency**: Every 4 hours for current-day data + daily historical processing
**Dashboard status**: Fully implemented — search, pagination, dark mode, per-sender breakdown, health panels

**Next session focus**:
1. **VPS deployment** — `git pull` on VPS, restart Flask, run DB cleanup sequence (see VPS Deployment section above)
2. **DMARC integration** — Connect existing DMARC analysis to monitoring DB (~2h effort)
3. **Copy refreshed DB to local** after VPS cleanup

---

## Quick How to Set Up Local Dev to Test Dashboard Mini Pass Admin Dashboard

**Purpose:** Copy production monitoring data and customer database from VPS to local development environment for dashboard testing and development.

### Copy Email Monitoring Data from VPS to Local Dev

```bash
# Copy entire monitoring directory (database + logs + reports)
scp -P 2222 -r kdresdell@minipass.me:/home/kdresdell/minipass_env/email_monitoring/ ./

# Copy monitoring database only (lightweight option)
scp -P 2222 kdresdell@minipass.me:/home/kdresdell/minipass_env/email_monitoring/monitoring.db ./email_monitoring/

# Copy monitoring logs for debugging
scp -P 2222 kdresdell@minipass.me:/home/kdresdell/logs/email_monitor*.log ./logs/
```

### Copy Customer Database from VPS to Local Dev

```bash
# Copy main customer database to Flask app instance directory
scp -P 2222 kdresdell@minipass.me:/home/kdresdell/minipass_env/app/instance/minipass.db ./app/instance/

# Copy MinipassWebSite database (if separate)
scp -P 2222 kdresdell@minipass.me:/home/kdresdell/minipass_env/MinipassWebSite/instance/minipass.db ./MinipassWebSite/instance/
```

### Verify Local Setup

```bash
# Verify monitoring database
python3 scripts/email_monitor_to_db.py --report

# Test Flask dashboard access (after copying customer DB)
cd app && flask run
# Access: http://localhost:5000/admin/mail-dashboard

# Test MinipassWebSite dashboard access
cd MinipassWebSite && flask run --port 5001
# Access: http://localhost:5001/admin/mail-dashboard
```

**Note:** Always copy fresh data from VPS before dashboard development sessions to ensure you're working with current email analytics and customer data.

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

## Phase 6 — Backup & Failover Strategy

**Context:** The Gmail ban crisis of Feb 2026 exposed a critical gap — zero backup strategy and zero alerting. Phases 1–4 are complete (96.9% pass rate, Gmail ban resolved). Phase 6 addresses infrastructure resilience: know immediately when something breaks, recover fast when it does.

**Two-tier approach:**
- **Phase 6a MVP**: Recover in 30–60 min with some manual steps. Zero new ongoing costs. Do this now.
- **Phase 6b Full**: Ansible-automated provisioning for faster recovery when a crisis hits. No standby VPS running 24/7.

**Key insight — what actually causes downtime:**
1. Container crash → fixed by `restart: always` (handles ~80% of cases, already configured)
2. Misconfiguration push → git rollback + `docker-compose up -d` (15 min)
3. VPS provider failure → backup restore to new VPS (Phase 6a: 45–90 min, Phase 6b: 25–35 min)
4. Another domain ban → Phase 5 (AWS SES fallback) addresses this

The backup strategy doesn't prevent bans. Phase 6 is purely about infrastructure resilience.

---

### Phase 6a — MVP Backup & Recovery

**Goal:** Know immediately when something breaks. Recover in 30–60 minutes. Zero new ongoing costs.

#### Step 1: External Alerting — FREE (Day 1, 30 min)

**UptimeRobot** (free tier, checks every 5 min, SMS + email alerts):
- Monitor HTTPS: `https://minipass.me`
- Monitor HTTPS: `https://lhgi.minipass.me`
- Monitor Port: `minipass.me:587` (mail submission — most critical)
- Monitor Port: `minipass.me:993` (IMAP)
- Set: 1-minute downtime threshold, email + SMS alerts

**healthchecks.io** (free tier, cron heartbeat monitor):
- Add a `/ping` call to the end of the nightly backup cron
- Alerts if backup stops running (server up, but script broken)
- Both services are external — alert even when your VPS is completely dead

#### Step 2: Docker Restart Policies — ALREADY DONE ✅

All services already have `restart: always` in `docker-compose.yml`:
`nginx-proxy`, `nginx-letsencrypt`, `mail-cert-request`, `mailserver`, `lhgi`, `flask-controller-proxy`, `bloomcap`

This handles container crashes automatically. No action needed.

#### Step 3: Home Server Backup via rsync Pull (Day 2, 3–4 hours)

**Strategy:** Cron job on home Linux system / Raspberry Pi pulls critical data from VPS via SSH nightly.

**Why pull (not push from VPS):**
- No need to expose home IP or SSH to the internet
- Home system initiates outbound connection — more secure
- Works with dynamic home IP

**Critical data NOT in git (must be backed up):**
- `config/opendkim/` — DKIM private keys **(#1 priority: losing this requires DNS TXT update)**
- `config/postfix-accounts.cf` — email account definitions
- `mailserver.env` — mail server config
- All `.env` files (MinipassWebSite, app, Marketing, etc.)
- SQLite databases: `customers.db`, `minipass.db` (multiple), `monitoring.db`
- `maildata/` (~29MB) — mail message archive
- `mailstate/` (~1.9MB) — postfix queues/state
- `docker-compose.yml` and `nginx/` config

**NOT critical to backup (regeneratable):**
- `certs/` — Let's Encrypt renews automatically
- `venv/` — `pip install` regenerates
- Application code — in git

**Script:** `scripts/backup_pull.sh` (runs on home system, see file for full implementation)

**Retention:** 30 daily snapshots (rolling). Total storage: ~1–2 GB per backup × 30 = ~30–60 GB max.

**Cron setup on home system:**
```bash
# Add to home crontab (crontab -e):
0 2 * * * /path/to/scripts/backup_pull.sh >> ~/backups/minipass/backup.log 2>&1
```

#### Step 4: Recovery Runbook (Day 3, 2 hours)

**Document:** `docs/RECOVERY_RUNBOOK.md` — covers three scenarios:

| Scenario | Recovery Time |
|----------|---------------|
| Container crash (auto-recovered) | 0–2 min |
| VPS running, data corrupted | 30–45 min |
| VPS completely gone (nuclear) | 45–90 min |
| DKIM key lost (no backup) | 60–90 min + DNS wait |

---

### Phase 6a — Implementation Checklist

- [ ] UptimeRobot setup (30 min) — monitor ports 25, 587, 993 + HTTPS — FREE
- [x] Docker restart policies — already `restart: always` on all services
- [ ] Create `scripts/backup_pull.sh` and test from home system (2–3 hours)
- [ ] Set up home cron for nightly backup pull (15 min)
- [ ] Register healthchecks.io → add ping to backup script (30 min)
- [ ] Create `docs/RECOVERY_RUNBOOK.md` (2 hours)
- [ ] Run first backup, verify DKIM keys + databases present in `~/backups/minipass/`

---

### Phase 6b — On-Demand VPS Provisioning (Full)

**Goal:** When disaster strikes, provision a new VPS and restore to full operation in under 30 minutes. No VPS running 24/7 — only spin up when needed.

**Why not Docker Swarm?**
Mail servers are stateful and don't cluster well. Running active/active Postfix creates split-brain risks (duplicate emails, queue corruption). Warm standby with failover is the industry-standard approach for mail at this scale.

**Why not an always-on $11 CAD/month standby?**
For 62 emails/day of transactional mail, Postfix queues for 10 days. A 1–2 hour recovery window with no ongoing cost is a better trade-off than $132 CAD/year for rare failure scenarios.

#### Component 1: Ansible Provisioning Playbook

**File:** `deploy/ansible/site.yml`

Playbook that provisions a fresh VPS to production-ready state:
1. Install Docker + docker-compose
2. Clone git repo
3. Restore from local backup (rsync from home server)
4. Set environment files
5. Start all services (`docker-compose up -d`)
6. Verify mail flow with test email

**Execution:** `ansible-playbook -i NEW_VPS_IP, deploy/ansible/site.yml`
**Time:** ~20–25 minutes from zero to fully running

#### Component 2: Uptime Kuma (Self-Hosted Monitoring)

Open source: https://github.com/louislam/uptime-kuma

Run on Raspberry Pi or home Linux server. Monitors all services (HTTPS, SMTP ports, ping). Notifications via Telegram, Discord, Slack, email, or SMS. Keeps alerting even when the primary VPS is dead.

```bash
# Deploy on Raspberry Pi or home server:
docker run -d --restart=always -p 3001:3001 \
  -v uptime-kuma:/app/data \
  --name uptime-kuma louislam/uptime-kuma:1
```

Complements UptimeRobot: Uptime Kuma provides the self-hosted dashboard; UptimeRobot provides external backup alerting.

#### Component 3: DNS Failover

**Short-term (Phase 6a):** Manual DNS update at domain.com admin panel — 5 minutes, propagates based on TTL.

**Optimization:** Lower TTL on `minipass.me` A record and MX record from 3600 → 300 seconds before any planned maintenance.

**Long-term option:** Migrate DNS to Cloudflare (free) for API-based automated MX/A record updates.

**File:** `scripts/failover.sh` — documents the manual failover procedure (can be automated with Cloudflare API).

#### Recovery Time Targets

| Scenario | Phase 6a | Phase 6b |
|----------|----------|----------|
| Container crash | ~2 min (auto) | ~2 min (auto) |
| Data corruption | 30–45 min | 15–20 min (Ansible) |
| VPS completely gone | 45–90 min | 25–35 min (Ansible + restore) |
| DKIM key lost | 60–90 min | 30 min (pre-documented) |

---

### Phase 6b — Implementation Checklist

- [ ] Set up Uptime Kuma on Raspberry Pi/home server
- [ ] Create `deploy/ansible/site.yml` provisioning playbook
- [ ] Write and test `scripts/failover.sh`
- [ ] Consider Cloudflare DNS migration for API-based failover
- [ ] Fire drill: simulate VPS failure, restore from backup to a test VPS, time it

---

### Files Added / Modified

| File | Purpose |
|------|---------|
| `scripts/backup_pull.sh` | Runs on home server — nightly rsync pull of critical VPS data |
| `scripts/restore.sh` | Runs on VPS (or new VPS) — restores from home backup + starts services |
| `docs/RECOVERY_RUNBOOK.md` | Step-by-step recovery guide for each failure scenario |
| `deploy/ansible/site.yml` | (Phase 6b) Ansible playbook for zero-to-running VPS provisioning |
| `scripts/failover.sh` | (Phase 6b) Failover procedure (manual steps + Cloudflare API option) |

### Verification

1. **Backup test**: Run `backup_pull.sh` from home system, verify all files arrive in `~/backups/minipass/`
2. **DKIM integrity**: `ls -la ~/backups/minipass/latest/config/opendkim/` — confirm keys present
3. **Restore test** (non-destructive): Copy backup to `/tmp/restore-test/` on test VPS, run `docker-compose up`, confirm services start
4. **Alert test**: Stop `nginx-proxy` container, verify UptimeRobot fires within 5 minutes
5. **Heartbeat test**: Skip the daily backup ping, verify healthchecks.io fires an alert

---

## Files Reference

| File | Purpose |
|------|---------|
| `scripts/fetch_dmarc_reports.py` | IMAP auto-fetch DMARC reports |
| `scripts/analyze_dmarc_failures.py` | Parse and analyze failures |
| `scripts/email_monitor_to_db.py` | SQLite metrics persistence (VPS) — UNIQUE + INSERT OR IGNORE fixed; `from=<>` → `'<>'` fix applied |
| `scripts/email_health_check.py` | Delivery health monitoring |
| `scripts/verify_email_rfc_compliance.sh` | DNS/RFC verification |
| `app/utils.py` | Customer app email sending (RFC compliant) |
| `MinipassWebSite/utils/email_helpers.py` | Platform email sending (RFC compliant) |
| `MinipassWebSite/app.py` | Main Flask app — `classify_error()` helper, `/sender-detail` route, failures enrichment |
| `MinipassWebSite/templates/admin/admin_base.html` | Shared DaisyUI 4 sidebar layout for all admin pages |
| `MinipassWebSite/templates/admin/mail_dashboard.html` | Email analytics dashboard (Phase 4 UI) |
| `MinipassWebSite/templates/admin/tools.html` | Customers page (extends admin_base) |
| `MinipassWebSite/templates/admin/promo_codes.html` | Promo codes page (extends admin_base) |
| `email_monitoring/monitoring.db` | SQLite analytics DB — 8 days data, read-only from dashboard |
| `docs/VPS_ARCHITECTURE_DIAGRAM.md` | Full VPS/container architecture |

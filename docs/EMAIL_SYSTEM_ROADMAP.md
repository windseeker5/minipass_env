# Minipass Email System — Master Roadmap

**Last Updated:** February 16, 2026
**Branch:** `feature/email-infrastructure-overhaul` (merged to main: commit `92b0813`)

---

## Current Status: Phase 1 Complete ✅

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

## Phase 3 — Email Size Optimization (Deferred)

**Trigger:** Only needed if Gmail blocks resume or email size becomes an issue.

Current email size: ~32KB–105KB (inline base64 images)
Target: ~8KB (75% reduction via hosted images)

**Plan:** Host images on CDN/static server, replace base64 inline images with HTTP URLs in email templates.
**Effort:** ~6–8 hours

---

## Phase 4 — Email Analytics Dashboard (Deferred, Month 2+)



**Trigger:** When operational visibility becomes a priority.

**Plan:** Simple Flask dashboard on top of `email_monitor_to_db.py` SQLite data showing:
- Daily/weekly inbound/outbound volume per sender/domain
- Authentication pass rate trends
- Alerts for volume spikes

**Effort:** ~4–6 hours

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

# 📧 MINIPASS EMAIL TRACKING SOLUTIONS - GITHUB ALTERNATIVES PLAN

## 🎯 OBJECTIVE
Create a persistent email volume tracking system that:
- Tracks inbound/outbound emails per user per domain
- Maintains historical data even after log rotation
- Provides simple dashboard/reporting
- Runs daily/weekly to capture data before logs are rotated

## 🔍 RESEARCH FINDINGS: TOP GITHUB SOLUTIONS

### 1. ⭐ **MailLogSentinel** (BEST FIT)
**Repository:** https://github.com/monozoide/MailLogSentinel
**Status:** Active, Recent Updates

**Key Features:**
- 🔄 Real-time log monitoring (tails logs incrementally)
- 📊 Exports to CSV and SQLite database
- ⚡ Lightweight systemd service
- 📧 Daily email summaries
- 🌍 IP geolocation tracking

**What it tracks:**
- Authentication failures (security focus)
- Failed login attempts with geolocation
- Event normalization to structured CSV

**Pros:** ✅
- SQLite export capability
- Real-time monitoring
- Designed for systemd (modern)
- Recent updates (2023-2024)

**Cons:** ❌
- Focuses mainly on security/auth failures
- May need modification for volume tracking
- Requires Python 3.10+

### 2. 📈 **SendmailAnalyzer** (COMPREHENSIVE)
**Repository:** https://github.com/darold/sendmailanalyzer
**Status:** Mature, Stable

**Key Features:**
- 📊 Full Postfix support (v7.0+)
- 📁 Flat file database with time hierarchy
- 🌐 HTML reports with graphs
- 👥 Per-domain and per-mailbox reporting
- 📤 Tracks inbound/outbound volumes

**What it tracks:**
- Inbound/outbound message counts
- Sender/recipient domains and addresses
- Spam/virus statistics
- SMTP authentication data
- Top senders/recipients

**Pros:** ✅
- Exactly matches your requirements
- Per-user and per-domain tracking
- Time-based data storage
- Proven solution (mature)

**Cons:** ❌
- Uses flat files, not SQLite
- More complex setup
- HTML-focused (not API-friendly)

### 3. 🔧 **maillogger** (SIMPLE)
**Repository:** https://github.com/homoluctus/maillogger
**Status:** Simple, Focused

**Key Features:**
- 📄 Outputs CSV, TSV, JSON
- 🗜️ Optional gzip compression
- 🗃️ MySQL schema examples
- ⚡ Lightweight and fast

**What it tracks:**
- Basic Postfix log events
- Customizable output formats

**Pros:** ✅
- Simple to use
- Multiple output formats
- Can be integrated with SQLite

**Cons:** ❌
- Basic functionality
- No built-in persistence
- Requires custom database setup

### 4. 📋 **pflogsumm** (STANDARD)
**Status:** Industry Standard

**Key Features:**
- 📊 Postfix log summarizer
- 📧 Daily/weekly/monthly reports
- 👑 Most widely used

**What it tracks:**
- Email traffic patterns
- Top senders/recipients
- SMTP connection statistics

**Pros:** ✅
- Industry standard
- Proven reliability
- Available on most systems

**Cons:** ❌
- No database storage
- Report-only (no persistent data)
- Perl-based (older technology)

## 🏆 RECOMMENDATION MATRIX

| Solution | Data Persistence | User Tracking | Domain Tracking | Setup Complexity | Real-time | Best For |
|----------|-----------------|---------------|-----------------|------------------|-----------|-----------|
| **MailLogSentinel** | SQLite ⭐ | ⚠️ Limited | ⚠️ Limited | Medium | Yes ⭐ | Security + Basic Volume |
| **SendmailAnalyzer** | Flat Files | Yes ⭐ | Yes ⭐ | High | No | Complete Analytics |
| **maillogger** | Custom | Basic | Basic | Low ⭐ | No | Simple Integration |
| **pflogsumm** | None | Yes | Yes | Low ⭐ | No | Quick Reports |

## 🎯 CUSTOM HYBRID APPROACH (RECOMMENDED)

Based on your needs, I recommend a **custom solution** that combines the best approaches:

### Phase 1: Enhanced Current Script
Improve our existing `email_volume_analysis.py`:
- Add SQLite database storage
- Run daily via cron to capture data before log rotation
- Simple schema: `emails(date, from_user, to_domain, email_type, count)`

### Phase 2: Real-time Monitoring
Add log tailing capability:
- Monitor live logs like MailLogSentinel
- Immediate data capture (no data loss)
- Simple alerting for volume spikes

### Phase 3: Dashboard
Simple web dashboard:
- Flask app showing daily/weekly/monthly volumes
- Per-user and per-domain charts
- Export capabilities

## 📋 IMPLEMENTATION PLAN

### Option A: Use SendmailAnalyzer (Fastest)
```bash
# Install SendmailAnalyzer
git clone https://github.com/darold/sendmailanalyzer
cd sendmailanalyzer
./configure
make install

# Configure for your logs
sendmailanalyzer --help
```

**Pros:** Complete solution, proven
**Cons:** Complex configuration, flat files

### Option B: Custom SQLite Solution (Recommended)
```python
# Enhanced email_volume_analysis.py with:
1. SQLite database storage
2. Incremental processing (only new logs)
3. Daily cron job
4. Simple web dashboard
```

**Pros:** Tailored to your needs, SQLite storage, simple
**Cons:** Custom development required

### Option C: MailLogSentinel + Modifications
```bash
# Install MailLogSentinel and modify for volume tracking
git clone https://github.com/monozoide/MailLogSentinel
# Modify to track email volumes instead of just auth failures
```

**Pros:** Real-time monitoring, SQLite built-in
**Cons:** Requires modification

## 💡 IMMEDIATE NEXT STEPS

1. **Test SendmailAnalyzer** (30 minutes)
   - Quick installation test
   - See if output meets your needs

2. **Enhance Current Script** (2 hours)
   - Add SQLite storage to `email_volume_analysis.py`
   - Create daily cron job
   - Test data persistence

3. **Evaluate Results** (1 week)
   - Compare approaches
   - Decide on final implementation

## 📁 FILE STRUCTURE RECOMMENDATION

```
/home/kdresdell/minipass_env/
├── email_tracking/
│   ├── email_tracker.py          # Enhanced tracker with SQLite
│   ├── email_tracker.db          # SQLite database
│   ├── daily_capture.sh          # Cron script
│   ├── dashboard.py              # Simple Flask dashboard
│   └── config.yml                # Configuration
```

This preserves all your email data permanently while being simple to maintain!
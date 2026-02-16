# Minipass Email Infrastructure Overhaul Plan

**Date:** February 16, 2026
**Version:** 2.0 - RFC 5322 Compliant Edition
**Status:** Planning Phase
**Priority:** CRITICAL - Business Continuity Issue

---

## Executive Summary

This comprehensive plan addresses Gmail blocking issues and ensures full RFC compliance for the Minipass email infrastructure. The plan identifies **7 critical issues** including missing Date header and oversized emails, and provides a **5-phase implementation roadmap** with **zero additional cost** for Phases 1-4.

**Key Findings:**
- 🚨 Missing RFC 5322 required Date header
- 🚨 Email size 32KB-105KB (should be <15KB)
- ⚠️ Missing charset declaration (UTF-8 for French content)
- ⚠️ No Return-Path header
- ⚠️ DMARC/SPF/DKIM verification needed

**Expected Outcome:** Zero Gmail blocks, 99%+ delivery rate, full RFC compliance

---

## Table of Contents

1. [Context](#context)
2. [Root Cause Analysis](#root-cause-analysis)
3. [RFC 5322 Compliance Audit](#rfc-5322-compliance-audit)
4. [Email Deliverability Best Practices](#email-deliverability-best-practices)
5. [Implementation Plan](#implementation-plan)
6. [Testing & Verification](#testing--verification-plan)
7. [Success Metrics](#success-metrics)

---

## Context

Minipass is a SaaS platform where **email is the primary interface for end-users**. Unlike typical applications where users log into a web interface, Minipass end-users interact entirely through email notifications for:
- Registration confirmations
- Payment receipts
- Digital pass delivery
- Session redemption notifications
- Payment reminders
- Surveys

**The Problem:** Gmail has blocked the minipass.me domain twice in one week, with the most recent block triggered by a single 32KB registration email. This is a business-threatening issue that requires immediate understanding and long-term solutions.

**Current Stats:**
- 62 emails/day average (1,923 sent in 31 days)
- 74% of emails go to Gmail addresses (2,415/3,255)
- LHGI customer: 938 emails sent (89% of outbound traffic)
- Failure rate during Gmail block: 40.9%

---

## Root Cause Analysis

### CRITICAL Issue #1: Missing Date Header ⚠️

**RFC Violation:** RFC 5322 Section 3.6 - Date header is REQUIRED

**Location:** `/home/kdresdell/Documents/DEV/minipass_env/app/utils.py`, lines 3030-3062

**Problem:** The `send_email()` function never sets the `Date` header in outgoing emails.

**Evidence:**
```
# From GMAIL_BAN_CULPRIT_ANALYSIS.txt
Amavis Alert: BAD-HEADER-7 {RelayedOpenRelay,Quarantined} - Missing "Date" header
```

**Impact:**
- Triggers Amavis quarantine on mail servers
- Makes emails look suspicious to Gmail's spam filters
- RFC 5322 non-compliance causes immediate rejection by strict mail servers

**Fix Required:**
```python
from email.utils import formatdate

# Add after line 3058 (Message-ID)
msg["Date"] = formatdate(localtime=True)
```

### CRITICAL Issue #2: Excessive Email Size (32KB-105KB)

**Location:** `/home/kdresdell/Documents/DEV/minipass_env/app/templates/email_templates/compileEmailTemplate.py`

**Problem:** All images are Base64-encoded and embedded directly in emails, making them 32KB-105KB in size.

**Evidence:**
```
# From GMAIL_BAN_CULPRIT_ANALYSIS.txt
Registration email: 32,584 bytes (32KB)
Second email: 105KB
Base64-encoded PNG image: ~16KB when decoded
```

**Why This Is Bad:**
1. **Spam Signal:** Large HTML emails with embedded images look like bulk marketing to Gmail
2. **Slow Loading:** Email clients must decode Base64 images before rendering
3. **Bandwidth:** Wastes server/client bandwidth (Base64 encoding adds ~33% overhead)
4. **Storage:** Takes up more space in user mailboxes
5. **Mobile:** Slower to download on mobile connections

**Industry Standard:** Transactional emails should be <100KB total, preferably <50KB

### CRITICAL Issue #3: Missing Charset Declaration

**RFC Violation:** RFC 2047 - Character encoding must be specified for non-ASCII content

**Location:** `/home/kdresdell/Documents/DEV/minipass_env/app/utils.py`, lines 3103-3104

**Problem:** No explicit charset specified for MIME parts

**Current Code:**
```python
alt_part.attach(MIMEText(plain_text, "plain"))
alt_part.attach(MIMEText(final_html, "html"))
```

**Impact:**
- French accents (é, è, à, ô) may render as � symbols
- Email subjects like "Demande d'inscription reçue" may be corrupted
- Some email clients default to ASCII, breaking French content

**Fix Required:**
```python
alt_part.attach(MIMEText(plain_text, "plain", "utf-8"))
alt_part.attach(MIMEText(final_html, "html", "utf-8"))
```

### HIGH Priority Issue #4: Missing Return-Path Header

**RFC Reference:** RFC 5321 Section 4.4

**Location:** `/home/kdresdell/Documents/DEV/minipass_env/app/utils.py`, line 3036

**Problem:** No Return-Path header set for bounce handling

**Impact:**
- Bounced emails may not be properly tracked
- Some strict mail servers reject emails without Return-Path
- No centralized bounce management

**Fix Required:**
```python
# After From header
msg["Return-Path"] = from_email  # Or bounces@minipass.me
```

### MEDIUM Priority Issue #5: Missing Auto-Submitted Header

**RFC Reference:** RFC 3834 - Recommendations for Automatic Responses

**Location:** `/home/kdresdell/Documents/DEV/minipass_env/app/utils.py`, line 3054

**Problem:** No Auto-Submitted header to prevent auto-response loops

**Impact:**
- Vacation auto-responders may reply to your transactional emails
- Creates email loops (your email → vacation reply → your auto-reply → loop)
- Wastes bandwidth and looks unprofessional

**Fix Required:**
```python
# After X-Mailer header
msg["Auto-Submitted"] = "auto-generated"
```

### MEDIUM Priority Issue #6: Unverified SPF/DKIM/DMARC

**RFC References:**
- RFC 7208 (SPF)
- RFC 6376 (DKIM)
- RFC 7489 (DMARC)

**Problem:** Authentication mechanisms exist but not verified

**Impact:**
- DMARC failures cause emails to be quarantined/rejected
- SPF failures make emails look like spoofing attempts
- DKIM failures break sender reputation

**Fix Required:** Automated daily verification script

### LOW Priority Issue #7: Line Length Limits

**RFC Violation:** RFC 5322 Section 2.1.1 - Lines MUST be <998 characters

**Location:** HTML email templates

**Problem:** Possible long lines in HTML templates

**Impact:** Some older mail servers may reject emails with lines >998 chars

**Fix Required:** Verify and test

---

## RFC 5322 Compliance Audit

### What is RFC 5322?

**RFC 5322** - "Internet Message Format" (April 2008, obsoletes RFC 2822)

This is the **fundamental standard** that defines how email messages must be structured. Non-compliance can cause:
- Immediate rejection by mail servers
- Quarantine by spam filters
- Delivery failures
- Poor sender reputation

### Current Compliance Status

| Requirement | RFC Section | Status | Priority | Action Needed |
|-------------|-------------|--------|----------|---------------|
| **Date header** | 3.6 | ❌ MISSING | CRITICAL | Add formatdate() |
| **From header** | 3.6.2 | ✅ COMPLIANT | - | None |
| **To/Cc/Bcc header** | 3.6.3 | ✅ COMPLIANT | - | None |
| **Subject header** | 3.6.5 | ✅ COMPLIANT | - | None |
| **Message-ID** | 3.6.4 | ✅ COMPLIANT | - | None |
| **Character encoding** | RFC 2047 | ⚠️ IMPLICIT | HIGH | Make explicit UTF-8 |
| **Return-Path** | RFC 5321 | ❌ MISSING | HIGH | Add header |
| **Auto-Submitted** | RFC 3834 | ❌ MISSING | MEDIUM | Add header |
| **Line length <998** | 2.1.1 | ❓ UNKNOWN | LOW | Verify |
| **SPF record** | RFC 7208 | ✅ LIKELY | MEDIUM | Verify |
| **DKIM signature** | RFC 6376 | ✅ CONFIGURED | MEDIUM | Verify |
| **DMARC policy** | RFC 7489 | ❓ UNKNOWN | MEDIUM | Verify & setup |

### Related Email RFCs

**Complete RFC Compliance Checklist:**

#### Core Message Format
- ✅ **RFC 5322** - Internet Message Format (email structure)
- ⚠️ **RFC 2047** - Encoded-Word for non-ASCII headers
- ✅ **RFC 2045-2049** - MIME standards (multipart messages)
- ❌ **RFC 2183** - Content-Disposition (inline images)

#### Email Transmission
- ✅ **RFC 5321** - SMTP Protocol
- ❌ **RFC 3834** - Auto-Response Recommendations
- ✅ **RFC 6152** - SMTP 8BITMIME (UTF-8 support)

#### Email Authentication
- ❓ **RFC 7208** - SPF (Sender Policy Framework)
- ✅ **RFC 6376** - DKIM (DomainKeys Identified Mail)
- ❓ **RFC 7489** - DMARC (Authentication & Reporting)
- ✅ **RFC 5451** - Authentication-Results header

#### Best Practices
- ✅ **RFC 2919** - List-Id header (you have List-Unsubscribe)
- ✅ **RFC 8058** - List-Unsubscribe with One-Click
- ⚠️ **RFC 3461** - Delivery Status Notifications

---

## Email Deliverability Best Practices - Educational Overview

### 1. Transactional vs Marketing Emails

**Transactional Emails** (What Minipass Sends):
- Triggered by user actions (registration, payment, redemption)
- Expected by recipient
- Should be simple, fast, and reliable
- Low decoration, high information density
- **Best Practice:** Plain HTML with minimal styling, hosted images

**Marketing Emails** (What Minipass Does NOT Send):
- Promotional content
- Newsletters
- Bulk campaigns
- Heavy design, lots of images
- **Pattern:** Complex layouts, large embedded images, tracking pixels

**Gmail's Problem:** Minipass transactional emails currently LOOK like marketing emails due to:
- Large size (32KB+)
- Embedded Base64 images
- Complex HTML structure
- Late-night sending patterns

### 2. Hosted Images vs Embedded Images

#### Option A: Embedded Images (Current Approach) ❌

**How It Works:**
```html
<img src="cid:hero_new_pass">
<!-- Image attached as MIME part with Content-ID -->
```

**Pros:**
- Works offline (image travels with email)
- No external dependencies
- No tracking concerns

**Cons:**
- Makes emails HUGE (32KB-105KB)
- Spam filter red flag
- Slow to load/decode
- Wastes bandwidth
- Looks like bulk marketing

**When to Use:** Never for transactional emails in 2026. This was common in 2010-2015.

#### Option B: Hosted Images (Industry Standard) ✅

**How It Works:**
```html
<img src="https://cdn.minipass.me/email-assets/hero-signup.png">
<!-- Image loaded from web server -->
```

**Pros:**
- Tiny email size (5-15KB instead of 32KB+)
- Fast rendering
- Browser caching
- No spam signals
- Easy to update images without resending emails
- Transactional email standard

**Cons:**
- Requires external hosting
- Doesn't work offline (but who reads email offline in 2026?)
- Image blocking in some email clients (but default is "show images" now)

**Industry Consensus:** All modern transactional email services (SendGrid, Postmark, Mailgun, AWS SES) use hosted images exclusively.

#### Option C: Hybrid Approach (Recommended for Minipass)

**Strategy:**
- **Hero images:** Hosted on CDN (cdn.minipass.me or S3)
- **QR codes:** Inline Base64 (small ~2KB, needs to travel with email)
- **Logos:** Hosted on CDN
- **Icons:** Use Unicode emoji or hosted SVG

**Result:** Email size drops from 32KB to ~8KB (75% reduction)

### 3. Email Size Optimization Guidelines

**Industry Standards:**
- **Excellent:** <10KB
- **Good:** 10-25KB
- **Acceptable:** 25-50KB
- **Warning:** 50-100KB
- **Red Flag:** >100KB (spam territory)

**Minipass Current State:**
- Registration email: 32KB ⚠️
- Some emails: 105KB 🚨

**Target State:**
- All emails: <15KB ✅

### 4. Email Authentication (SPF, DKIM, DMARC)

#### SPF (Sender Policy Framework)
**What It Is:** DNS record listing which servers can send email from your domain

**Minipass Status:** ✅ Configured (based on docker-mailserver setup)

**Example SPF Record:**
```
v=spf1 mx ip4:138.199.152.128 ~all
```

**Why It Matters:** Prevents email spoofing, improves deliverability

**How to Verify:**
```bash
dig minipass.me TXT | grep "v=spf1"
```

#### DKIM (DomainKeys Identified Mail)
**What It Is:** Cryptographic signature proving email came from your server

**Minipass Status:** ✅ Configured (OpenDKIM in docker-mailserver)

**Location:** `/home/kdresdell/Documents/DEV/minipass_env/config/opendkim/`

**Why It Matters:** Gmail/Yahoo require DKIM for bulk senders (>5000 emails/day)

**How to Verify:**
```bash
dig mail._domainkey.minipass.me TXT
```

#### DMARC (Domain-based Message Authentication, Reporting and Conformance)
**What It Is:** Policy telling receivers what to do with unauthenticated emails

**Minipass Status:** ❓ Unknown (need to check DNS)

**Example DMARC Record:**
```
v=DMARC1; p=quarantine; rua=mailto:dmarc@minipass.me; ruf=mailto:dmarc@minipass.me; pct=100
```

**Why It Matters:**
- Provides DMARC reports (XML files) showing delivery issues
- Protects domain reputation
- Gmail requires DMARC for bulk senders

**How to Verify:**
```bash
dig _dmarc.minipass.me TXT
```

### 5. DMARC Reports Explained

#### What Are DMARC Reports?

DMARC reports are XML files sent by email receivers (Gmail, Yahoo, Outlook) to your specified `rua` email address, containing:
- **How many emails** were sent from your domain
- **Which IP addresses** sent them
- **SPF/DKIM results** (pass/fail)
- **Disposition** (none/quarantine/reject)
- **Reasons for failure**

#### Two Types of Reports:

**Aggregate Reports (RUA):**
- Sent daily by Gmail, Yahoo, Outlook
- XML format
- Statistics summary (volume, pass/fail rates)
- Helps identify deliverability issues

**Forensic Reports (RUF):**
- Sent immediately when authentication fails
- Contains email headers
- Helps debug specific failures

#### How to Read DMARC Reports:

**XML Structure:**
```xml
<feedback>
  <report_metadata>
    <org_name>google.com</org_name>
    <email>noreply-dmarc-support@google.com</email>
    <date_range>
      <begin>1707955200</begin>
      <end>1708041599</end>
    </date_range>
  </report_metadata>
  <policy_published>
    <domain>minipass.me</domain>
    <p>none</p>
  </policy_published>
  <record>
    <row>
      <source_ip>138.199.152.128</source_ip>
      <count>62</count>
      <policy_evaluated>
        <disposition>none</disposition>
        <dkim>pass</dkim>
        <spf>pass</spf>
      </policy_evaluated>
    </row>
  </record>
</feedback>
```

**Key Fields:**
- `source_ip`: Which server sent emails
- `count`: How many emails
- `dkim/spf`: Did authentication pass?
- `disposition`: What receiver did (none/quarantine/reject)

**What to Look For:**
- ❌ `dkim=fail` or `spf=fail` → Authentication broken
- ❌ `disposition=quarantine` → Emails going to spam
- ❌ `disposition=reject` → Emails blocked entirely
- ✅ `dkim=pass`, `spf=pass`, `disposition=none` → All good

---

## Comparison: Self-Hosted vs Transactional Email Services

### Option A: Keep Self-Hosted (docker-mailserver)

**Pros:**
- Full control
- No per-email costs
- No vendor lock-in
- Data sovereignty
- Already set up

**Cons:**
- Requires ongoing maintenance
- Deliverability depends on IP reputation
- Shared reputation risk (one customer affects all)
- No built-in analytics
- Manual DMARC report analysis
- Risk of Gmail blocks (as experienced)

**Best For:**
- Low volume (<1,000 emails/day)
- Privacy-focused
- Technical expertise available
- Willing to manage reputation

### Option B: Transactional Email Service

**Popular Services:**

#### SendGrid
- **Cost:** Free tier: 100 emails/day; $19.95/mo for 50k emails/mo
- **Pros:** Great deliverability, analytics dashboard, DMARC monitoring
- **Cons:** Expensive at scale

#### Postmark
- **Cost:** $15/mo for 10k emails
- **Pros:** Best deliverability reputation, transactional focus, excellent support
- **Cons:** More expensive than SendGrid

#### AWS SES (Simple Email Service)
- **Cost:** $0.10 per 1,000 emails
- **Pros:** Cheapest at scale, integrates with AWS
- **Cons:** Complex setup, reputation warming required

#### Mailgun
- **Cost:** $35/mo for 50k emails
- **Pros:** Developer-friendly API, good analytics
- **Cons:** Reputation issues in recent years

**Comparison Table:**

| Service | Cost (50k emails/mo) | Deliverability | Analytics | DMARC Reports | Setup Complexity |
|---------|---------------------|----------------|-----------|---------------|------------------|
| Self-Hosted | $0 | ⚠️ Risk | ❌ None | Manual | ⭐⭐⭐⭐⭐ |
| AWS SES | $5 | ✅ Good | Basic | Yes | ⭐⭐⭐⭐ |
| SendGrid | $20 | ✅✅ Excellent | ✅ Great | Yes | ⭐⭐ |
| Postmark | $75 | ✅✅✅ Best | ✅ Excellent | Yes | ⭐ |
| Mailgun | $35 | ✅ Good | ✅ Good | Yes | ⭐⭐ |

### Hybrid Approach (Recommended)

**Strategy:**
1. **Keep docker-mailserver** for:
   - Receiving emails (payment notifications from Interac)
   - Personal email (kdresdell@minipass.me, support@minipass.me)
   - Internal notifications

2. **Add transactional service** for:
   - Customer-facing emails (registration, payment confirmations, etc.)
   - High deliverability priority
   - Analytics and monitoring

**Cost Analysis (Based on Current Volume):**
- Current: 62 emails/day = ~1,860 emails/month
- AWS SES cost: $0.19/month
- SendGrid cost: Free tier covers it
- Postmark cost: $15/month

**Scaling (100 customers = 6,200 emails/day = 186k emails/month):**
- AWS SES: $18.60/month
- SendGrid: $89.95/month
- Postmark: $279/month

---

## Implementation Plan

### Phase 1: RFC 5322 Compliance & Emergency Fixes (This Week) 🚨

**Priority: CRITICAL - Prevent Future Gmail Blocks**

**Goal:** Achieve 100% RFC 5322 compliance and reduce email size

#### 1.1 Add Missing Date Header (5 minutes)

**File:** `/home/kdresdell/Documents/DEV/minipass_env/app/utils.py`

**Changes:**
```python
# Line 2850 - Update import
from email.utils import formatdate, formataddr, parsedate_to_datetime

# Line 3058 - After Message-ID, add Date header
msg["Message-ID"] = f"<{timestamp}@minipass.me>"
msg["Date"] = formatdate(localtime=True)  # ← ADD THIS LINE
```

**Why:**
- RFC 5322 REQUIRED header
- Prevents Amavis BAD-HEADER-7 quarantine
- Critical for email delivery

**Testing:**
```bash
# Send test email
curl -X POST http://localhost:5000/api/test-email \
  -H "Content-Type: application/json" \
  -d '{"to": "kdresdell@gmail.com"}'

# Check headers in Gmail
# Gmail → Show Original → Search for "Date:" header
# Should see: Date: Sun, 16 Feb 2026 14:23:45 -0500
```

#### 1.2 Add Explicit UTF-8 Charset (5 minutes)

**File:** `/home/kdresdell/Documents/DEV/minipass_env/app/utils.py`

**Changes:**
```python
# Line 3103-3104 - Add explicit UTF-8 charset
alt_part.attach(MIMEText(plain_text, "plain", "utf-8"))  # ← ADD "utf-8"
alt_part.attach(MIMEText(final_html, "html", "utf-8"))   # ← ADD "utf-8"
```

**Why:**
- RFC 2047 compliance for non-ASCII characters
- Ensures French accents (é, è, à, ô) display correctly
- Prevents � character corruption

**Testing:**
```bash
# Send email with French subject
# Subject: "Demande d'inscription reçue"
# Verify accents display correctly in Gmail
```

#### 1.3 Add Return-Path Header (2 minutes)

**File:** `/home/kdresdell/Documents/DEV/minipass_env/app/utils.py`

**Changes:**
```python
# Line 3036 - After From header, add Return-Path
msg["From"] = formataddr((sender_name, from_email))
msg["Return-Path"] = from_email  # ← ADD THIS LINE
# Or use dedicated bounce address: msg["Return-Path"] = "bounces@minipass.me"
```

**Why:**
- RFC 5321 requirement for bounce handling
- Some strict mail servers require it
- Proper bounce management

**Testing:**
```bash
# Check email headers in Gmail → Show Original
# Should see: Return-Path: <noreply@minipass.me>
```

#### 1.4 Add Auto-Submitted Header (2 minutes)

**File:** `/home/kdresdell/Documents/DEV/minipass_env/app/utils.py`

**Changes:**
```python
# Line 3054 - After X-Mailer header, add Auto-Submitted
msg["X-Mailer"] = "Minipass/1.0"
msg["Auto-Submitted"] = "auto-generated"  # ← ADD THIS LINE
```

**Why:**
- RFC 3834 best practice
- Prevents vacation auto-responders from replying
- Avoids email loops

**Testing:**
```bash
# Check email headers in Gmail → Show Original
# Should see: Auto-Submitted: auto-generated
```

#### 1.5 Reduce Email Size (Quick Win) (30 minutes)

**File:** `/home/kdresdell/Documents/DEV/minipass_env/app/templates/email_templates/compileEmailTemplate.py`

**Changes:**
```python
# Line 207-240 - Modify hero image processing
# Current: target_width = 600, quality = 85
# New: target_width = 400, quality = 70

def process_hero_image(image_path, padding=0):
    img = Image.open(image_path)

    # Reduce target width
    target_width = 400  # ← CHANGE FROM 600

    # ... existing crop logic ...

    # Increase compression
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG', optimize=True, quality=70)  # ← CHANGE FROM 85
    return img_byte_arr.getvalue()
```

**Result:** Should reduce email size from 32KB to ~20KB (still not ideal, but better)

**Testing:**
```bash
# Recompile templates
cd /home/kdresdell/Documents/DEV/minipass_env/app/templates/email_templates
python compileEmailTemplate.py signup --update-original
python compileEmailTemplate.py newPass --update-original
# ... repeat for all templates

# Send test email
# Check size: Gmail → Show Original → Look for total bytes
# Target: <20KB (down from 32KB)
```

#### 1.6 Create RFC Compliance Verification Script (30 minutes)

**Create:** `/home/kdresdell/Documents/DEV/minipass_env/scripts/verify_email_rfc_compliance.sh`

```bash
#!/bin/bash
# RFC 5322 & Email Authentication Verification Script

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        Minipass Email RFC Compliance Verification              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# SPF Check (RFC 7208)
echo "📋 [RFC 7208] SPF (Sender Policy Framework)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
SPF=$(dig minipass.me TXT +short | grep "v=spf1")
if [ -z "$SPF" ]; then
    echo "❌ FAIL: No SPF record found"
    echo "   Action: Add SPF record to DNS"
else
    echo "✅ PASS: $SPF"
fi
echo ""

# DKIM Check (RFC 6376)
echo "🔐 [RFC 6376] DKIM (DomainKeys Identified Mail)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
DKIM=$(dig mail._domainkey.minipass.me TXT +short)
if [ -z "$DKIM" ]; then
    echo "❌ FAIL: No DKIM record found"
    echo "   Action: Check OpenDKIM configuration"
else
    echo "✅ PASS: DKIM record exists"
    echo "   Record: ${DKIM:0:80}..."
fi
echo ""

# DMARC Check (RFC 7489)
echo "📊 [RFC 7489] DMARC (Authentication & Reporting)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
DMARC=$(dig _dmarc.minipass.me TXT +short)
if [ -z "$DMARC" ]; then
    echo "⚠️  WARN: No DMARC record found"
    echo "   Action: Create DMARC record with RUA email"
    echo "   Recommended: v=DMARC1; p=quarantine; rua=mailto:dmarc@minipass.me"
else
    echo "✅ PASS: $DMARC"
fi
echo ""

# MX Record Check
echo "📬 MX Records (Mail Servers)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
dig minipass.me MX +short
echo ""

# PTR Record Check (Reverse DNS)
echo "🔄 PTR Record (Reverse DNS)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
IP="138.199.152.128"  # Your mail server IP
PTR=$(dig -x $IP +short)
if [ -z "$PTR" ]; then
    echo "⚠️  WARN: No PTR record for $IP"
    echo "   Action: Contact VPS provider to set PTR record"
else
    echo "✅ PASS: $PTR"
fi
echo ""

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                      Verification Complete                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
```

**Make executable:**
```bash
chmod +x /home/kdresdell/Documents/DEV/minipass_env/scripts/verify_email_rfc_compliance.sh
```

**Usage:**
```bash
bash /home/kdresdell/Documents/DEV/minipass_env/scripts/verify_email_rfc_compliance.sh
```

#### 1.7 Create Email Health Check Script (30 minutes)

**Create:** `/home/kdresdell/Documents/DEV/minipass_env/scripts/email_health_check.py`

```python
#!/usr/bin/env python3
"""
Email Health Check Script
Monitors email delivery health and alerts on issues
"""

import sqlite3
from datetime import datetime, timedelta
import sys

# Database path
DB_PATH = "/home/kdresdell/Documents/DEV/minipass_env/app/instance/minipass.db"

def check_email_health():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get emails from last 24 hours
    yesterday = datetime.now() - timedelta(days=1)

    # Total emails sent
    cursor.execute("""
        SELECT COUNT(*) FROM email_log
        WHERE timestamp >= ?
    """, (yesterday,))
    total_sent = cursor.fetchone()[0]

    # Failed emails
    cursor.execute("""
        SELECT COUNT(*) FROM email_log
        WHERE timestamp >= ? AND result = 'FAILED'
    """, (yesterday,))
    failed_count = cursor.fetchone()[0]

    # Success rate
    success_rate = ((total_sent - failed_count) / total_sent * 100) if total_sent > 0 else 0

    # Gmail-specific failures
    cursor.execute("""
        SELECT COUNT(*) FROM email_log
        WHERE timestamp >= ?
        AND result = 'FAILED'
        AND to_email LIKE '%@gmail.com'
    """, (yesterday,))
    gmail_failures = cursor.fetchone()[0]

    print("╔════════════════════════════════════════════════════════════════╗")
    print("║          Minipass Email Health Report (24 hours)              ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print(f"\n📊 Total Emails Sent: {total_sent}")
    print(f"✅ Successfully Delivered: {total_sent - failed_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"📈 Success Rate: {success_rate:.1f}%")
    print(f"🎯 Gmail Failures: {gmail_failures}")

    # Alert conditions
    alerts = []
    if success_rate < 95:
        alerts.append(f"⚠️  Low success rate: {success_rate:.1f}% (target: >95%)")

    if gmail_failures > 5:
        alerts.append(f"⚠️  High Gmail failure count: {gmail_failures} (investigate!)")

    if total_sent == 0:
        alerts.append("⚠️  No emails sent in last 24 hours (expected?)")

    if alerts:
        print("\n🚨 ALERTS:")
        for alert in alerts:
            print(f"   {alert}")
        sys.exit(1)  # Non-zero exit for monitoring
    else:
        print("\n✅ All systems healthy!")
        sys.exit(0)

    conn.close()

if __name__ == "__main__":
    check_email_health()
```

**Make executable:**
```bash
chmod +x /home/kdresdell/Documents/DEV/minipass_env/scripts/email_health_check.py
```

**Add to cron (daily check at 9 AM):**
```bash
0 9 * * * /home/kdresdell/Documents/DEV/minipass_env/venv/bin/python \
          /home/kdresdell/Documents/DEV/minipass_env/scripts/email_health_check.py
```

#### Phase 1 Summary

**Files Modified:**
1. `app/utils.py` - 4 new header lines added
2. `templates/email_templates/compileEmailTemplate.py` - Image compression increased

**Files Created:**
1. `scripts/verify_email_rfc_compliance.sh` - DNS verification
2. `scripts/email_health_check.py` - Daily monitoring

**Expected Results:**
- ✅ 100% RFC 5322 compliant
- ✅ Email size reduced to ~20KB
- ✅ All authentication verified
- ✅ Daily health monitoring active

**Time Required:** 2-3 hours total

---

### Phase 2: Hosted Images Implementation (Week 2) ✅

**Priority: HIGH - Sustainable Fix**

**Goal:** Reduce email size from 32KB to <10KB by hosting images externally

#### 2.1 Set Up Image Hosting (1 hour)

**Option A: Use Existing Web Server (Recommended)**

**Steps:**
```bash
# 1. Create email-assets directory
mkdir -p /home/kdresdell/Documents/DEV/minipass_env/app/static/email-assets

# 2. Copy all hero images from compiled templates
cd /home/kdresdell/Documents/DEV/minipass_env/app/templates/email_templates

# Extract images from inline_images.json and save as PNG files
# This requires a small Python script
```

**Create extraction script:** `scripts/extract_template_images.py`

```python
#!/usr/bin/env python3
"""Extract hero images from compiled templates"""

import json
import base64
import os

templates = ['signup', 'newPass', 'paymentReceived', 'redeemPass', 'latePayment', 'survey_invitation']
output_dir = '/home/kdresdell/Documents/DEV/minipass_env/app/static/email-assets'

os.makedirs(output_dir, exist_ok=True)

for template in templates:
    json_path = f'{template}_compiled/inline_images.json'

    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            images = json.load(f)

        # Find hero image key
        hero_keys = {
            'signup': 'hero_signup',
            'newPass': 'hero_new_pass',
            'paymentReceived': 'currency-dollar',
            'redeemPass': 'hand-rock',
            'latePayment': 'thumb-down',
            'survey_invitation': 'sondage'
        }

        hero_key = hero_keys.get(template)
        if hero_key and hero_key in images:
            # Decode base64 and save
            img_data = base64.b64decode(images[hero_key])
            output_file = f'{output_dir}/hero_{template}.png'

            with open(output_file, 'wb') as f:
                f.write(img_data)

            print(f'✅ Extracted {template}: {output_file}')
```

**Run:**
```bash
cd /home/kdresdell/Documents/DEV/minipass_env/app/templates/email_templates
python ../scripts/extract_template_images.py
```

**Configure Nginx to serve static files:**

Check if already configured at `/etc/nginx/sites-available/minipass`:
```nginx
location /email-assets/ {
    alias /home/kdresdell/Documents/DEV/minipass_env/app/static/email-assets/;
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

**Test:**
```bash
curl https://minipass.me/email-assets/hero_signup.png
# Should return 200 OK with PNG data
```

**Option B: CloudFlare CDN (Later Enhancement)**

- Free tier available
- Better performance globally
- Automatic caching
- Can migrate after Option A works

**Option C: AWS S3 + CloudFront**

- Professional setup
- ~$1/month
- Best performance
- Overkill for current volume

#### 2.2 Modify Email Templates (2-3 hours)

**For each template, update HTML to use hosted images:**

**File:** `/home/kdresdell/Documents/DEV/minipass_env/app/templates/email_templates/signup/index.html`

**BEFORE:**
```html
<img src="cid:hero_signup" alt="Welcome">
```

**AFTER:**
```html
<img src="https://minipass.me/email-assets/hero_signup.png" alt="Welcome">
```

**Keep Embedded (Important!):**
```html
<!-- QR codes must stay embedded (small size, need to work offline) -->
<img src="cid:qr_code" alt="QR Code">
```

**Templates to modify:**
1. `signup/index.html`
2. `newPass/index.html`
3. `paymentReceived/index.html`
4. `redeemPass/index.html`
5. `latePayment/index.html`
6. `survey_invitation/index.html`

**After modifications, recompile:**
```bash
cd /home/kdresdell/Documents/DEV/minipass_env/app/templates/email_templates

for template in signup newPass paymentReceived redeemPass latePayment survey_invitation; do
    python compileEmailTemplate.py "$template" --update-original
done
```

#### 2.3 Add Hosted Images Mode Flag (1 hour)

**File:** `/home/kdresdell/Documents/DEV/minipass_env/app/utils.py`

**Changes:**
```python
# Line 2844 - Add parameter with default True (hosted mode)
def send_email(subject, to_email, template_name=None, context=None,
               inline_images=None, html_body=None, timestamp_override=None,
               email_config=None, use_hosted_images=True,  # ← ADD THIS
               user=None, activity=None):

    # ... existing code ...

    # Line 3107 - Modify inline image attachment logic
    for cid, img_data in inline_images.items():
        if img_data:
            # Only attach if NOT using hosted images, OR if it's a QR code
            if not use_hosted_images or cid.startswith('qr_'):
                try:
                    part = MIMEImage(img_data)
                    part.add_header("Content-ID", f"<{cid}>")
                    part.add_header("Content-Disposition", "inline")
                    msg.attach(part)
                except Exception as e:
                    logging.error(f"❌ Image embed error for {cid}: {e}")
```

**Rollout Strategy:**

**Week 1 (Testing):**
```python
# Default to embedded mode for production
use_hosted_images=False
```

**Week 2 (Gradual Rollout):**
```python
# Test with 10% of emails
import random
use_hosted_images = random.random() < 0.1  # 10% hosted
```

**Week 3 (Full Deployment):**
```python
# Default to hosted mode
use_hosted_images=True
```

#### 2.4 Testing & Validation (2 hours)

**Test Checklist:**

1. **Send test emails:**
```python
# Test both modes
send_email(subject="Test Hosted", ..., use_hosted_images=True)
send_email(subject="Test Embedded", ..., use_hosted_images=False)
```

2. **Check email size:**
```bash
# Gmail → Show Original → Check size
# Hosted mode: Should be <10KB
# Embedded mode: ~20-32KB (baseline)
```

3. **Verify images display:**
- Gmail web
- Gmail mobile app
- Outlook web
- Apple Mail
- Yahoo Mail

4. **Check accessibility:**
```bash
# Test image URLs are public
curl https://minipass.me/email-assets/hero_signup.png
```

5. **Performance test:**
```bash
# Measure load time
time curl -o /dev/null https://minipass.me/email-assets/hero_signup.png
# Should be <100ms
```

#### Phase 2 Summary

**Expected Results:**
- ✅ Email size reduced from 32KB to ~8KB (75% reduction)
- ✅ Faster email rendering
- ✅ Lower bandwidth usage
- ✅ No spam signals from large attachments
- ✅ Backward compatibility maintained

**Time Required:** 6-8 hours total

---

### Phase 3: DMARC Report Automation & Monitoring (Week 3-4) 📊

**Priority: MEDIUM - Learn from Failures**

**Goal:** Automate collection and analysis of DMARC reports to continuously improve deliverability

#### 3.1 Verify DMARC Configuration (30 minutes)

**Run RFC compliance script:**
```bash
bash /home/kdresdell/Documents/DEV/minipass_env/scripts/verify_email_rfc_compliance.sh
```

**If DMARC record missing, create one:**

**Add to DNS (via CloudFlare, registrar, or DNS provider):**
```
Record Type: TXT
Name: _dmarc.minipass.me
Value: v=DMARC1; p=quarantine; rua=mailto:dmarc@minipass.me; ruf=mailto:dmarc@minipass.me; pct=100; adkim=r; aspf=r
```

**Field Explanations:**
- `v=DMARC1` - Version
- `p=quarantine` - Policy (quarantine failed emails, don't reject outright)
- `rua=mailto:dmarc@minipass.me` - Aggregate report email
- `ruf=mailto:dmarc@minipass.me` - Forensic report email
- `pct=100` - Apply to 100% of emails
- `adkim=r` - Relaxed DKIM alignment
- `aspf=r` - Relaxed SPF alignment

**Create dmarc@minipass.me mailbox:**
```bash
# Use your mail_manager.py tool
python /home/kdresdell/Documents/DEV/minipass_env/mail_manager.py create-user dmarc@minipass.me
```

#### 3.2 DMARC Report Fetcher Script (3 hours)

**Create:** `/home/kdresdell/Documents/DEV/minipass_env/scripts/fetch_dmarc_reports.py`

```python
#!/usr/bin/env python3
"""
DMARC Report Fetcher & Parser
Connects to dmarc@minipass.me mailbox and parses DMARC XML reports
"""

import imaplib
import email
import xml.etree.ElementTree as ET
import sqlite3
import gzip
import io
from datetime import datetime
from email import policy

# Configuration
IMAP_SERVER = "mail.minipass.me"
IMAP_PORT = 993
EMAIL_USER = "dmarc@minipass.me"
EMAIL_PASS = "your_password_here"  # TODO: Use environment variable or keyring
DB_PATH = "/home/kdresdell/Documents/DEV/minipass_env/data/dmarc_reports.db"

def init_database():
    """Create DMARC reports database if not exists"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dmarc_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id TEXT UNIQUE,
            org_name TEXT,
            email TEXT,
            date_begin INTEGER,
            date_end INTEGER,
            domain TEXT,
            policy TEXT,
            source_ip TEXT,
            email_count INTEGER,
            dkim_result TEXT,
            spf_result TEXT,
            disposition TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

def connect_imap():
    """Connect to IMAP server and login"""
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(EMAIL_USER, EMAIL_PASS)
    return mail

def parse_dmarc_xml(xml_content):
    """Parse DMARC XML report"""
    try:
        root = ET.fromstring(xml_content)

        # Extract report metadata
        report_id = root.find('.//report_id').text
        org_name = root.find('.//org_name').text
        email_addr = root.find('.//email').text
        date_begin = int(root.find('.//date_range/begin').text)
        date_end = int(root.find('.//date_range/end').text)

        # Extract policy
        domain = root.find('.//policy_published/domain').text
        policy = root.find('.//policy_published/p').text

        # Extract records
        records = []
        for record in root.findall('.//record'):
            source_ip = record.find('.//source_ip').text
            count = int(record.find('.//count').text)

            policy_eval = record.find('.//policy_evaluated')
            disposition = policy_eval.find('disposition').text
            dkim = policy_eval.find('dkim').text
            spf = policy_eval.find('spf').text

            records.append({
                'report_id': report_id,
                'org_name': org_name,
                'email': email_addr,
                'date_begin': date_begin,
                'date_end': date_end,
                'domain': domain,
                'policy': policy,
                'source_ip': source_ip,
                'email_count': count,
                'dkim_result': dkim,
                'spf_result': spf,
                'disposition': disposition
            })

        return records

    except Exception as e:
        print(f"❌ Error parsing XML: {e}")
        return []

def store_reports(records):
    """Store parsed reports in database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for record in records:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO dmarc_reports
                (report_id, org_name, email, date_begin, date_end, domain, policy,
                 source_ip, email_count, dkim_result, spf_result, disposition)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record['report_id'], record['org_name'], record['email'],
                record['date_begin'], record['date_end'], record['domain'],
                record['policy'], record['source_ip'], record['email_count'],
                record['dkim_result'], record['spf_result'], record['disposition']
            ))
        except Exception as e:
            print(f"⚠️  Error storing record: {e}")

    conn.commit()
    conn.close()

def fetch_and_process():
    """Main function to fetch and process DMARC reports"""
    print("📧 Connecting to dmarc@minipass.me...")

    init_database()
    mail = connect_imap()
    mail.select('INBOX')

    # Search for DMARC report emails
    status, messages = mail.search(None, 'ALL')
    email_ids = messages[0].split()

    print(f"📬 Found {len(email_ids)} emails")

    total_reports = 0

    for email_id in email_ids:
        status, msg_data = mail.fetch(email_id, '(RFC822)')

        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1], policy=policy.default)

                # Check if it's a DMARC report
                if 'dmarc' not in msg.get('Subject', '').lower():
                    continue

                print(f"📊 Processing: {msg.get('Subject')}")

                # Process attachments
                for part in msg.walk():
                    if part.get_content_maintype() == 'multipart':
                        continue

                    filename = part.get_filename()
                    if not filename:
                        continue

                    # DMARC reports are usually .xml or .gz files
                    if filename.endswith('.gz'):
                        # Decompress gzip
                        compressed_data = part.get_payload(decode=True)
                        xml_content = gzip.decompress(compressed_data).decode('utf-8')
                    elif filename.endswith('.xml'):
                        xml_content = part.get_payload(decode=True).decode('utf-8')
                    else:
                        continue

                    # Parse and store
                    records = parse_dmarc_xml(xml_content)
                    if records:
                        store_reports(records)
                        total_reports += len(records)
                        print(f"   ✅ Stored {len(records)} records")

    mail.close()
    mail.logout()

    print(f"\n🎉 Complete! Processed {total_reports} total records")

if __name__ == "__main__":
    fetch_and_process()
```

**Make executable:**
```bash
chmod +x /home/kdresdell/Documents/DEV/minipass_env/scripts/fetch_dmarc_reports.py
```

**Add to cron (daily at 9 AM):**
```bash
0 9 * * * /home/kdresdell/Documents/DEV/minipass_env/venv/bin/python \
          /home/kdresdell/Documents/DEV/minipass_env/scripts/fetch_dmarc_reports.py >> \
          /home/kdresdell/Documents/DEV/minipass_env/logs/dmarc_fetch.log 2>&1
```

#### 3.3 DMARC Report Dashboard (4-6 hours)

**Create Flask route:** `/home/kdresdell/Documents/DEV/minipass_env/app/app.py`

```python
@app.route('/admin/dmarc-reports')
@admin_required
def dmarc_reports():
    """DMARC Reports Dashboard"""
    import sqlite3
    from datetime import datetime, timedelta

    db_path = "/home/kdresdell/Documents/DEV/minipass_env/data/dmarc_reports.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get date range filter
    days = request.args.get('days', 30, type=int)
    cutoff = int((datetime.now() - timedelta(days=days)).timestamp())

    # Summary statistics
    cursor.execute("""
        SELECT
            COUNT(DISTINCT report_id) as report_count,
            SUM(email_count) as total_emails,
            SUM(CASE WHEN dkim_result = 'pass' THEN email_count ELSE 0 END) as dkim_pass,
            SUM(CASE WHEN spf_result = 'pass' THEN email_count ELSE 0 END) as spf_pass,
            SUM(CASE WHEN disposition = 'quarantine' THEN email_count ELSE 0 END) as quarantined,
            SUM(CASE WHEN disposition = 'reject' THEN email_count ELSE 0 END) as rejected
        FROM dmarc_reports
        WHERE date_begin >= ?
    """, (cutoff,))

    summary = cursor.fetchone()

    # By organization (Gmail, Yahoo, etc.)
    cursor.execute("""
        SELECT
            org_name,
            SUM(email_count) as total,
            SUM(CASE WHEN dkim_result = 'pass' THEN email_count ELSE 0 END) as dkim_pass,
            SUM(CASE WHEN disposition = 'quarantine' THEN email_count ELSE 0 END) as quarantined
        FROM dmarc_reports
        WHERE date_begin >= ?
        GROUP BY org_name
        ORDER BY total DESC
    """, (cutoff,))

    by_org = cursor.fetchall()

    # Recent reports
    cursor.execute("""
        SELECT report_id, org_name, email, date_begin, date_end,
               source_ip, email_count, dkim_result, spf_result, disposition
        FROM dmarc_reports
        WHERE date_begin >= ?
        ORDER BY date_begin DESC
        LIMIT 100
    """, (cutoff,))

    recent_reports = cursor.fetchall()

    conn.close()

    return render_template('dmarc_reports.html',
                         summary=summary,
                         by_org=by_org,
                         recent_reports=recent_reports,
                         days=days)

@app.route('/admin/dmarc-reports/export')
@admin_required
def dmarc_reports_export():
    """Export DMARC reports as CSV"""
    import csv
    import io

    db_path = "/home/kdresdell/Documents/DEV/minipass_env/data/dmarc_reports.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM dmarc_reports ORDER BY date_begin DESC")

    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([desc[0] for desc in cursor.description])

    # Write data
    writer.writerows(cursor.fetchall())

    conn.close()

    # Return as downloadable file
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=dmarc_reports.csv'}
    )
```

**Create template:** `/home/kdresdell/Documents/DEV/minipass_env/app/templates/dmarc_reports.html`

```html
{% extends "base.html" %}

{% block title %}DMARC Reports{% endblock %}

{% block content %}
<div class="container-xl">
    <div class="page-header">
        <h1>📊 DMARC Reports Dashboard</h1>
        <p class="text-muted">Email authentication & delivery monitoring</p>
    </div>

    <!-- Summary Cards -->
    <div class="row row-cards mb-3">
        <div class="col-md-2">
            <div class="card">
                <div class="card-body">
                    <div class="h1 mb-0">{{ summary[0] }}</div>
                    <div class="text-muted">Reports</div>
                </div>
            </div>
        </div>
        <div class="col-md-2">
            <div class="card">
                <div class="card-body">
                    <div class="h1 mb-0">{{ summary[1] }}</div>
                    <div class="text-muted">Total Emails</div>
                </div>
            </div>
        </div>
        <div class="col-md-2">
            <div class="card">
                <div class="card-body">
                    <div class="h1 mb-0">{{ (summary[2] / summary[1] * 100) | round(1) }}%</div>
                    <div class="text-muted">DKIM Pass</div>
                </div>
            </div>
        </div>
        <div class="col-md-2">
            <div class="card">
                <div class="card-body">
                    <div class="h1 mb-0">{{ (summary[3] / summary[1] * 100) | round(1) }}%</div>
                    <div class="text-muted">SPF Pass</div>
                </div>
            </div>
        </div>
        <div class="col-md-2">
            <div class="card {% if summary[4] > 0 %}bg-yellow{% endif %}">
                <div class="card-body">
                    <div class="h1 mb-0">{{ summary[4] }}</div>
                    <div class="text-muted">Quarantined</div>
                </div>
            </div>
        </div>
        <div class="col-md-2">
            <div class="card {% if summary[5] > 0 %}bg-red{% endif %}">
                <div class="card-body">
                    <div class="h1 mb-0">{{ summary[5] }}</div>
                    <div class="text-muted">Rejected</div>
                </div>
            </div>
        </div>
    </div>

    <!-- By Organization -->
    <div class="card mb-3">
        <div class="card-header">
            <h3 class="card-title">Reports by Email Provider</h3>
        </div>
        <div class="card-body">
            <table class="table table-vcenter">
                <thead>
                    <tr>
                        <th>Provider</th>
                        <th>Total Emails</th>
                        <th>DKIM Pass Rate</th>
                        <th>Quarantined</th>
                    </tr>
                </thead>
                <tbody>
                    {% for org in by_org %}
                    <tr>
                        <td><strong>{{ org[0] }}</strong></td>
                        <td>{{ org[1] }}</td>
                        <td>
                            {% set pass_rate = (org[2] / org[1] * 100) | round(1) %}
                            <span class="badge bg-{{ 'green' if pass_rate >= 95 else 'yellow' if pass_rate >= 85 else 'red' }}">
                                {{ pass_rate }}%
                            </span>
                        </td>
                        <td>
                            {% if org[3] > 0 %}
                            <span class="badge bg-yellow">{{ org[3] }}</span>
                            {% else %}
                            <span class="text-muted">0</span>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Recent Reports Table -->
    <div class="card">
        <div class="card-header">
            <h3 class="card-title">Recent Reports</h3>
            <div class="card-actions">
                <a href="/admin/dmarc-reports/export" class="btn btn-primary">Export CSV</a>
            </div>
        </div>
        <div class="card-body">
            <table class="table table-vcenter">
                <thead>
                    <tr>
                        <th>Provider</th>
                        <th>Date Range</th>
                        <th>Source IP</th>
                        <th>Count</th>
                        <th>DKIM</th>
                        <th>SPF</th>
                        <th>Disposition</th>
                    </tr>
                </thead>
                <tbody>
                    {% for report in recent_reports %}
                    <tr>
                        <td>{{ report[1] }}</td>
                        <td>{{ report[3] | timestamp_to_date }} - {{ report[4] | timestamp_to_date }}</td>
                        <td><code>{{ report[5] }}</code></td>
                        <td>{{ report[6] }}</td>
                        <td><span class="badge bg-{{ 'green' if report[7] == 'pass' else 'red' }}">{{ report[7] }}</span></td>
                        <td><span class="badge bg-{{ 'green' if report[8] == 'pass' else 'red' }}">{{ report[8] }}</span></td>
                        <td><span class="badge bg-{{ 'gray' if report[9] == 'none' else 'yellow' if report[9] == 'quarantine' else 'red' }}">{{ report[9] }}</span></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}
```

**Add Jinja2 filter for timestamp conversion:**

```python
@app.template_filter('timestamp_to_date')
def timestamp_to_date(timestamp):
    return datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d')
```

#### Phase 3 Summary

**Expected Results:**
- ✅ DMARC reports collected daily
- ✅ Dashboard showing pass/fail rates
- ✅ Alert when quarantine rate >5%
- ✅ Historical tracking of email authentication

**Time Required:** 8-10 hours total

---

### Phase 4: Email Statistics & Monitoring (Month 2) 📈

**Priority: MEDIUM - Operational Visibility**

**Goal:** Comprehensive email performance monitoring and analytics

#### 4.1 Enhanced EmailLog Model (2 hours)

**File:** `/home/kdresdell/Documents/DEV/minipass_env/app/models.py`

**Add fields to EmailLog model:**
```python
class EmailLog(db.Model):
    __tablename__ = 'email_log'

    # Existing fields
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    to_email = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    pass_code = db.Column(db.String(16))
    template_name = db.Column(db.String(100))
    context_json = db.Column(db.Text)
    result = db.Column(db.String(50))
    error_message = db.Column(db.Text)

    # NEW FIELDS
    send_duration_ms = db.Column(db.Integer)  # How long SMTP send took
    email_size_bytes = db.Column(db.Integer)  # Total email size
    retry_count = db.Column(db.Integer, default=0)  # Number of retry attempts
    bounce_reason = db.Column(db.Text)  # Bounce/rejection reason
    recipient_domain = db.Column(db.String(100))  # gmail.com, yahoo.com, etc.
    smtp_code = db.Column(db.String(10))  # SMTP response code (250, 421, etc.)

    # Indexes for performance
    __table_args__ = (
        db.Index('idx_timestamp', 'timestamp'),
        db.Index('idx_result', 'result'),
        db.Index('idx_recipient_domain', 'recipient_domain'),
        db.Index('idx_template_name', 'template_name'),
    )
```

**Create migration:** `/home/kdresdell/Documents/DEV/minipass_env/migrations/add_email_log_fields.py`

```python
"""Add enhanced fields to email_log table"""

import sqlite3

DB_PATH = "/home/kdresdell/Documents/DEV/minipass_env/app/instance/minipass.db"

def upgrade():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Add new columns
    columns = [
        "ALTER TABLE email_log ADD COLUMN send_duration_ms INTEGER",
        "ALTER TABLE email_log ADD COLUMN email_size_bytes INTEGER",
        "ALTER TABLE email_log ADD COLUMN retry_count INTEGER DEFAULT 0",
        "ALTER TABLE email_log ADD COLUMN bounce_reason TEXT",
        "ALTER TABLE email_log ADD COLUMN recipient_domain VARCHAR(100)",
        "ALTER TABLE email_log ADD COLUMN smtp_code VARCHAR(10)",
    ]

    for col in columns:
        try:
            cursor.execute(col)
            print(f"✅ Added column: {col}")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print(f"⚠️  Column already exists: {col}")
            else:
                raise

    # Create indexes
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_timestamp ON email_log(timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_result ON email_log(result)",
        "CREATE INDEX IF NOT EXISTS idx_recipient_domain ON email_log(recipient_domain)",
        "CREATE INDEX IF NOT EXISTS idx_template_name ON email_log(template_name)",
    ]

    for idx in indexes:
        cursor.execute(idx)
        print(f"✅ Created index: {idx}")

    # Backfill recipient_domain from existing to_email
    cursor.execute("""
        UPDATE email_log
        SET recipient_domain = SUBSTR(to_email, INSTR(to_email, '@') + 1)
        WHERE recipient_domain IS NULL AND to_email LIKE '%@%'
    """)

    conn.commit()
    print(f"✅ Backfilled {cursor.rowcount} recipient_domain values")

    conn.close()

if __name__ == "__main__":
    upgrade()
```

**Run migration:**
```bash
python /home/kdresdell/Documents/DEV/minipass_env/migrations/add_email_log_fields.py
```

#### 4.2 Update send_email() to Track Metrics (1 hour)

**File:** `/home/kdresdell/Documents/DEV/minipass_env/app/utils.py`

**Add tracking around SMTP send:**
```python
# Line 3167 - Before sendmail, start timer
import time
send_start = time.time()

# Calculate email size
email_data = msg.as_string()
email_size = len(email_data.encode('utf-8'))

print(f"📤 Sending email from {from_email} to {to_email}...")
print(f"   Size: {email_size} bytes ({email_size/1024:.1f} KB)")

# Line 3174 - Send email
try:
    clean_mime_headers(msg)
    server.sendmail(from_email, [to_email], email_data)
    server.quit()

    send_duration = int((time.time() - send_start) * 1000)  # milliseconds

    # Extract recipient domain
    recipient_domain = to_email.split('@')[1] if '@' in to_email else None

    print(f"✅ EMAIL SENT SUCCESSFULLY to {to_email}")
    print(f"   Duration: {send_duration}ms")
    print(f"   Size: {email_size} bytes")
    print(f"   Domain: {recipient_domain}")

    # Log success with metrics
    if user:
        EmailLog.log_email(
            to_email=to_email,
            subject=subject,
            template_name=template_name,
            result='SENT',
            send_duration_ms=send_duration,
            email_size_bytes=email_size,
            recipient_domain=recipient_domain,
            smtp_code='250'
        )

except smtplib.SMTPException as e:
    send_duration = int((time.time() - send_start) * 1000)

    # Extract SMTP error code
    smtp_code = None
    error_str = str(e)
    if error_str.startswith('('):
        smtp_code = error_str.split(',')[0].strip('(')

    # Log failure with metrics
    if user:
        EmailLog.log_email(
            to_email=to_email,
            subject=subject,
            template_name=template_name,
            result='FAILED',
            error_message=error_str,
            send_duration_ms=send_duration,
            email_size_bytes=email_size,
            recipient_domain=recipient_domain,
            smtp_code=smtp_code
        )
```

#### 4.3 Email Statistics Dashboard (4-6 hours)

**Create route:** `/home/kdresdell/Documents/DEV/minipass_env/app/app.py`

```python
@app.route('/admin/email-statistics')
@admin_required
def email_statistics():
    """Email Statistics Dashboard"""
    from datetime import datetime, timedelta
    from sqlalchemy import func

    # Get date range filter
    days = request.args.get('days', 30, type=int)
    since = datetime.now() - timedelta(days=days)

    # Total emails
    total_sent = EmailLog.query.filter(EmailLog.timestamp >= since).count()

    # Success/failure counts
    success_count = EmailLog.query.filter(
        EmailLog.timestamp >= since,
        EmailLog.result == 'SENT'
    ).count()

    failed_count = total_sent - success_count
    success_rate = (success_count / total_sent * 100) if total_sent > 0 else 0

    # Average email size
    avg_size = db.session.query(func.avg(EmailLog.email_size_bytes)).filter(
        EmailLog.timestamp >= since,
        EmailLog.email_size_bytes.isnot(None)
    ).scalar() or 0

    # Average send time
    avg_duration = db.session.query(func.avg(EmailLog.send_duration_ms)).filter(
        EmailLog.timestamp >= since,
        EmailLog.send_duration_ms.isnot(None)
    ).scalar() or 0

    # By template
    by_template = db.session.query(
        EmailLog.template_name,
        func.count(EmailLog.id).label('count'),
        func.avg(EmailLog.email_size_bytes).label('avg_size'),
        func.sum(case((EmailLog.result == 'SENT', 1), else_=0)).label('success')
    ).filter(
        EmailLog.timestamp >= since
    ).group_by(EmailLog.template_name).all()

    # By domain
    by_domain = db.session.query(
        EmailLog.recipient_domain,
        func.count(EmailLog.id).label('count'),
        func.sum(case((EmailLog.result == 'SENT', 1), else_=0)).label('success')
    ).filter(
        EmailLog.timestamp >= since,
        EmailLog.recipient_domain.isnot(None)
    ).group_by(EmailLog.recipient_domain).order_by(desc('count')).limit(10).all()

    # Daily volume (last 30 days)
    daily_volume = db.session.query(
        func.date(EmailLog.timestamp).label('date'),
        func.count(EmailLog.id).label('count')
    ).filter(
        EmailLog.timestamp >= since
    ).group_by('date').order_by('date').all()

    return render_template('email_statistics.html',
                         total_sent=total_sent,
                         success_count=success_count,
                         failed_count=failed_count,
                         success_rate=success_rate,
                         avg_size=avg_size,
                         avg_duration=avg_duration,
                         by_template=by_template,
                         by_domain=by_domain,
                         daily_volume=daily_volume,
                         days=days)
```

#### 4.4 Mailbox Size Tracking Script (2 hours)

**Create:** `/home/kdresdell/Documents/DEV/minipass_env/scripts/check_mailbox_sizes.py`

```python
#!/usr/bin/env python3
"""
Mailbox Size Checker
Scans docker-mailserver maildata directory and reports storage usage
"""

import os
from pathlib import Path

MAILDATA_PATH = "/home/kdresdell/Documents/DEV/minipass_env/maildata"

def get_dir_size(path):
    """Calculate total size of directory"""
    total = 0
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file(follow_symlinks=False):
                total += entry.stat().st_size
            elif entry.is_dir(follow_symlinks=False):
                total += get_dir_size(entry.path)
    return total

def format_bytes(bytes_val):
    """Format bytes to human-readable"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} TB"

def check_mailboxes():
    """Check all mailbox sizes"""
    mailboxes = []

    # Scan maildata directory
    # Structure: maildata/minipass.me/user/
    domain_path = Path(MAILDATA_PATH) / "minipass.me"

    if not domain_path.exists():
        print("❌ Maildata directory not found")
        return

    for user_dir in domain_path.iterdir():
        if user_dir.is_dir():
            user_name = user_dir.name
            size = get_dir_size(user_dir)
            mailboxes.append((f"{user_name}@minipass.me", size))

    # Sort by size descending
    mailboxes.sort(key=lambda x: x[1], reverse=True)

    # Print report
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║            Minipass Mailbox Storage Report                     ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print("")

    total_size = 0
    for email, size in mailboxes:
        total_size += size
        percent = (size / (5 * 1024**3)) * 100  # Assuming 5GB quota

        status = "  "
        if percent > 90:
            status = "🚨"
        elif percent > 75:
            status = "⚠️ "

        print(f"{status} {email:30s} {format_bytes(size):>12s}  ({percent:.1f}%)")

    print("─" * 66)
    print(f"   {'TOTAL':30s} {format_bytes(total_size):>12s}")
    print("")

if __name__ == "__main__":
    check_mailboxes()
```

**Make executable and add to cron:**
```bash
chmod +x /home/kdresdell/Documents/DEV/minipass_env/scripts/check_mailbox_sizes.py

# Add to cron (weekly on Sunday at 3 AM)
0 3 * * 0 /home/kdresdell/Documents/DEV/minipass_env/venv/bin/python \
          /home/kdresdell/Documents/DEV/minipass_env/scripts/check_mailbox_sizes.py >> \
          /home/kdresdell/Documents/DEV/minipass_env/logs/mailbox_sizes.log 2>&1
```

#### Phase 4 Summary

**Expected Results:**
- ✅ Detailed email performance metrics
- ✅ Dashboard showing trends and patterns
- ✅ Mailbox storage monitoring
- ✅ Proactive alerting on issues

**Time Required:** 10-12 hours total

---

### Phase 5: Long-Term Improvements (Month 3+) 🚀

**Priority: LOW - Future-Proofing**

**Goal:** Evaluate and implement advanced features for scaling

#### 5.1 Transactional Email Service Evaluation

**When to Consider:**
- Gmail blocks persist despite Phase 1-2 fixes
- Volume exceeds 5,000 emails/day
- Need advanced analytics
- Want to reduce maintenance burden

**Recommended Service:** AWS SES
- Cost-effective ($0.10 per 1,000 emails)
- Good deliverability
- API integration available

**Implementation Plan:**
```python
# Add provider abstraction layer
def send_email(..., provider='smtp'):
    if provider == 'ses':
        return send_via_aws_ses(...)
    elif provider == 'sendgrid':
        return send_via_sendgrid(...)
    else:
        return send_via_smtp(...)  # Current implementation
```

#### 5.2 Email Template Framework (MJML)

**What Is MJML:**
- Responsive email framework
- Compiles to HTML that works across all clients
- Easier maintenance

**Decision:** Evaluate after Phase 2 if template maintenance becomes burden

#### 5.3 Advanced Monitoring

- Email warming strategy (if switching providers)
- A/B testing for email templates
- Click-through tracking (if needed)
- Advanced bounce processing

---

## Testing & Verification Plan

### Pre-Deployment Testing

#### Test 1: RFC 5322 Compliance

**Send test email and verify headers:**
```bash
# Send test email
curl -X POST http://localhost:5000/api/test-email \
  -H "Content-Type: application/json" \
  -d '{"to": "kdresdell@gmail.com"}'

# In Gmail, click "Show Original"
# Verify ALL headers present:
```

**Required Headers Checklist:**
```
✓ Date: Sun, 16 Feb 2026 14:23:45 -0500
✓ From: Minipass <noreply@minipass.me>
✓ To: kdresdell@gmail.com
✓ Subject: Test Email
✓ Message-ID: <1708110225000000@minipass.me>
✓ Return-Path: <noreply@minipass.me>
✓ Auto-Submitted: auto-generated
✓ MIME-Version: 1.0
✓ Content-Type: multipart/related; charset="utf-8"
```

#### Test 2: Email Size Verification

**Check email size:**
```bash
# Gmail → Show Original → Look for "Content-Length" or count bytes
# Phase 1 target: <20KB
# Phase 2 target: <10KB
```

#### Test 3: Character Encoding

**Send French email:**
```python
subject = "Demande d'inscription reçue — Vérification"
# Verify accents display correctly (no � symbols)
```

#### Test 4: SPF/DKIM/DMARC Authentication

**Run verification script:**
```bash
bash /home/kdresdell/Documents/DEV/minipass_env/scripts/verify_email_rfc_compliance.sh
```

**Expected Output:**
```
✅ PASS: SPF record found
✅ PASS: DKIM record exists
✅ PASS: DMARC record configured
```

#### Test 5: Spam Score

**Use Mail-Tester:**
```
1. Send test email to address provided by https://www.mail-tester.com/
2. Check spam score
3. Target: 10/10
```

**Common issues if score <10:**
- DMARC not configured
- SPF alignment issue
- DKIM signature missing
- Large email size
- Spam-trigger words in content

### Post-Deployment Monitoring

#### Week 1: Gmail Block Watch

**Daily Checks:**
```bash
# Check email health
python /home/kdresdell/Documents/DEV/minipass_env/scripts/email_health_check.py

# Expected output:
# ✅ All systems healthy!
# 📈 Success Rate: 98.5%
# 🎯 Gmail Failures: 0
```

**Monitor for:**
- ❌ Success rate drops below 95%
- ❌ Gmail-specific failures increase
- ❌ Any 421 SMTP error codes (rate limiting)

#### Week 2: Size Reduction Validation

**Check average email size:**
```sql
SELECT AVG(email_size_bytes) / 1024 as avg_size_kb
FROM email_log
WHERE timestamp >= DATE('now', '-7 days')
  AND email_size_bytes IS NOT NULL;

-- Target: <15KB after Phase 1, <10KB after Phase 2
```

#### Week 3: DMARC Report Analysis

**Review first DMARC reports:**
```bash
python /home/kdresdell/Documents/DEV/minipass_env/scripts/fetch_dmarc_reports.py

# Check dashboard at /admin/dmarc-reports
# Look for:
# ✅ DKIM pass rate >95%
# ✅ SPF pass rate 100%
# ✅ Disposition = "none" (not quarantine/reject)
```

#### Month 2: Long-Term Trends

**KPIs to track:**
- Monthly email volume
- Delivery success rate trend
- Average email size trend
- Gmail vs other providers success rates
- DMARC authentication pass rates

---

## Success Metrics

### Short-Term (Month 1)

**Must Achieve:**
- ✅ Zero Gmail blocks for 30 consecutive days
- ✅ Email size <15KB average (Phase 1)
- ✅ Date header in 100% of emails
- ✅ UTF-8 charset declared in all emails
- ✅ SPF/DKIM/DMARC verified and passing
- ✅ 98%+ delivery success rate

**Indicators:**
- Email health check passes daily
- No 421 SMTP error codes
- Mail-Tester score: 9-10/10

### Medium-Term (Month 3)

**Must Achieve:**
- ✅ Email size <10KB average (Phase 2 - hosted images)
- ✅ DMARC reports collected and analyzed weekly
- ✅ Email statistics dashboard operational
- ✅ Mailbox size monitoring active
- ✅ 99%+ delivery success rate

**Indicators:**
- DMARC pass rates >95%
- No deliverability regressions
- Proactive alerting working

### Long-Term (Month 6)

**Must Achieve:**
- ✅ Zero deliverability incidents for 6 months
- ✅ Automated monitoring and alerting fully operational
- ✅ Email infrastructure documented and maintainable
- ✅ Transactional service evaluation completed (decision made)
- ✅ 99.5%+ delivery success rate

**Indicators:**
- Confidence in email infrastructure
- Scalability proven (can handle 10x volume)
- Team trained on monitoring tools

---

## Cost Analysis

### Current State (Self-Hosted Only)

**Monthly Cost:** $0 (excluding VPS cost)
**Good For:** 1-10 customers, <2,000 emails/day
**Risk:** Gmail blocks, manual troubleshooting

### Phase 1-4 Implementation

**Monthly Cost:** $0
**Infrastructure:** Existing VPS and docker-mailserver
**Time Investment:** ~30-40 hours over 2 months
**Good For:** 10-50 customers, <5,000 emails/day

### Phase 5 (If Transactional Service Needed)

#### Option A: AWS SES
- **Current volume** (1,860 emails/month): $0.19/month
- **10x scale** (18,600 emails/month): $1.86/month
- **100x scale** (186,000 emails/month): $18.60/month

#### Option B: SendGrid
- **Current volume**: $0 (free tier: 100/day)
- **10x scale**: Still free tier
- **100x scale**: $89.95/month (100k emails)

#### Option C: Postmark
- **Current volume**: $15/month (10k minimum)
- **10x scale**: $15/month (still within 10k)
- **100x scale**: $279/month (200k emails)

**Recommendation:** Only add transactional service if Gmail blocks continue after Phase 1-2

---

## Risk Assessment & Mitigation

### Risk 1: Image Hosting Downtime

**Impact:** If web server down, images won't display in emails

**Mitigation:**
- Monitor nginx uptime
- Use reliable VPS
- Emails still readable without images (graceful degradation)
- Consider CloudFlare CDN (free tier) for redundancy

**Probability:** Low (same VPS hosts Flask app)

### Risk 2: Breaking Existing Emails

**Impact:** Old emails in user inboxes might break with template changes

**Mitigation:**
- Keep both embedded and hosted modes available initially
- Gradual rollout (10% → 50% → 100%)
- Test extensively before full deployment
- Old emails unchanged (only new emails use hosted images)

**Probability:** Low (changes only affect new emails)

### Risk 3: DMARC False Positives

**Impact:** Good emails marked as failed in reports

**Mitigation:**
- Start with `p=quarantine` not `p=reject`
- Manually review reports for first month
- Don't auto-act on report data initially
- Use reports for insight, not automation

**Probability:** Medium (common during initial setup)

### Risk 4: Database Migration Errors

**Impact:** EmailLog table corruption during field additions

**Mitigation:**
- Backup database before migration
- Test migration on dev/staging first
- Verify data integrity after migration
- Have rollback plan ready

**Probability:** Low (simple ALTER TABLE commands)

### Risk 5: Cron Job Failures

**Impact:** Monitoring/fetching scripts don't run

**Mitigation:**
- Add logging to all cron jobs
- Monitor cron logs weekly
- Set up cron failure alerting
- Test scripts manually before adding to cron

**Probability:** Medium (common misconfiguration)

---

## Rollback Plan

### If Phase 1 Causes Issues

**Symptoms:**
- Higher failure rate than before
- New types of errors

**Rollback:**
```bash
cd /home/kdresdell/Documents/DEV/minipass_env
git checkout HEAD~1 app/utils.py
git checkout HEAD~1 templates/email_templates/compileEmailTemplate.py
sudo systemctl restart minipass
```

**Verify:**
- Check email_health_check.py output
- Send test email to kdresdell@gmail.com
- Monitor for 24 hours

### If Phase 2 (Hosted Images) Causes Issues

**Symptoms:**
- Images not displaying in emails
- Higher failure rate
- User complaints about missing images

**Rollback:**
```python
# In utils.py, temporarily default to embedded mode
def send_email(..., use_hosted_images=False):  # ← Change back to False
```

**Verify:**
- Emails revert to embedded images
- Size increases back to ~20KB
- Images display correctly

### If Phase 3 (DMARC) Causes Issues

**Symptoms:**
- DMARC fetcher errors
- Database issues
- Cron job failures

**Rollback:**
```bash
# Disable cron job
crontab -e
# Comment out DMARC fetcher line

# Drop DMARC database if corrupted
rm /home/kdresdell/Documents/DEV/minipass_env/data/dmarc_reports.db
```

**Verify:**
- No cron errors in logs
- Email sending unaffected

---

## Conclusion

This comprehensive plan provides a **complete roadmap to RFC 5322 compliance** and **bulletproof email deliverability** for Minipass.

### Key Takeaways

**What Went Wrong:**
1. Missing RFC 5322 required Date header (critical bug)
2. Outdated email design approach (embedded Base64 images from 2010s)
3. No character encoding declaration (breaks French accents)
4. No monitoring or DMARC feedback loop

**The Fix:**
- **Phase 1**: 100% RFC compliance + emergency fixes (2-3 hours)
- **Phase 2**: Modern hosted images approach (6-8 hours)
- **Phase 3**: DMARC automation and monitoring (8-10 hours)
- **Phase 4**: Comprehensive analytics (10-12 hours)
- **Phase 5**: Evaluate advanced options (as needed)

**Expected Outcome:**
- ✅ Zero Gmail blocks
- ✅ 99%+ delivery rate
- ✅ <10KB email size
- ✅ Full RFC compliance
- ✅ Proactive monitoring
- ✅ Scalable to 10x volume

**Cost:** $0 for Phases 1-4 (all on existing infrastructure)

**Time Investment:** ~30-40 hours over 2 months

**ROI:** Business continuity secured, professional email infrastructure, ready to scale

---

## Quick Reference

### Essential Commands

```bash
# RFC Compliance Check
bash /home/kdresdell/Documents/DEV/minipass_env/scripts/verify_email_rfc_compliance.sh

# Email Health Check
python /home/kdresdell/Documents/DEV/minipass_env/scripts/email_health_check.py

# DMARC Reports Fetch
python /home/kdresdell/Documents/DEV/minipass_env/scripts/fetch_dmarc_reports.py

# Mailbox Sizes
python /home/kdresdell/Documents/DEV/minipass_env/scripts/check_mailbox_sizes.py

# Recompile Email Templates
cd /home/kdresdell/Documents/DEV/minipass_env/app/templates/email_templates
python compileEmailTemplate.py signup --update-original

# Test Email Send
curl -X POST http://localhost:5000/api/test-email \
  -H "Content-Type: application/json" \
  -d '{"to": "kdresdell@gmail.com"}'
```

### Dashboard URLs

- Email Statistics: `http://localhost:5000/admin/email-statistics`
- DMARC Reports: `http://localhost:5000/admin/dmarc-reports`
- Mailbox Storage: (add to admin dashboard in Phase 4)

### Important File Paths

```
/home/kdresdell/Documents/DEV/minipass_env/
├── app/
│   ├── utils.py                           # Email sending function
│   ├── models.py                          # EmailLog model
│   └── templates/email_templates/          # Email templates
├── scripts/
│   ├── verify_email_rfc_compliance.sh      # DNS verification
│   ├── email_health_check.py               # Daily monitoring
│   ├── fetch_dmarc_reports.py              # DMARC automation
│   └── check_mailbox_sizes.py              # Storage tracking
├── config/opendkim/                        # DKIM configuration
├── data/
│   └── dmarc_reports.db                    # DMARC database
└── logs/
    ├── dmarc_fetch.log                     # DMARC fetcher logs
    └── mailbox_sizes.log                   # Storage check logs
```

---

## Need Help?

**Documentation:**
- RFC 5322: https://www.rfc-editor.org/rfc/rfc5322.html
- SPF: https://www.rfc-editor.org/rfc/rfc7208.html
- DKIM: https://www.rfc-editor.org/rfc/rfc6376.html
- DMARC: https://www.rfc-editor.org/rfc/rfc7489.html

**Testing Tools:**
- Mail-Tester: https://www.mail-tester.com/
- MXToolbox: https://mxtoolbox.com/
- DMARC Analyzer: https://dmarcian.com/

**Support:**
- Review this plan section by section
- Test each phase before proceeding to next
- Monitor dashboards daily during rollout
- Keep rollback plan handy

**Your email infrastructure will be RFC-compliant and fireproof** ✅ 🔥

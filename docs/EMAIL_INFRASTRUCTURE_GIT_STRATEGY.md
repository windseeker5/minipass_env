# Email Infrastructure Overhaul - Git Branch Strategy

**Date:** February 16, 2026
**Project:** Minipass Email Infrastructure Overhaul
**Related Doc:** `docs/EMAIL_INFRASTRUCTURE_PLAN.md`

---

## Overview

This document outlines the Git branch strategy for implementing the Email Infrastructure Overhaul plan. The work is organized into separate branches by phase to allow for:
- Independent testing of each phase
- Easy rollback if issues arise
- Clean pull requests for code review
- Staged deployment to production

---

## Branch Structure

### Main Branches

```
main (production)
  └── feature/email-infrastructure-overhaul (parent branch)
       ├── feature/email-phase1-critical-fixes
       ├── feature/email-phase2-hosted-images
       ├── feature/email-phase3-dmarc-automation
       └── feature/email-phase4-monitoring
```

---

## Branch Details

### 1. Parent Branch: `feature/email-infrastructure-overhaul`

**Purpose:** Integration branch for all email infrastructure work

**Create from:** `main`

**Commands:**
```bash
git checkout main
git pull origin main
git checkout -b feature/email-infrastructure-overhaul
git push -u origin feature/email-infrastructure-overhaul
```

**Contains:** Documentation and shared configuration files

**Merge to:** `main` (only after ALL phases tested and approved)

---

### 2. Phase 1: `feature/email-phase1-critical-fixes`

**Purpose:** CRITICAL fixes to prevent Gmail blocks

**Create from:** `feature/email-infrastructure-overhaul`

**Priority:** 🚨 URGENT - Deploy within 24 hours

**Commands:**
```bash
git checkout feature/email-infrastructure-overhaul
git checkout -b feature/email-phase1-critical-fixes
```

**Changes Include:**
1. **Add missing Date header** (`app/utils.py`)
   - Line 2850: Import `formatdate`
   - Line 3061: Add `msg["Date"] = formatdate(localtime=True)`

2. **Reduce email size** (`app/templates/email_templates/compileEmailTemplate.py`)
   - Line 207-240: Reduce image width from 600px to 400px
   - Increase compression from 85% to 70%

3. **Create email health monitor** (`scripts/email_health_check.py`)
   - Monitor email success rate (last 24 hours)
   - Alert if success rate < 95%
   - Alert if average email size > 25KB
   - Alert if Gmail bounce rate > 5%

**Testing:**
```bash
# Send test email to verify Date header
curl -X POST http://localhost:5000/api/test-email \
  -H "Content-Type: application/json" \
  -d '{"to": "kdresdell@gmail.com"}'

# Check Gmail "Show Original" for Date header
# Verify email size < 25KB
```

**Merge to:** `feature/email-infrastructure-overhaul` after testing

**Deploy to Production:** Immediately after merge (business-critical fix)

---

### 3. Phase 2: `feature/email-phase2-hosted-images`

**Purpose:** Switch from embedded Base64 images to hosted URLs

**Create from:** `feature/email-infrastructure-overhaul`

**Priority:** HIGH - Deploy within 1 week

**Commands:**
```bash
git checkout feature/email-infrastructure-overhaul
git checkout -b feature/email-phase2-hosted-images
```

**Changes Include:**
1. **Create image hosting directory**
   - `app/static/email-assets/` (new directory)
   - Upload all email images from templates
   - Configure nginx to serve static files

2. **Modify email templates** (all templates in `app/templates/email_templates/`)
   - Replace: `<img src="cid:hero_new_pass">`
   - With: `<img src="https://minipass.me/email-assets/hero_new_pass.png">`
   - Keep QR codes as embedded (small, ~2KB)

3. **Add hosted images flag** (`app/utils.py`)
   - Add `use_hosted_images=True` parameter to `send_email()`
   - If True: Don't attach inline images, use URLs
   - If False: Current behavior (backward compatibility)

**Testing:**
```bash
# Test hosted image serving
curl -I https://minipass.me/email-assets/hero_new_pass.png

# Send test emails with hosted images
# Verify images display in Gmail, Yahoo, Outlook
# Check email size (target: < 10KB)
```

**Target Result:**
- Email size reduction: 32KB → < 10KB (75% reduction)
- Images display correctly in all email clients

**Merge to:** `feature/email-infrastructure-overhaul` after 1 week of testing

**Deploy to Production:** After monitoring deliverability for 1 week

---

### 4. Phase 3: `feature/email-phase3-dmarc-automation`

**Purpose:** Automate DMARC report collection and analysis

**Create from:** `feature/email-infrastructure-overhaul`

**Priority:** MEDIUM - Deploy within 2-3 weeks

**Commands:**
```bash
git checkout feature/email-infrastructure-overhaul
git checkout -b feature/email-phase3-dmarc-automation
```

**Changes Include:**
1. **DMARC configuration check** (`scripts/check_dmarc.sh`)
   - Check if DMARC record exists
   - Verify dmarc@minipass.me mailbox exists
   - Confirm reports are arriving

2. **DMARC report fetcher** (`scripts/fetch_dmarc_reports.py`)
   - Connect to dmarc@minipass.me via IMAP
   - Download and parse XML reports
   - Store in SQLite database
   - Run daily via cron

3. **DMARC dashboard** (`app/templates/dmarc_reports.html`)
   - Flask route: `/admin/dmarc-reports`
   - Table view of all DMARC reports
   - Filter by org (Gmail, Yahoo, Outlook)
   - Chart showing pass/fail trends
   - Alert if failure rate > 5%

**Testing:**
```bash
# Run DMARC check script
./scripts/check_dmarc.sh

# Manually fetch reports
python scripts/fetch_dmarc_reports.py

# Test dashboard
# Visit http://localhost:5000/admin/dmarc-reports
```

**Merge to:** `feature/email-infrastructure-overhaul` after dashboard testing

**Deploy to Production:** After verifying dashboard displays correctly

---

### 5. Phase 4: `feature/email-phase4-monitoring`

**Purpose:** Add comprehensive email statistics and monitoring

**Create from:** `feature/email-infrastructure-overhaul`

**Priority:** MEDIUM - Deploy within 1-2 months

**Commands:**
```bash
git checkout feature/email-infrastructure-overhaul
git checkout -b feature/email-phase4-monitoring
```

**Changes Include:**
1. **Enhance EmailLog model** (`app/models.py`)
   - Add fields: `send_duration_ms`, `email_size_bytes`, `retry_count`, `bounce_reason`, `recipient_domain`
   - Add indexes for performance
   - Create migration script: `migrations/upgrade_production_database.py`

2. **Email statistics dashboard** (`app/templates/email_statistics.html`)
   - Flask route: `/admin/email-statistics`
   - Volume chart (emails sent per day, last 30 days)
   - Success rate pie chart
   - Breakdown by template type
   - Domain distribution (Gmail vs Yahoo vs Others)
   - Average email size trend

3. **Mailbox size tracking** (`scripts/check_mailbox_sizes.py`)
   - Parse `/maildata/` directories
   - Calculate storage per mailbox
   - Alert if any mailbox > 90% quota
   - Integration with Flask admin: `/admin/mailbox-storage`

**Testing:**
```bash
# Run database migration
python migrations/upgrade_production_database.py

# Test statistics dashboard
# Visit http://localhost:5000/admin/email-statistics

# Check mailbox sizes
python scripts/check_mailbox_sizes.py
```

**Merge to:** `feature/email-infrastructure-overhaul` after migration testing

**Deploy to Production:** After verifying database migration works correctly

---

## Workflow Summary

### Step 1: Create Parent Branch
```bash
git checkout main
git pull origin main
git checkout -b feature/email-infrastructure-overhaul
git push -u origin feature/email-infrastructure-overhaul
```

### Step 2: Work on Phase 1 (CRITICAL)
```bash
# Create Phase 1 branch
git checkout feature/email-infrastructure-overhaul
git checkout -b feature/email-phase1-critical-fixes

# Make changes
# (edit app/utils.py, app/templates/email_templates/compileEmailTemplate.py, etc.)

# Commit changes
git add app/utils.py
git commit -m "Add RFC 5322-compliant Date header to emails

Fixes critical issue causing Gmail blocks. Adds formatdate import
and sets Date header in send_email() function.

Related: EMAIL_INFRASTRUCTURE_PLAN.md Phase 1

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# Push to remote
git push -u origin feature/email-phase1-critical-fixes

# Test thoroughly

# Merge to parent branch
git checkout feature/email-infrastructure-overhaul
git merge feature/email-phase1-critical-fixes
git push origin feature/email-infrastructure-overhaul

# Deploy to production (URGENT)
git checkout main
git merge feature/email-infrastructure-overhaul
git push origin main
```

### Step 3: Work on Phase 2
```bash
# Create Phase 2 branch
git checkout feature/email-infrastructure-overhaul
git checkout -b feature/email-phase2-hosted-images

# Make changes
# (create app/static/email-assets/, modify templates, update utils.py)

# Commit changes
git add app/static/email-assets/
git add app/templates/email_templates/
git add app/utils.py
git commit -m "Implement hosted images for email templates

Switches from Base64 embedded images to hosted URLs. Reduces
email size from 32KB to <10KB (75% reduction).

- Create /static/email-assets/ directory
- Modify all email templates to use hosted URLs
- Add use_hosted_images flag to send_email()
- Keep QR codes as embedded (small, ~2KB)

Target: Improve Gmail deliverability and reduce spam signals

Related: EMAIL_INFRASTRUCTURE_PLAN.md Phase 2

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# Push and test
git push -u origin feature/email-phase2-hosted-images

# After 1 week of testing, merge to parent
git checkout feature/email-infrastructure-overhaul
git merge feature/email-phase2-hosted-images
git push origin feature/email-infrastructure-overhaul
```

### Step 4: Work on Phase 3 & 4 (Same Pattern)
Follow the same workflow as Phase 2:
1. Create branch from parent
2. Make changes
3. Commit with descriptive message
4. Push to remote
5. Test thoroughly
6. Merge to parent branch

### Step 5: Final Production Deployment (After ALL Phases Complete)
```bash
# Only after ALL phases are tested and working
git checkout main
git merge feature/email-infrastructure-overhaul
git push origin main

# Create release tag
git tag -a v2.0-email-infrastructure -m "Email Infrastructure Overhaul

Complete rewrite of email system for better deliverability:
- Fixed missing Date header (RFC 5322 compliance)
- Switched to hosted images (75% size reduction)
- Automated DMARC report analysis
- Added comprehensive email statistics
- Implemented mailbox size tracking

Related: docs/EMAIL_INFRASTRUCTURE_PLAN.md"

git push origin v2.0-email-infrastructure
```

---

## Branch Protection Rules

### For `feature/email-infrastructure-overhaul`:
- Require pull request reviews (optional, for team review)
- Require status checks to pass (if CI/CD configured)
- Do NOT allow force pushes

### For Phase Branches:
- Can be deleted after merging to parent
- Keep for 30 days for rollback if needed

---

## Rollback Strategy

### If Phase 1 Causes Issues:
```bash
# Revert main to previous commit
git checkout main
git revert <commit-hash>
git push origin main
```

### If Phase 2 Causes Issues:
```bash
# Revert parent branch
git checkout feature/email-infrastructure-overhaul
git revert <commit-hash>
git push origin feature/email-infrastructure-overhaul

# Re-deploy Phase 1 only
git checkout main
git merge feature/email-phase1-critical-fixes
git push origin main
```

---

## Commit Message Format

Use this format for all commits:

```
<action>: <brief description>

<detailed explanation>

- Bullet point 1
- Bullet point 2

<why this change matters>

Related: <document or issue>

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**Example:**
```
fix: Add missing Date header to prevent Gmail blocks

Implements RFC 5322-compliant Date header in send_email() function.
Gmail was blocking emails due to missing Date header, triggering
Amavis BAD-HEADER-7 quarantine.

- Import formatdate from email.utils
- Add msg["Date"] = formatdate(localtime=True) after Message-ID
- Prevents future Gmail blocks

Critical fix for business continuity. Without this, 40.9% of emails
were failing during Gmail blocks.

Related: docs/EMAIL_INFRASTRUCTURE_PLAN.md Phase 1

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

---

## Current Status

### ⚠️ IMPORTANT: Uncommitted Changes Exist

The following changes have already been made to the codebase but are NOT committed:

**File:** `app/utils.py`
- Line 2850: Added `formatdate` import
- Line 3061: Added Date header

**Action Required:**
```bash
# Check current changes
git status
git diff app/utils.py

# Option 1: Commit to Phase 1 branch immediately
git checkout -b feature/email-phase1-critical-fixes
git add app/utils.py
git commit -m "Add RFC 5322-compliant Date header to emails

Fixes critical issue causing Gmail blocks. Adds formatdate import
and sets Date header in send_email() function.

Related: EMAIL_INFRASTRUCTURE_PLAN.md Phase 1

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
git push -u origin feature/email-phase1-critical-fixes

# Option 2: Stash changes and start fresh
git stash save "Date header fix - Phase 1"
# Then create branches as outlined above
# Apply stash later: git stash pop
```

---

## Testing Checklist

### Phase 1 Testing:
- [ ] Date header appears in "Show Original" in Gmail
- [ ] Email size < 25KB
- [ ] No Amavis quarantine alerts
- [ ] Success rate > 95% for 48 hours
- [ ] No Gmail blocks

### Phase 2 Testing:
- [ ] Images display in Gmail, Yahoo, Outlook
- [ ] Email size < 10KB
- [ ] Hosted images load quickly
- [ ] No broken image icons
- [ ] Success rate > 98% for 1 week

### Phase 3 Testing:
- [ ] DMARC reports are fetched daily
- [ ] Dashboard displays reports correctly
- [ ] Pass/fail rates are accurate
- [ ] Alerts trigger when failure rate > 5%

### Phase 4 Testing:
- [ ] Database migration runs successfully
- [ ] Email statistics display correctly
- [ ] Mailbox size tracking works
- [ ] No performance degradation

---

## Timeline

| Phase | Duration | Start | End | Deployment |
|-------|----------|-------|-----|------------|
| Phase 1 | 2-3 days | Feb 16 | Feb 18 | Feb 18 (URGENT) |
| Phase 2 | 1 week | Feb 19 | Feb 25 | Feb 26 (after testing) |
| Phase 3 | 2-3 weeks | Feb 26 | Mar 11 | Mar 12 |
| Phase 4 | 1-2 months | Mar 12 | Apr 30 | May 1 |

**Total Timeline:** ~10-12 weeks for complete implementation

**CRITICAL PATH:** Phase 1 must be deployed within 24-48 hours to prevent further Gmail blocks.

---

## Questions & Decisions

### Q: Should we create pull requests for each phase?
**A:** Optional. If working solo, direct merges to parent branch are fine. If team review is desired, create PRs for each phase.

### Q: Can we skip phases?
**A:** Phase 1 is MANDATORY. Phase 2 is highly recommended. Phases 3-4 are optional but valuable.

### Q: What if Gmail blocks occur during Phase 2 development?
**A:** Immediately deploy Phase 1 fixes to production, even if Phase 2 is incomplete. Phase 1 is independent and can be deployed alone.

### Q: Should we deploy phases incrementally or all at once?
**A:** **Incremental deployment is strongly recommended.** Deploy Phase 1 immediately, then Phase 2 after 1 week of testing. This reduces risk and allows for rollback if issues arise.

---

## Success Criteria

### Phase 1 Success:
- ✅ Zero Gmail blocks for 1 week
- ✅ Email size < 25KB average
- ✅ Success rate > 95%

### Phase 2 Success:
- ✅ Email size < 10KB average
- ✅ Images display correctly in all email clients
- ✅ Success rate > 98%

### Phase 3 Success:
- ✅ DMARC reports collected daily
- ✅ Dashboard operational
- ✅ Pass/fail rates visible

### Phase 4 Success:
- ✅ Email statistics dashboard working
- ✅ Mailbox size tracking active
- ✅ No performance degradation

---

## Contact & Support

**Primary Developer:** kdresdell@gmail.com
**Documentation:** `docs/EMAIL_INFRASTRUCTURE_PLAN.md`
**Related Issues:** GitHub issue tracker (if applicable)

---

**Last Updated:** February 16, 2026
**Version:** 1.0
**Status:** Ready for Implementation

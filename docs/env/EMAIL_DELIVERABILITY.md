# Email Deliverability & Architecture Decisions

**READ THIS FILE BEFORE touching any email template or email-sending code.**

This documents the permanent architectural decisions made to achieve RFC 5322 compliance
and avoid spam filters / domain bans. Do not revert these without a deliberate decision.

---

## The Core Rule: Hosted Images, Except QR Codes

### Decision (Phase 3 — Feb 2026)

| Image type | How it's served | Reason |
|---|---|---|
| Hero image | Hosted Flask route (`{{ hero_image_url }}`) | Reduces email size, no CID |
| Owner logo | Hosted Flask route (`{{ owner_logo_url }}`) | Same |
| Interac logo | Hosted static URL (`{{ base_url }}/static/images/email/interac-logo.jpg`) | Same |
| Any other static image | Hosted static URL via `{{ base_url }}/static/...` | Same |
| **QR code** | **CID attachment (`cid:qr_code`)** | **Must be embedded — QR must survive email forwarding and offline viewing** |

**Never re-add `cid:interac_logo`, `cid:hero_image`, or any other CID attachment
to a template. The Phase 3 decision was made to:**
1. Keep email file size under 100 KB (large emails go to spam)
2. Avoid triggering spam filters that penalize many inline attachments
3. Prevent the Gmail 24h domain block we experienced (Feb 2026)

### The `base_url` Variable

Every email context receives `base_url` automatically — injected by `send_email()` in
`utils.py` (around line 2949):

```python
context['base_url'] = base_url  # e.g. https://minipass.me
```

Use it for any static image:
```html
<img src="{{ base_url }}/static/images/email/interac-logo.jpg" alt="Interac" width="40">
```

**Dev note:** In dev, `base_url` = `http://127.0.0.1:5000`. Images won't load in Gmail
when sent from localhost — this is expected and acceptable. Use the browser preview at
`/activity/<id>/email-preview?type=<template_name>` for visual validation locally.

### inline_images.json

This file stores base64-encoded images for the `/hero-image/` Flask route (Priority 2
fallback for hero images). It is **not** used for MIME email attachments.

- The `interac_logo` key must NOT appear in any `inline_images.json` — it was removed
  in Phase 3.
- The only CID attachment handled in code is `qr_code` (added dynamically in
  `send_email()`, not from inline_images.json).

---

## Subject Line Rules

"Payment required" and its French equivalent "Paiement requis" are known spam triggers.
**Never use payment-urgency language in the default subject line.**

| Template | Field | Value (default) | Changed from |
|---|---|---|---|
| `signup_payment_first` | `subject` | "Pré-inscription reçue — Prochaine étape" | "Paiement requis" (Feb 2026) |
| `signup_payment_first` | `title` | "Pré-inscription reçue — Prochaine étape" | "Paiement requis" (Mar 2026) |

> **Note:** `subject` = email subject line (seen in inbox). `title` = heading rendered inside the email body. **Both must be changed** — spam filters scan both.

**Words/phrases to avoid in subject lines:**
- "Paiement requis" / "Payment required"
- "Urgent" / "Action required"
- "Confirmez maintenant" / "Confirm now"
- Any ALL CAPS word

**Safe alternatives:**
- "Prochaine étape" (Next step)
- "Votre inscription" (Your registration)
- "Confirmation de pré-inscription"

---

## RFC 5322 Compliance Checklist

These are already implemented correctly. Do not break them.

| Header / Feature | Status | Code location |
|---|---|---|
| `Precedence: normal` for transactional | ✅ | `utils.py` ~3088 — `'signup' in template_name` |
| `Precedence: bulk` for bulk sends | ✅ | `utils.py` ~3088 |
| `List-Unsubscribe` header | ✅ | `utils.py` — all outbound emails |
| `List-Unsubscribe-Post: List-Unsubscribe=One-Click` | ✅ | `utils.py` |
| `Return-Path` aligned with `From:` | ✅ | docker-mailserver config |
| `Message-ID` with microsecond precision | ✅ | `utils.py` |
| `multipart/alternative` with plain-text fallback | ✅ | `utils.py` |
| Physical address in footer | ✅ | All email templates |
| Unsubscribe link in footer | ✅ | All email templates |
| Duplicate MIME-Version removed | ✅ | `clean_mime_headers()` in `utils.py` |

### Precedence Header Logic (utils.py ~3088)

```python
# Transactional emails (signup confirmation, payment receipt, QR pass delivery)
if 'signup' in template_name or 'pass' in template_name:
    msg['Precedence'] = 'normal'
else:
    msg['Precedence'] = 'bulk'
```

---

## Server-Level Deliverability (docker-mailserver)

These are outside the app code. Verify after any server migration:

- **DKIM signing** — must be enabled in docker-mailserver config
- **SPF record** — `minipass.me` DNS must have correct SPF TXT record
- **DMARC policy** — should be set to at minimum `p=none` with reporting

The Feb 2026 Google 24h domain ban was caused by a combination of spam subject lines
and possibly a temporary DKIM/SPF alignment issue. Both are now fixed.

---

## Template Browser Preview (Dev)

To visually test any email template without sending:

```
http://localhost:5000/activity/<activity_id>/email-preview?type=<template_name>
```

Examples:
```
http://localhost:5000/activity/1/email-preview?type=signup_payment_first
http://localhost:5000/activity/1/email-preview?type=signup
http://localhost:5000/activity/1/email-preview?type=newPass
```

In the browser preview:
- CID images are converted to data URIs — they render correctly
- Hosted images (`{{ base_url }}/...`) resolve from localhost — they also render correctly
- This is the best tool for visual email validation in dev

To send an actual test email: activity Settings page → "Send Test Email".

---

## Summary: What To Check Every Time You Touch an Email Template

1. **Images** — Are you using hosted URLs or CID? Only `qr_code` may be CID.
2. **Subject line** — Does it contain urgency/payment trigger words?
3. **inline_images.json** — Does it have any unexpected CID keys?
4. **`Precedence` header** — Transactional = `normal`, bulk = `bulk`. Don't change.
5. **Footer** — Physical address, unsubscribe link, support email all present?
6. **Preview** — Check `/email-preview` before sending a test.

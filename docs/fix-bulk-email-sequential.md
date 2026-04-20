# Fix: Bulk Email — Sequential Send (Option B)

**Date:** 2026-04-19  
**Diagnosed on:** LHGI production container (`minipass_lhgi`)  
**Reporter:** Ken Dresdell  

---

## Problem Summary

When Jean-François triggered a broadcast email to all participants of "Hockey Printemps 2026" (24 passports, ~15 unique emails), 13 emails failed with:

```
SMTPServerDisconnected: please run connect() first
```

and

```
sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached, connection timed out
```

---

## Root Cause

The announcement broadcast loops over all passports and calls `send_email_async()` once per passport, spawning **N threads simultaneously**. Each thread calls `get_setting("MAIL_SERVER")` inside the thread, which hits the database.

With 13+ threads all querying the DB at the same time:

1. SQLAlchemy connection pool (max 15: 5 base + 10 overflow) is exhausted
2. `Setting.query.all()` throws `TimeoutError` in some threads
3. The exception is **silently swallowed** in `get_setting()` (`utils.py:486`):
   ```python
   except Exception:
       g._settings_cache = {}   # silent failure — empty cache
   ```
4. `get_setting("MAIL_SERVER")` returns `""` (the default)
5. `smtplib.SMTP("", 587)` is called — Python never connects (empty host = `if host:` is False)
6. `server.ehlo()` raises `SMTPServerDisconnected: please run connect() first`

**13 of 15 unique recipients did not receive the email.**  
The 2 that succeeded were the first threads to grab a DB connection before the pool was exhausted.

---

## Fix: Option B — Sequential Bulk Send

Instead of spawning N threads simultaneously, create one reusable function that spawns **one** background thread, reads SMTP settings **once**, and sends emails **sequentially** with a small delay.

---

## Files to Change

| File | Change |
|---|---|
| `app/utils.py` | Add `send_bulk_sequential()` + fix silent exception log in `get_setting()` |
| `app/app.py` | Replace bulk loops at lines 8713, 11235, 1202 |

---

## Step 1 — Fix silent failure in `get_setting()` (`utils.py:486`)

```python
# BEFORE
except Exception:
    g._settings_cache = {}

# AFTER
except Exception as e:
    logging.error(f"❌ get_setting() DB pool exhausted — settings cache empty: {e}")
    g._settings_cache = {}
```

---

## Step 2 — Add `send_bulk_sequential()` to `utils.py`

Add after `send_email_async()` (after line ~3598).

```python
def send_bulk_sequential(app, email_jobs, subject, activity=None, operational=False, delay=0.3):
    """
    Send multiple emails in a single background thread, sequentially.

    Designed for bulk/announcement sends. Reads SMTP config once,
    then sends one-by-one — no DB pool pressure, no simultaneous
    SMTP connections.

    Args:
        email_jobs: list of dicts, each with keys:
            - to_email (str)
            - html_body (str)
            - user (User object, optional)
        subject: email subject line (same for all)
        activity: Activity object (optional, for logging)
        operational: if True, bypasses unsubscribe checks
        delay: seconds to wait between sends (default 0.3)
    """
    import threading
    import time

    activity_id = activity.id if activity and hasattr(activity, 'id') else None

    def _run():
        with app.app_context():
            from utils import send_email, get_setting
            from models import EmailLog
            import json
            from datetime import datetime, timezone

            # ── Read SMTP config ONCE ──────────────────────────────────
            smtp_config = {
                'MAIL_SERVER':         get_setting('MAIL_SERVER'),
                'MAIL_PORT':           int(get_setting('MAIL_PORT', '587') or 587),
                'MAIL_USERNAME':       get_setting('MAIL_USERNAME'),
                'MAIL_PASSWORD':       get_setting('MAIL_PASSWORD'),
                'MAIL_USE_TLS':        True,
                'MAIL_USE_SSL':        False,
                'MAIL_DEFAULT_SENDER': get_setting('MAIL_DEFAULT_SENDER') or get_setting('MAIL_USERNAME'),
                'SENDER_NAME':         get_setting('SENDER_NAME', 'Minipass'),
            }

            if not smtp_config['MAIL_SERVER']:
                logging.error("❌ send_bulk_sequential: MAIL_SERVER is empty — aborting bulk send")
                return

            sent = 0
            failed = 0

            for job in email_jobs:
                to_email = job.get('to_email')
                html_body = job.get('html_body')

                try:
                    result = send_email(
                        subject=subject,
                        to_email=to_email,
                        html_body=html_body,
                        email_config=smtp_config,
                        operational=operational,
                    )

                    # ── Write EmailLog ─────────────────────────────────
                    log_entry = EmailLog(
                        timestamp=datetime.now(timezone.utc),
                        to_email=to_email,
                        subject=subject,
                        template_name='',
                        pass_code=None,
                        result='SENT' if result else 'FAILED',
                        context_json=json.dumps({'activity_id': activity_id}),
                        error_message=None if result else 'send_email() returned False',
                    )
                    db.session.add(log_entry)
                    db.session.commit()

                    if result:
                        sent += 1
                    else:
                        failed += 1
                        logging.error(f"❌ Bulk send failed for {to_email}")

                except Exception as e:
                    failed += 1
                    logging.exception(f"❌ Bulk send exception for {to_email}: {e}")
                    try:
                        log_entry = EmailLog(
                            timestamp=datetime.now(timezone.utc),
                            to_email=to_email,
                            subject=subject,
                            template_name='',
                            result='FAILED',
                            context_json=json.dumps({'error': str(e)}),
                            error_message=str(e),
                        )
                        db.session.add(log_entry)
                        db.session.commit()
                    except Exception:
                        pass  # Don't let logging failure crash the loop

                if delay > 0:
                    time.sleep(delay)

            logging.info(f"✅ Bulk send complete — {sent} sent, {failed} failed (subject: {subject})")

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
```

---

## Step 3 — Replace announcement broadcast loop (`app.py` ~line 8713)

**Remove** the existing loop (lines 8710–8732):

```python
# REMOVE THIS
sent_count = 0
failed_count = 0

for passport in unique_passports:
    try:
        user_name = passport.user.name or ""
        personalized = message.replace("{{ user_name }}", user_name).replace("{{ org_name }}", org_name)
        html_body = _build_announcement_html(personalized, logo_src)

        send_email_async(
            app=current_app._get_current_object(),
            user=passport.user,
            activity=activity,
            subject=subject,
            to_email=passport.user.email,
            html_body=html_body,
            operational=True,
        )
        sent_count += 1
    except Exception as e:
        print(f"❌ Failed to send announcement to {passport.user.email}: {e}")
        failed_count += 1
```

**Replace with:**

```python
# Build all email payloads in request context
email_jobs = []
for passport in unique_passports:
    user_name = passport.user.name or ""
    personalized = message.replace("{{ user_name }}", user_name).replace("{{ org_name }}", org_name)
    email_jobs.append({
        'to_email': passport.user.email,
        'html_body': _build_announcement_html(personalized, logo_src),
        'user': passport.user,
    })

# ONE sequential background thread — no more N simultaneous threads
from utils import send_bulk_sequential
send_bulk_sequential(
    app=current_app._get_current_object(),
    email_jobs=email_jobs,
    subject=subject,
    activity=activity,
    operational=True,
)

sent_count = len(email_jobs)  # optimistic count — thread runs after response
failed_count = 0
```

> **Note:** The HTTP response is now returned immediately (optimistic). The EmailLog will reflect the real results once the background thread completes. This is correct behavior — the admin does not wait for all emails to send before getting a response.

---

## Step 4 — Replace survey invitation loop (`app.py` ~line 11235)

Same pattern as Step 3. Build `email_jobs[]` with fully rendered `html_body` values in the request context (before the thread), then call `send_bulk_sequential()` once.

Each job needs a personalized `survey_url` — build it inside the loop before adding to `email_jobs`, just like `personalized` in the announcement.

Lower priority than Step 3 (surveys send smaller batches) but should be in the same commit.

---

## Step 5 — Fix `retry_failed_emails()` (`app.py` line 1202)

Low risk (small number of emails), but same pattern. Replace loop with `send_bulk_sequential()`.

---

## Deployment to LHGI (on the VPS after git pull)

```bash
cd /home/kdresdell/minipass_env

# Pull changes from main
git pull

# Sync changed files to LHGI deployed copy
cp app/utils.py deployed/lhgi/app/utils.py
cp app/app.py deployed/lhgi/app/app.py

# Restart container (~30 sec downtime)
cd deployed/lhgi
docker-compose restart
```

---

## After Deployment — Resend the 13 Failed Emails

Jean-François goes to the **Hockey Printemps 2026** activity dashboard and resends the broadcast.

- All 15 unique recipients will receive it this time
- 2 people (Kathleen Fournier Slater and William Gagnon) will receive it twice
- Acceptable for an end-of-season announcement

---

## Implementation Priority

| Priority | File | Change |
|---|---|---|
| 1 — Critical | `utils.py` | Add `send_bulk_sequential()` |
| 2 — Critical | `app.py` line ~8713 | Replace announcement broadcast loop |
| 3 — Important | `utils.py` line 486 | Log the silent DB failure |
| 4 — Good practice | `app.py` line ~11235 | Replace survey invitation loop |
| 5 — Nice to have | `app.py` line ~1202 | Replace retry failed emails loop |

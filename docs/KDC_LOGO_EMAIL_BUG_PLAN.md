# Fix Plan: KDC Email Logo Bugs (for VPS Claude Code)

## Context

Three logo bugs exist on kdc.minipass.me after a recent deployment:
1. **Bug 1** — Email preview shows LHGI foundation logo instead of a "K" placeholder
2. **Bug 2** — After "reset to default", email preview shows a tiny unusable placeholder
3. **Bug 3** — Received email shows broken image (alt text "Logo") instead of any logo

The app code lives in two places on this VPS:
- **KDC app code**: `/home/kdresdell/minipass_env/deployed/kdc/app/` (git repo, same code as local dev)
- **KDC config/compose**: `/home/kdresdell/minipass_env/deployed/kdc/`

---

## Root Cause Summary

| Bug | Root Cause |
|-----|-----------|
| Bug 1 — LHGI logo in preview | `LOGO_FILENAME` set in KDC DB or docker-compose env var, AND `logo.png` in uploads is LHGI's logo |
| Bug 2 — Tiny placeholder in preview | `email_preview_live` generates placeholder inline; font loading fails → 10px fallback font → invisible letter |
| Bug 3 — Broken logo in email | `_owner_logo_url = None` → template uses `cid:logo` → CID is stripped in hosted-images mode → broken image |

---

## Step 1 — Diagnose Bug 1: Find why LHGI logo appears

Read these files to find the source of the wrong logo:

1. Read `/home/kdresdell/minipass_env/deployed/kdc/docker-compose.yml`
   — Look for any `LOGO_FILENAME` entry in environment variables

2. Read `/home/kdresdell/minipass_env/deployed/kdc/.env` (if it exists)
   — Same, look for `LOGO_FILENAME`

3. Run a SQLite query on the KDC database to check if LOGO_FILENAME is in the DB:
   ```bash
   sqlite3 /home/kdresdell/minipass_env/deployed/kdc/app/instance/minipass.db \
     "SELECT key, value FROM setting WHERE key = 'LOGO_FILENAME';"
   ```

4. Check if a `logo.png` exists in KDC uploads:
   ```bash
   ls -la /home/kdresdell/minipass_env/deployed/kdc/app/static/uploads/logo.png 2>/dev/null && echo "EXISTS" || echo "MISSING"
   ```

**Based on what you find:**
- If `LOGO_FILENAME` is in `docker-compose.yml` env → remove that line from the file
- If `LOGO_FILENAME` is in the SQLite DB with value `'logo.png'` → update it to empty string:
  ```bash
  sqlite3 /home/kdresdell/minipass_env/deployed/kdc/app/instance/minipass.db \
    "UPDATE setting SET value = '' WHERE key = 'LOGO_FILENAME';"
  ```
- If `logo.png` exists in uploads → delete it:
  ```bash
  rm /home/kdresdell/minipass_env/deployed/kdc/app/static/uploads/logo.png
  ```

---

## Step 2 — Fix Bug 2 (preview tiny placeholder) in `app/app.py`

**File:** `/home/kdresdell/minipass_env/deployed/kdc/app/app.py`

Find the section in `email_preview_live` that generates the placeholder inline
(around the `else` branch after the two `elif os.path.exists()` checks for logo files).

**Replace this block:**
```python
        else:
            # No logo file found — generate placeholder data URI for browser preview
            from utils import generate_placeholder_logo_image
            _org_name = get_setting('ORG_NAME', 'Minipass')
            try:
                _placeholder_buf = generate_placeholder_logo_image(_org_name)
                _logo_b64 = base64.b64encode(_placeholder_buf.read()).decode('utf-8')
                _owner_logo_url = f'data:image/png;base64,{_logo_b64}'
            except Exception:
                _owner_logo_url = None
```

**With this:**
```python
        else:
            # No logo file — delegate to /owner-logo endpoint (browser fetches it; same path as signup page)
            _owner_logo_url = f'/owner-logo?activity_id={activity.id}'
```

**Why this works:** The `/owner-logo` endpoint (`serve_owner_logo` route) already generates the
correct placeholder — proven by the signup page showing a perfect "K". The inline generation
is fragile and produces bad results when fonts aren't found. Just use the working endpoint.

---

## Step 3 — Fix Bug 3 (broken logo in email) in `app/utils.py`

**File:** `/home/kdresdell/minipass_env/deployed/kdc/app/utils.py`

Find the section in `notify_pass_event` (~line 3719) that builds `_owner_logo_url`.
It's in the `else` branch (org logo path) after checking for activity-specific logo.

**Replace this:**
```python
        _org_logo_filename = get_setting('LOGO_FILENAME', '')
        _org_logo_path = os.path.join("static/uploads", _org_logo_filename) if _org_logo_filename else None
        _owner_logo_url = f"{_BASE_URL}/static/uploads/{_org_logo_filename}" if _org_logo_filename and _org_logo_path and os.path.exists(_org_logo_path) else None
```

**With this:**
```python
        _org_logo_filename = get_setting('LOGO_FILENAME', '')
        _org_logo_path = os.path.join("static/uploads", _org_logo_filename) if _org_logo_filename else None
        if _org_logo_filename and _org_logo_path and os.path.exists(_org_logo_path):
            _owner_logo_url = f"{_BASE_URL}/static/uploads/{_org_logo_filename}"
        else:
            # No logo file → use /owner-logo endpoint which generates placeholder correctly
            _act_id = activity.id if activity else None
            _owner_logo_url = f"{_BASE_URL}/owner-logo" + (f"?activity_id={_act_id}" if _act_id else "")
```

**Why this works:** In hosted-images mode, all CID attachments except the QR code are stripped
(utils.py line 2946). When `_owner_logo_url = None`, the template falls back to `cid:logo` which is
never attached → broken image. Using the `/owner-logo` URL means Gmail fetches a real PNG.

---

## Step 4 — Restart the KDC container

After making all changes:

```bash
cd /home/kdresdell/minipass_env/deployed/kdc
docker-compose restart
```

---

## Step 5 — Verify

1. **Bug 1**: Open KDC email preview → should show "K" placeholder (not LHGI logo)
2. **Bug 2**: Click "reset to default" on a template → preview should show proper "K" placeholder
3. **Bug 3**: Send a test email → received email should show a proper logo (same "K" placeholder)

---

## Files Modified on VPS

| File | Change |
|------|--------|
| `deployed/kdc/app/app.py` | Replace inline placeholder generation with `/owner-logo` URL |
| `deployed/kdc/app/utils.py` | Use `/owner-logo` URL instead of None when no logo file exists |
| `deployed/kdc/docker-compose.yml` | Remove `LOGO_FILENAME` env var if found |
| `deployed/kdc/app/instance/minipass.db` | Clear `LOGO_FILENAME` setting if found |
| `deployed/kdc/app/static/uploads/logo.png` | Delete if it's the LHGI logo |

---

## Important: Sync fixes back to local dev after VPS fixes work

Once VPS changes are confirmed working, the code fixes (Steps 2 and 3) need to be applied
to the local dev repo (`/home/kdresdell/Documents/DEV/minipass_env/app/`) and committed so
the next `upgrade_customers.py` run doesn't overwrite them.

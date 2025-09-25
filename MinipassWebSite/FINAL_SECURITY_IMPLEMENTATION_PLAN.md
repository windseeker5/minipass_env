# Final Security Implementation Plan for Minipass Controller
**Updated Version - For VPS Implementation**

## Context
- NO active customers
- NO running containers created by the application
- NO active email accounts
- Safe to delete old test data and implement directly on VPS

## Part 1: Cleanup (Safe to Delete)

### Delete Old Test Data
```bash
cd /path/to/minipass_env/MinipassWebSite
rm -rf config/user-patches/*  # Old test email forwarding configs - safe to delete
rm -f customers.db  # Old test database - will be recreated
```

## Part 2: Create Environment File

### Create .env file in MinipassWebSite directory
```bash
# Generate a strong secret key first:
python3 -c "import secrets; print(secrets.token_hex(32))"

# Create .env file
nano /path/to/minipass_env/MinipassWebSite/.env
```

### .env content:
```
SECRET_KEY=<paste-your-generated-64-character-hex-key-here>
STRIPE_SECRET_KEY=<your-stripe-secret-key>
STRIPE_PUBLISHABLE_KEY=<your-stripe-publishable-key>
STRIPE_WEBHOOK_SECRET=<your-webhook-secret>
MAIL_SERVER=<your-mail-server>
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=<your-mail-username>
MAIL_PASSWORD=<your-mail-password>
```

## Part 3: Code Changes

### File: app.py

#### Change 1: Import regex at top (add with other imports)
```python
import re
```

#### Change 2: Fix secret key and add session security (replace lines 32-33)
```python
# REPLACE line 32:
# OLD: app.secret_key = os.getenv("SECRET_KEY", "fallback123")
# NEW:
app.secret_key = os.getenv("SECRET_KEY")
if not app.secret_key:
    raise ValueError("SECRET_KEY environment variable is required! Create a .env file.")

# ADD these lines right after secret_key:
app.config.update(
    SESSION_COOKIE_SECURE=True,  # HTTPS only
    SESSION_COOKIE_HTTPONLY=True,  # No JS access
    SESSION_COOKIE_SAMESITE='Lax',  # CSRF protection
)
```

#### Change 3: Remove duplicate mail initialization (lines 39-40)
```python
# DELETE line 40: mail.init_app(app)
# KEEP only line 39: init_mail(app)
```

#### Change 4: Fix subdomain validation (line 67)
```python
# REPLACE:
# OLD: if not name or not name.isalnum():
# NEW:
subdomain_pattern = re.compile(r'^[a-z0-9][a-z0-9-]{0,61}[a-z0-9]$')
if not name or not subdomain_pattern.match(name):
```

#### Change 5: Clear session after checkout (after line 139)
```python
# ADD this line after the redirect on line 139:
session.pop('checkout_info', None)  # Clear sensitive data from session
```

### File: utils/customer_helpers.py

#### Change 6: Fix password storage (line 98)
```python
# Line 98 - REPLACE:
# OLD: password,  # ✅ plain-text for debugging
# NEW:
bcrypt.hashpw(password.encode(), bcrypt.gensalt()),  # Hashed password for security
```

#### Note: Line 102 stays the same
```python
# Line 102 - KEEP AS IS:
password,  # email_password needs plain text for mail server API
```

#### Change 7: Add bcrypt import at top if missing
```python
# Add at top with other imports if not already there:
import bcrypt
```

## Part 4: Testing After Implementation

### 1. Restart Flask Application
```bash
# If using systemd:
sudo systemctl restart minipass

# If using docker-compose:
cd /path/to/minipass_env
docker-compose down
docker-compose up -d

# If running directly:
# Kill the process and restart
```

### 2. Check Application Starts
```bash
# Check logs
tail -f /path/to/logs/app.log
# or
docker-compose logs -f minipass
```

### 3. Test with Stripe Test Mode
- Use Stripe test card: 4242 4242 4242 4242
- Any future expiry date
- Any 3-digit CVC
- Create a test subscription

### 4. Verify Security Fixes
```bash
# Check database has hashed passwords
sqlite3 customers.db
SELECT admin_password FROM customers LIMIT 1;
# Should show bcrypt hash like: $2b$12$...
```

## Part 5: Rollback Plan (If Something Goes Wrong)

```bash
# Save current state
git stash

# Revert to previous version
git checkout HEAD~1

# Restart application
sudo systemctl restart minipass  # or your restart method
```

## Implementation Checklist

- [ ] Pull latest code from git repository
- [ ] Delete old test data (config/user-patches/*, customers.db)
- [ ] Create .env file with all required variables
- [ ] Generate strong SECRET_KEY (64 characters)
- [ ] Make all 7 code changes
- [ ] Restart Flask application
- [ ] Test with Stripe test payment
- [ ] Verify passwords are hashed in database
- [ ] Monitor logs for any errors

## Notes
- All changes are backward compatible
- Database will be recreated automatically on first run
- Email forwarding configs will be recreated as new customers sign up
- Keep monitoring logs after deployment for any issues
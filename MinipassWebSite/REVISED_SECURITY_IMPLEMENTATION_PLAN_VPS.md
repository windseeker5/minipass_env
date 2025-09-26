# Revised Security Implementation Plan for VPS
**Updated for Actual VPS Environment - September 2024**

## Environment Analysis Summary

After analyzing your VPS environment, the original plan needs significant updates. Your VPS already has many components in place that weren't present on your local machine.

### ✅ Already Implemented on VPS
- **.env file exists** with all required environment variables
- **bcrypt library installed** and properly used in `deploy_helpers.py` for admin passwords
- **Customer database exists** (`customers.db`) with existing customer data
- **Mail configuration working** - no duplicate mail issues to resolve
- **No config/user-patches directory** - cleanup not needed

### ❌ Critical Security Vulnerabilities Found

1. **WEAK SECRET_KEY** (HIGH PRIORITY)
   - Current: `"my_flask_secret_123"`
   - Location: `.env` file line 5
   - Risk: Session hijacking, authentication bypass

2. **PLAINTEXT CUSTOMER PASSWORDS** (HIGH PRIORITY)
   - Location: `utils/customer_helpers.py` line 98
   - Risk: Password exposure if database is compromised

3. **MISSING SESSION SECURITY** (MEDIUM PRIORITY)
   - No HTTPS-only cookies
   - No HTTPOnly protection
   - No CSRF protection

4. **WEAK SUBDOMAIN VALIDATION** (MEDIUM PRIORITY)
   - Current: Only `isalnum()` check
   - Missing proper DNS-safe validation

5. **SESSION DATA LEAKAGE** (LOW PRIORITY)
   - Sensitive checkout data remains in session after payment

## Implementation Plan

### Part 1: Generate Strong Secret Key

```bash
# Generate new 64-character secret key
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
```

### Part 2: Update Environment File

**File: `.env`**
```bash
# Replace line 5:
# OLD: SECRET_KEY=my_flask_secret_123
# NEW: SECRET_KEY=<paste-your-generated-64-character-key-here>
```

### Part 3: Code Security Fixes

#### Fix 1: app.py - Import regex (add at top with other imports)
```python
import re
```

#### Fix 2: app.py - Secure SECRET_KEY validation (replace lines 32-33)
```python
# REPLACE:
# OLD: app.secret_key = os.getenv("SECRET_KEY", "fallback123")
# NEW:
app.secret_key = os.getenv("SECRET_KEY")
if not app.secret_key:
    raise ValueError("SECRET_KEY environment variable is required!")

# ADD session security settings right after:
app.config.update(
    SESSION_COOKIE_SECURE=True,    # HTTPS only
    SESSION_COOKIE_HTTPONLY=True,  # No JavaScript access
    SESSION_COOKIE_SAMESITE='Lax', # CSRF protection
)
```

#### Fix 3: app.py - Fix subdomain validation (replace line 67)
```python
# REPLACE:
# OLD: if not name or not name.isalnum():
# NEW:
subdomain_pattern = re.compile(r'^[a-z0-9][a-z0-9-]{0,61}[a-z0-9]$')
if not name or not subdomain_pattern.match(name):
```

#### Fix 4: app.py - Clear session after checkout (after line 139)
```python
# ADD this line after the redirect:
session.pop('checkout_info', None)  # Clear sensitive data
```

#### Fix 5: utils/customer_helpers.py - Hash customer passwords (line 98)
```python
# Add import at top if missing:
import bcrypt

# REPLACE line 98:
# OLD: password,  # ✅ plain-text for debugging
# NEW:
bcrypt.hashpw(password.encode(), bcrypt.gensalt()),  # Hashed password for security
```

**Note:** Line 102 stays the same (email_password needs plaintext for mail server)

## Part 4: Testing and Verification

### 1. Restart Application
```bash
# Find and restart your Flask process
sudo systemctl restart minipass  # if using systemd
# OR
pkill -f "python.*app.py" && python app.py &  # if running directly
```

### 2. Test New Customer Registration
- Use Stripe test card: `4242 4242 4242 4242`
- Create test subscription
- Verify deployment works

### 3. Verify Password Hashing
```bash
sqlite3 customers.db
SELECT admin_password FROM customers ORDER BY created_at DESC LIMIT 1;
# Should show bcrypt hash like: $2b$12$...
```

### 4. Check Logs
```bash
tail -f subscribed_app.log
# Monitor for any errors during testing
```

## Part 5: Rollback Plan

```bash
# Create backup first
cp app.py app.py.backup
cp utils/customer_helpers.py utils/customer_helpers.py.backup
cp .env .env.backup

# If issues occur, restore:
cp app.py.backup app.py
cp utils/customer_helpers.py.backup utils/customer_helpers.py
cp .env.backup .env
# Restart application
```

## Implementation Checklist

- [ ] Generate strong 64-character SECRET_KEY
- [ ] Update .env file with new SECRET_KEY
- [ ] Add `import re` to app.py
- [ ] Fix SECRET_KEY validation and add session security
- [ ] Update subdomain validation with regex pattern
- [ ] Add session cleanup after checkout
- [ ] Add bcrypt import to customer_helpers.py (if missing)
- [ ] Fix password hashing in customer_helpers.py line 98
- [ ] Create backups of modified files
- [ ] Restart Flask application
- [ ] Test with Stripe test payment
- [ ] Verify customer passwords are hashed in database
- [ ] Monitor logs for errors

## Risk Assessment

**RISK LEVEL: LOW**
- No customer data deletion required
- No database schema changes needed
- All changes are security improvements to existing working system
- Existing customers and deployments remain unaffected
- Rollback plan available if issues occur

## Key Differences from Original Plan

1. **No cleanup needed** - No old test data or config directories to remove
2. **Database preserved** - Existing customer data maintained
3. **Environment ready** - .env file already properly configured
4. **bcrypt available** - Library already installed and partially implemented
5. **Focus on vulnerabilities** - Targeted fixes for actual security issues found

## Post-Implementation Notes

- Monitor `subscribed_app.log` for 24 hours after implementation
- Test customer email functionality after changes
- Verify SSL certificates still work properly
- Check that existing customer applications remain accessible
- Update documentation if new security measures affect customer experience
# Password Reset Sync Debug Plan

## Problem Summary
Password reset works in KDC customer container but doesn't sync back to the main customer database in your admin tool.

## Root Cause Analysis (Production Investigation)
- ✅ KDC container password reset functionality works
- ✅ Environment variables properly configured:
  - `MINIPASS_SITE_URL=https://minipass.me`
  - `INTERNAL_API_SECRET=mp_internal_7f3a9b2e4c1d8f6a0e5b2c9d3a7f1e4b`
  - `APP_SUBDOMAIN=kdc`
- ❌ Sync endpoint `/internal/notify-password-reset` returns 404
- ❌ Flask app with sync API not accessible

## Debugging Steps for Localhost Development

### Step 1: Verify Local Environment Setup
```bash
cd /path/to/your/minipass_env/MinipassWebSite
source venv/bin/activate
python app.py
```
- Should start Flask app on localhost:5000
- Test endpoint: `curl -X POST http://localhost:5000/internal/notify-password-reset`

### Step 2: Test Sync Endpoint Locally
```bash
# Test with proper authentication
curl -X POST http://localhost:5000/internal/notify-password-reset \
  -H "Content-Type: application/json" \
  -d '{
    "subdomain": "kdc",
    "email": "test@example.com",
    "new_password": "testpass123",
    "secret": "mp_internal_7f3a9b2e4c1d8f6a0e5b2c9d3a7f1e4b"
  }'
```
Expected response: `{"ok": true}`

### Step 3: Verify Customer Database Update
```bash
cd /path/to/your/minipass_env/MinipassWebSite
sqlite3 customers.db "SELECT subdomain, admin_password FROM customers WHERE subdomain='kdc';"
```
- Check if password hash was updated

### Step 4: Test Full Container Sync Flow
1. Deploy a test customer container locally
2. Set environment variables in container:
   ```
   MINIPASS_SITE_URL=http://localhost:5000
   INTERNAL_API_SECRET=mp_internal_7f3a9b2e4c1d8f6a0e5b2c9d3a7f1e4b
   APP_SUBDOMAIN=testcustomer
   ```
3. Trigger password reset in container
4. Verify sync call reaches localhost Flask app

### Step 5: Production Deployment Investigation
Once localhost works, investigate production setup:

#### Check if Flask app should be running as service
```bash
# Check for systemd service
systemctl list-unit-files | grep minipass
systemctl list-unit-files | grep flask

# Check for supervisor/other process managers
ps aux | grep python | grep app.py
```

#### Check nginx configuration for API routing
```bash
# Look for Flask backend configuration
docker exec nginx-proxy cat /etc/nginx/conf.d/default.conf | grep -A20 -B5 "internal"

# Check if there should be separate API backend
docker ps | grep flask
```

#### Check docker-compose for Flask service
```bash
cd /home/kdresdell/minipass_env
cat docker-compose.yml | grep -A10 -B5 flask
cat docker-compose.yml | grep -A10 -B5 minipass
```

### Step 6: Fix Production Configuration

#### Option A: Add Flask API service to docker-compose
```yaml
# Add to docker-compose.yml
minipass-api:
  build: ./MinipassWebSite
  ports:
    - "5001:5000"
  environment:
    - VIRTUAL_HOST=minipass.me
    - VIRTUAL_PATH=/internal/
    - INTERNAL_API_SECRET=mp_internal_7f3a9b2e4c1d8f6a0e5b2c9d3a7f1e4b
  volumes:
    - ./MinipassWebSite:/app
```

#### Option B: Configure existing service to handle API
- Modify nginx routing to forward `/internal/*` to Flask backend
- Ensure Flask app runs alongside static content

## Testing Checklist
- [ ] Local Flask app starts successfully
- [ ] Sync endpoint responds correctly
- [ ] Customer database updates
- [ ] Container sync call works locally
- [ ] Production routing identified
- [ ] Production fix implemented
- [ ] End-to-end sync verified

## Notes
- Use localhost/dev environment for all testing
- Backup customer database before production changes
- Test with non-production customer data first
- Verify sync secret matches between container and API
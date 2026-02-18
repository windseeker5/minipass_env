# SITE_URL Fix Plan for Customer Email Images

## Problem
The MinipassWebSite deployment tool generates docker-compose.yml files **without SITE_URL**, causing broken email images for all customers.

## Solution

### 1. Fix the Deployment Script for Future Customers
**File**: `/home/kdresdell/minipass_env/MinipassWebSite/utils/deploy_helpers.py`

**Production Template (around line 810-817)**:
```yaml
environment:
  - FLASK_ENV=dev
  - SITE_URL=https://{app_name}.minipass.me  # ADD THIS LINE

  # ✅ NGINX reverse proxy support
  - VIRTUAL_HOST={app_name}.minipass.me
  - VIRTUAL_PORT=8889
  - LETSENCRYPT_HOST={app_name}.minipass.me
  - LETSENCRYPT_EMAIL=kdresdell@gmail.com
```

**Local Template (around line 851-852)**:
```yaml
environment:
  - FLASK_ENV=dev
  - SITE_URL=http://localhost:{port}  # ADD THIS LINE
```

### 2. Fix Existing Customer Deployments

#### Customer: heq
```bash
# Edit file: /home/kdresdell/minipass_env/deployed/heq/docker-compose.yml
# Add this line in environment section:
- SITE_URL=https://heq.minipass.me

# Restart container:
cd /home/kdresdell/minipass_env/deployed/heq
docker-compose down && docker-compose up -d
```

#### Customer: testdelancementmf
```bash
# Edit file: /home/kdresdell/minipass_env/deployed/testdelancementmf/docker-compose.yml
# Add this line in environment section:
- SITE_URL=https://testdelancementmf.minipass.me

# Restart container:
cd /home/kdresdell/minipass_env/deployed/testdelancementmf
docker-compose down && docker-compose up -d
```

#### Customer: demo
✅ **Already fixed** - SITE_URL=https://demo.minipass.me is working

### 3. Result
- ✅ All **future deployments** will have SITE_URL automatically
- ✅ All **existing customers** will have working email images
- ✅ Email images will show full URLs like `https://customer.minipass.me/activity/1/hero-image/newPass`

### 4. Verification
Test each customer's email images:
```bash
curl -I https://heq.minipass.me/activity/1/hero-image/newPass
curl -I https://testdelancementmf.minipass.me/activity/1/hero-image/newPass
curl -I https://demo.minipass.me/activity/1/hero-image/newPass  # Already working
```

All should return `HTTP/2 200`.
# Quick Customer Upgrade Guide

**⏱️ Time: 3-5 minutes | 📋 For auto-deployed customers like HEQ**

---

## 🎯 Customer Upgrade Process (4 Steps)

### 1️⃣ Connect to VPS & Navigate to Customer
```bash
ssh kdresdell@minipass.me -p 2222
cd /home/kdresdell/minipass_env/deployed/{CUSTOMER_NAME}

# Example for HEQ:
cd /home/kdresdell/minipass_env/deployed/heq
```

### 2️⃣ Update Customer App Code
```bash
# Navigate to customer's app directory
cd app

# Backup database (extra safety)
cp instance/minipass.db instance/minipass_backup_$(date +%Y%m%d_%H%M%S).db

# Pull latest code from main branch
git fetch origin main && git reset --hard origin/main
```

### 3️⃣ Upgrade Database (CRITICAL!)
```bash
# Still in app/ directory
python3 migrations/upgrade_production_database.py
flask db stamp head
cd ..
```

**Expected Output:** 8 tasks with ✅ checkmarks (or ⏭️ if already done)

### 4️⃣ Rebuild and Deploy Container
```bash
# Now in customer root directory (/deployed/{CUSTOMER_NAME}/)
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**Expected Output:**
- 🛑 Container stopped
- 🔨 Building new image
- 🚀 Container started

---

## 🔍 Verify Success

### Check Container Status
```bash
# Check if container is running
docker-compose ps

# Check container logs
docker-compose logs -f --tail 50

# Test customer site in browser
# https://{CUSTOMER_NAME}.minipass.me
# Example: https://heq.minipass.me
```

### Quick Health Check
```bash
# Test the application responds
curl -I https://{CUSTOMER_NAME}.minipass.me

# Expected: HTTP/1.1 200 OK or 302 redirect
```

---

## 🆘 If Something Goes Wrong

**Container won't start?**
```bash
docker-compose logs
# Look for Python errors or missing dependencies
```

**Database upgrade failed?**
```bash
# Database backup was created - restore if needed
cd app
cp instance/minipass_backup_YYYYMMDD_HHMMSS.db instance/minipass.db
```

**Need to rollback completely?**
```bash
# Reset to previous git state
cd app
git reflog  # Find previous commit
git reset --hard {PREVIOUS_COMMIT_ID}
cd ..
docker-compose down && docker-compose up -d
```

---

## 📝 Customer Directory Structure

```
/deployed/{CUSTOMER_NAME}/
├── docker-compose.yml     # Customer-specific compose file
└── app/                   # Customer's app code (copied from main template)
    ├── instance/
    │   └── minipass.db    # Customer's database (persistent)
    ├── dockerfile         # Customer's Dockerfile
    └── [rest of app files]
```

---

## 🔄 Automated vs Manual Deployments

| Type | Location | Upgrade Method |
|------|----------|----------------|
| **LHGI (Test)** | `/home/kdresdell/minipass_env/app` | Use `./deploy-lghi-vps.sh` |
| **Customers (HEQ, etc)** | `/deployed/{customer}/` | Use this guide |

---

## ⚠️ Important Notes

- ✅ Database is SAFE - volume mounted outside container
- ✅ Customer-specific configurations preserved in docker-compose.yml
- ✅ Each customer runs on unique subdomain and port
- ✅ SSL certificates automatically managed by nginx proxy
- ⚠️ MUST run database upgrade BEFORE rebuilding container
- ⚠️ Each customer deployment is independent - upgrade one at a time

---

## 🎯 Current Deployed Customers

- **HEQ** (Hockey Est du Quebec): https://heq.minipass.me
  - Location: `/deployed/heq/`
  - Container: `minipass_heq`

---

## 🔗 Related Commands

```bash
# List all deployed customers
ls -la /home/kdresdell/minipass_env/deployed/

# Check all customer containers
docker ps | grep minipass_

# View main infrastructure
docker-compose ps  # (from main minipass_env directory)

# Update main template (affects future deployments)
cd /home/kdresdell/minipass_env/app && git pull origin main
```

---

## 🚨 Emergency Contacts

- **Developer**: Ken Dresdell (kdresdell@gmail.com)
- **Repository**: Main branch at `/home/kdresdell/minipass_env/`
- **Infrastructure**: Nginx proxy + Let's Encrypt + Mail server
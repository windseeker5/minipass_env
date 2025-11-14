# 🧪 LOCAL TESTING GUIDE
## Testing Git-Based Deployment Workflow on Your Development Machine

This guide shows you how to test the complete Stripe → Deployment workflow on your local machine **without** needing the VPS infrastructure (nginx proxy, docker-mailserver, SSL, etc.).

---

## 🎯 What Gets Tested Locally

### ✅ Fully Tested (90% of deployment)
- ✅ Stripe webhook integration
- ✅ Git clone from GitHub repository
- ✅ .env file generation with tier configuration
- ✅ Python dependencies installation
- ✅ Database migration (clean single migration)
- ✅ Admin user creation
- ✅ Organization setup
- ✅ Docker image build
- ✅ Docker container deployment
- ✅ Container accessibility via localhost
- ✅ App functionality (login, features)

### ⚠️ Skipped in Local Mode
- ⚠️ Email account creation (logged but not executed)
- ⚠️ Deployment email notification (saved to file instead)
- ⚠️ SSL/Let's Encrypt certificates
- ⚠️ nginx reverse proxy integration

**Why this is safe:** The email creation code hasn't changed - it's already working on your VPS. We're only testing the NEW git-based deployment code.

---

## 📋 Prerequisites

### 1. Stripe CLI Installed
```bash
# Check if installed
stripe --version

# If not installed on Arch Linux:
yay -S stripe-cli
# or
paru -S stripe-cli
```

### 2. MinipassWebSite Running
```bash
cd /home/kdresdell/Documents/DEV/minipass_env/MinipassWebSite
source venv/bin/activate
python app.py
# Should be running on http://localhost:5000
```

### 3. Docker Running
```bash
docker --version
docker info  # Verify Docker daemon is running
```

---

## 🚀 Local Testing Workflow

### Step 1: Start Stripe CLI (Terminal 1)

```bash
# Forward Stripe webhooks to your local server
stripe listen --forward-to localhost:5000/webhook

# You should see:
# > Ready! Your webhook signing secret is whsec_xxx (^C to quit)
#
# IMPORTANT: Copy the webhook secret (starts with whsec_)
```

**Note:** Keep this terminal open - it needs to stay running!

### Step 2: Update Stripe Webhook Secret (if needed)

If the webhook secret changed, update your `.env` file:

```bash
# Edit .env file
nano /home/kdresdell/Documents/DEV/minipass_env/MinipassWebSite/.env

# Update this line:
STRIPE_WEBHOOK_SECRET=whsec_YOUR_NEW_SECRET_HERE

# Save and exit (Ctrl+X, Y, Enter)
```

### Step 3: Start MinipassWebSite (Terminal 2)

```bash
cd /home/kdresdell/Documents/DEV/minipass_env/MinipassWebSite
source venv/bin/activate
python app.py

# You should see:
# * Running on http://127.0.0.1:5000
# 🌍 Environment: LOCAL (Development)  # ← This confirms local mode!
```

### Step 4: Trigger Test Payment

#### Option A: Via Web Interface (Recommended)
1. Open browser to http://localhost:5000
2. Click on a subscription plan (1 Activité / 15 Activités / 100 Activités)
3. Choose billing frequency (Mensuel / Annuel)
4. Fill out the form:
   - App Name: `testapp` (or any unique name)
   - Organization Name: `Test Organization`
   - Admin Email: `test@example.com`
   - Forwarding Email: `your-real-email@example.com`
5. Click "S'inscrire" (Sign up)
6. Use Stripe test card: **4242 4242 4242 4242**
   - Expiry: Any future date (e.g., 12/25)
   - CVC: Any 3 digits (e.g., 123)
   - ZIP: Any 5 digits (e.g., 12345)
7. Complete the checkout

#### Option B: Via Stripe CLI (Quick Test)
```bash
# In Terminal 3
stripe trigger checkout.session.completed
```

### Step 5: Watch the Deployment

In Terminal 2 (MinipassWebSite), you'll see:

```
📩 Stripe webhook received
🌍 Environment: LOCAL (Development)  ← Confirms local mode detection!
🚀 Starting operation: Deploy Customer Container
📦 Step 1: Cloning app repository from GitHub
   💻 Command: git clone git@github.com:windseeker5/dpm.git
✅ Repository clone completed
⚙️ Step 2a: Creating .env file with tier 1 configuration
✅ .env file created
📦 Step 2b: Installing application dependencies
✅ Dependencies installation completed (59 packages)
🗄️ Step 2c: Initializing database schema
   Running flask db upgrade to create database schema
✅ Database schema created (22 tables)
🔐 Step 2d: Configuring admin user and organization
✅ Admin user created: test@example.com
✅ Organization set: Test Organization
🐳 Step 3: Writing docker-compose.yml
   📝 Generating LOCAL docker-compose.yml (direct port mapping)
   🌐 App will be accessible at: http://localhost:9100
✅ Docker compose file created
🚀 Step 4: Deploying container
   💻 Command: docker-compose up -d
✅ Container deployment completed

⚠️ LOCAL MODE: Skipping email account creation
   📧 Would create: testapp_app@minipass.me
   📧 Would forward to: your-real-email@example.com

⚠️ LOCAL MODE: Skipping deployment email
   📄 Deployment info saved to: deployed/testapp/DEPLOYMENT_INFO.txt
   🌐 Access app at: http://localhost:9100
   👤 Admin login: test@example.com / [password]

✅ Deployment completed successfully!
```

### Step 6: Verify the Deployment

#### A. Check Container is Running
```bash
docker ps | grep minipass

# You should see:
# minipass_testapp   ...   Up X minutes   0.0.0.0:9100->8889/tcp
```

#### B. Check Deployment Info File
```bash
cat /home/kdresdell/Documents/DEV/minipass_env/deployed/testapp/DEPLOYMENT_INFO.txt

# You'll see:
# ===========================================
# MINIPASS DEPLOYMENT INFO (LOCAL TEST)
# ===========================================
#
# App Name: testapp
# App URL: http://localhost:9100
#
# ADMIN CREDENTIALS:
#   Email: test@example.com
#   Password: [password]
#
# EMAIL ACCOUNT (NOT CREATED IN LOCAL MODE):
#   Email: testapp_app@minipass.me
#   ...
```

#### C. Check Database Structure
```bash
sqlite3 /home/kdresdell/Documents/DEV/minipass_env/deployed/testapp/app/instance/minipass.db ".tables"

# You should see all 22 tables:
# Organization       chat_message       organizations      setting
# activity           chat_usage         passport           signup
# admin              ebank_payment      passport_type      survey
# admin_action_log   email_log          query_log          survey_response
# alembic_version    expense            redemption         survey_template
# chat_conversation  income             reminder_log       user
```

#### D. Verify Admin User
```bash
sqlite3 /home/kdresdell/Documents/DEV/minipass_env/deployed/testapp/app/instance/minipass.db \
  "SELECT id, email FROM admin;"

# Should show:
# 1|test@example.com
```

#### E. Verify Organization
```bash
sqlite3 /home/kdresdell/Documents/DEV/minipass_env/deployed/testapp/app/instance/minipass.db \
  "SELECT id, name FROM Organization;"

# Should show:
# 1|Test Organization
```

### Step 7: Access the Deployed App

1. **Open browser** to the URL shown in the logs (e.g., http://localhost:9100)
2. You should see the **Minipass login page**
3. **Login** with the admin credentials from DEPLOYMENT_INFO.txt
4. **Test app functionality:**
   - ✅ Dashboard loads
   - ✅ Create an activity
   - ✅ Add a user
   - ✅ Generate a passport
   - ✅ Check reports
   - ✅ Test settings

---

## 🔍 Verification Checklist

After deployment completes, verify each item:

### Deployment Process
- [ ] Container is running: `docker ps | grep minipass_testapp`
- [ ] No errors in Terminal 2 (Flask logs)
- [ ] Logs show "LOCAL (Development)" environment
- [ ] DEPLOYMENT_INFO.txt file created in deployed/testapp/

### Database
- [ ] Database file exists: `deployed/testapp/app/instance/minipass.db`
- [ ] All 22 tables created (use `.tables` in sqlite3)
- [ ] Admin user exists with correct email
- [ ] Organization name is set correctly
- [ ] alembic_version shows correct migration ID

### Docker Container
- [ ] Container built successfully
- [ ] Container is running (not exited)
- [ ] Port mapping is correct (e.g., 9100:8889)
- [ ] Container logs show no errors: `docker logs minipass_testapp`

### Application
- [ ] App is accessible at http://localhost:PORT
- [ ] Login page loads correctly
- [ ] Admin login works
- [ ] Dashboard displays
- [ ] Can create an activity
- [ ] Can add a user
- [ ] Settings page accessible

### Logs and Files
- [ ] subscribed_app.log has no critical errors
- [ ] .env file created in deployed/testapp/app/
- [ ] docker-compose.yml uses local configuration (no proxy network)
- [ ] Git repository cloned (has .git folder)

---

## 🛠️ Troubleshooting

### Issue: Port Already in Use
```
Error: port is already allocated
```

**Solution:**
```bash
# Find what's using the port
sudo lsof -i :9100

# Stop the container using that port
docker stop minipass_previous-app

# Or remove it completely
docker rm -f minipass_previous-app

# Or let the system assign next available port automatically
```

### Issue: Git Clone Fails
```
ERROR: Repository not found or access denied
```

**Solution:**
```bash
# Test SSH access to GitHub
ssh -T git@github.com

# You should see:
# Hi windseeker5! You've successfully authenticated

# If authentication fails, check your SSH keys:
ssh-add -l

# Add your key if needed:
ssh-add ~/.ssh/id_rsa
```

### Issue: Database Migration Fails
```
ERROR: No such table: income
```

**Solution:**
```bash
# This means the old problematic migration was cloned
# Make sure your Git repo has the clean migration

# Check migration file in cloned repo:
ls deployed/testapp/app/migrations/versions/

# Should only have:
# f4c10e5088aa_initial_schema_clean_migration_from_.py

# If you see old migrations, your Git repo needs to be updated
cd /home/kdresdell/Documents/DEV/minipass_env/app
git pull origin main
```

### Issue: Docker Build Fails
```
ERROR: Cannot locate specified Dockerfile
```

**Solution:**
```bash
# Check dockerfile exists in cloned repo
ls deployed/testapp/app/dockerfile

# Check Docker is running
docker info

# Check Docker disk space
docker system df

# Clean up if needed
docker system prune -a
```

### Issue: Container Exits Immediately
```
Container exited with code 1
```

**Solution:**
```bash
# Check container logs
docker logs minipass_testapp

# Common issues:
# - Missing dependencies (should be installed in Step 2b)
# - Database connection errors
# - Port already in use inside container

# Restart container with logs visible
cd deployed/testapp
docker-compose up
# (without -d flag to see output)
```

### Issue: Can't Access App in Browser
```
This site can't be reached
```

**Solution:**
```bash
# Verify container is running
docker ps | grep minipass_testapp

# Check port mapping
docker port minipass_testapp

# Should show:
# 8889/tcp -> 0.0.0.0:9100

# Try accessing with explicit localhost
http://127.0.0.1:9100

# Check if firewall is blocking
sudo ufw status
```

---

## 🧹 Cleanup After Testing

### Remove Single Test Deployment
```bash
# Stop and remove container
cd /home/kdresdell/Documents/DEV/minipass_env/deployed/testapp
docker-compose down

# Remove deployment directory
cd ..
rm -rf testapp

# Remove from customers database
sqlite3 /home/kdresdell/Documents/DEV/minipass_env/MinipassWebSite/customers.db
DELETE FROM customers WHERE subdomain = 'testapp';
.quit
```

### Remove All Test Deployments
```bash
# Stop all minipass containers
docker ps -a | grep minipass | awk '{print $1}' | xargs docker rm -f

# Remove all test deployment directories
rm -rf /home/kdresdell/Documents/DEV/minipass_env/deployed/test*

# Clean customers database
sqlite3 /home/kdresdell/Documents/DEV/minipass_env/MinipassWebSite/customers.db
DELETE FROM customers WHERE subdomain LIKE 'test%';
.quit
```

---

## 📊 Environment Detection

The system automatically detects whether it's running on:

### PRODUCTION (VPS)
- Has `minipass_env_proxy` Docker network
- Uses nginx reverse proxy
- Creates real email accounts
- Sends deployment emails
- Uses SSL/Let's Encrypt

### LOCAL (Development)
- No `minipass_env_proxy` network
- Direct port mapping
- Skips email creation (logged only)
- Saves deployment info to file
- No SSL needed (HTTP)

You can verify detection:
```bash
# Check if production network exists
docker network ls | grep minipass_env_proxy

# VPS: Will show the network
# Local: Won't show anything (triggers local mode)
```

---

## 🎯 Configuration Differences

| Feature | Production (VPS) | Local (Dev) |
|---------|------------------|-------------|
| **App URL** | https://app-name.minipass.me | http://localhost:PORT |
| **Docker Network** | minipass_env_proxy (nginx) | Default bridge |
| **Port Access** | Via nginx reverse proxy | Direct mapping (9100:8889) |
| **Email Creation** | Real account on docker-mailserver | Skipped (logged only) |
| **Deployment Email** | Sent via Flask-Mail | Saved to DEPLOYMENT_INFO.txt |
| **SSL** | Let's Encrypt automatic | Not needed (HTTP) |
| **Environment Vars** | VIRTUAL_HOST, LETSENCRYPT_* | None (direct access) |
| **Detection** | Auto (has proxy network) | Auto (no proxy network) |

---

## ✅ Testing All Plan Tiers

Test all subscription tiers to ensure they work correctly:

| Test # | Plan | Frequency | Expected Port | Expected Tier | Amount (CAD) |
|--------|------|-----------|---------------|---------------|--------------|
| 1 | 1 Activité | Mensuel | 9100 | TIER=1 | $20 |
| 2 | 1 Activité | Annuel | 9101 | TIER=1 | $120 |
| 3 | 15 Activités | Mensuel | 9102 | TIER=2 | $50 |
| 4 | 15 Activités | Annuel | 9103 | TIER=2 | $300 |
| 5 | 100 Activités | Mensuel | 9104 | TIER=3 | $120 |
| 6 | 100 Activités | Annuel | 9105 | TIER=3 | $720 |

**Use unique app names for each test:**
- `test-basic-monthly`, `test-basic-annual`
- `test-pro-monthly`, `test-pro-annual`
- `test-ultimate-monthly`, `test-ultimate-annual`

---

## 📝 Success Criteria

Your local test is **successful** if:

1. ✅ Stripe webhook triggers deployment
2. ✅ Git clone completes without errors
3. ✅ Dependencies install successfully (59 packages)
4. ✅ Database is created with all 22 tables
5. ✅ Admin user can login
6. ✅ Organization name is set correctly
7. ✅ App is accessible at localhost:PORT
8. ✅ App functionality works (create activities, users, passports)
9. ✅ Logs show "LOCAL (Development)" mode
10. ✅ DEPLOYMENT_INFO.txt contains correct details
11. ✅ No critical errors in subscribed_app.log

**If all these pass, you're ready to test on VPS!**

---

## 🚀 Moving to Production Testing

After successful local testing:

### Step 1: Push Changes to GitHub
```bash
cd /home/kdresdell/Documents/DEV/minipass_env/MinipassWebSite
git add -A
git commit -m "Add local testing support with environment detection"
git push origin main
```

### Step 2: Pull Changes on VPS
```bash
# SSH into VPS
ssh user@your-vps.com

# Pull latest code
cd /path/to/MinipassWebSite
git pull origin main

# Restart Flask app
sudo systemctl restart minipass  # if using systemd
# or
pkill -f "python app.py" && python app.py &  # if running manually
```

### Step 3: Test with ONE Real Customer
1. Use test customer email (not real customer)
2. Use Stripe test mode
3. Verify complete workflow:
   - ✅ Git clone works on VPS
   - ✅ Dependencies install
   - ✅ Database migration succeeds
   - ✅ Email account is created
   - ✅ Deployment email is sent
   - ✅ SSL certificate works
   - ✅ App accessible via https://subdomain.minipass.me

### Step 4: Production Ready!
If VPS test succeeds:
- ✅ System is production-ready
- ✅ Can accept real customers
- ✅ Switch to Stripe live mode when ready

---

## 📚 Additional Resources

- **Deployment Workflow:** See `Docs/deployment_workflow.md`
- **Stripe Setup:** See `Docs/STRIPE_IMPLEMENTATION_PLAN.md`
- **Docker Logs:** `docker logs minipass_[app_name]`
- **Application Logs:** `tail -f subscribed_app.log`
- **Stripe Dashboard:** https://dashboard.stripe.com (Test mode)

---

## 🆘 Need Help?

### Check Logs
```bash
# Deployment logs
tail -100 subscribed_app.log

# Container logs
docker logs minipass_testapp

# Flask app logs (in Terminal 2)
# Watch in real-time as deployment happens
```

### Common Commands
```bash
# List all deployments
ls -la deployed/

# Check database
sqlite3 customers.db "SELECT subdomain, plan, tier, deployed FROM customers;"

# Check running containers
docker ps | grep minipass

# Stop a container
docker stop minipass_testapp

# Remove a container
docker rm -f minipass_testapp
```

---

**Happy Testing! 🧪**

Remember: Local testing is fast, safe, and lets you iterate quickly. Test thoroughly here before deploying to VPS!

# Local Testing Guide for MiniPass Stripe Integration

## Overview
This guide will help you test the multi-tier subscription system on your local development machine (Arch Linux) using Stripe test mode.

---

## Prerequisites

You're currently in **Stripe Test Mode** (the keys in your `.env` start with `pk_test_` and `sk_test_`). This is perfect for testing - you won't be charged real money!

---

## Step 1: Install Stripe CLI (Arch Linux)

The Stripe CLI lets you forward webhook events from Stripe to your local Flask app (even though you're behind a firewall).

### Installation Options:

**Option A: Using AUR (Recommended)**
```bash
# Install using yay or paru
yay -S stripe-cli
# or
paru -S stripe-cli
```

**Option B: Manual Download**
```bash
# Download the latest release
cd ~/Downloads
wget https://github.com/stripe/stripe-cli/releases/download/v1.19.5/stripe_1.19.5_linux_x86_64.tar.gz

# Extract
tar -xvf stripe_1.19.5_linux_x86_64.tar.gz

# Move to /usr/local/bin
sudo mv stripe /usr/local/bin/

# Verify installation
stripe --version
```

---

## Step 2: Authenticate Stripe CLI

```bash
# Login to Stripe (will open browser)
stripe login

# This will:
# 1. Open your browser
# 2. Ask you to allow access
# 3. Give you a pairing code
# 4. Authenticate the CLI with your Stripe account
```

**You should see:**
```
Your pairing code is: word-word-word
Press Enter to open the browser or visit https://dashboard.stripe.com/stripecli/confirm_auth?t=...

> Done! The Stripe CLI is configured for your account
```

---

## Step 3: Verify Your Stripe Configuration

Check that your `.env` file has the correct test keys:

```bash
cd /home/kdresdell/Documents/DEV/minipass_env/MinipassWebSite
cat .env | grep STRIPE
```

**You should see (with your actual test keys):**
```
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_BASIC_MONTHLY=price_...
STRIPE_PRICE_BASIC_ANNUAL=price_...
STRIPE_PRICE_PRO_MONTHLY=price_...
STRIPE_PRICE_PRO_ANNUAL=price_...
STRIPE_PRICE_ULTIMATE_MONTHLY=price_...
STRIPE_PRICE_ULTIMATE_ANNUAL=price_...
```

✅ **All set!** These test keys are safe to use locally.

---

## Step 4: Start Your Local Flask App

Open **Terminal 1**:

```bash
cd /home/kdresdell/Documents/DEV/minipass_env/MinipassWebSite

# Activate virtual environment (if you have one)
source venv/bin/activate  # or wherever your venv is

# Start Flask
python app.py
```

**You should see:**
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

✅ **Keep this terminal open** - your Flask app is running!

---

## Step 5: Forward Webhooks to Your Local App

Open **Terminal 2** (new terminal window):

```bash
cd /home/kdresdell/Documents/DEV/minipass_env/MinipassWebSite

# Forward Stripe webhooks to your local Flask app
stripe listen --forward-to localhost:5000/webhook
```

**You should see:**
```
> Ready! You are using Stripe API Version [2024-XX-XX]. Your webhook signing secret is whsec_... (^C to quit)
```

**IMPORTANT:** Copy the webhook signing secret that starts with `whsec_...`

### Update Your .env with the New Webhook Secret

The Stripe CLI generates a NEW webhook secret for local testing. Update your `.env`:

```bash
# Open .env in your editor
nano .env  # or vim, or your favorite editor

# Find the line:
STRIPE_WEBHOOK_SECRET=whsec_QxzSBbRpFeUKkgANCMos5majO0pcT9DL

# Replace with the NEW secret from Terminal 2:
STRIPE_WEBHOOK_SECRET=whsec_[NEW_SECRET_FROM_STRIPE_LISTEN]

# Save and exit
```

**RESTART your Flask app** in Terminal 1 (Ctrl+C, then `python app.py` again) to load the new webhook secret.

✅ **Keep Terminal 2 open** - it's forwarding webhooks to your local app!

---

## Step 6: Test a Payment Flow

### What You'll Test:
Let's test **Basic Monthly** ($20 CAD)

### Steps:

1. **Open your browser:** http://localhost:5000

2. **Click on "1 Activité"** (Basic plan)

3. **Make sure toggle is on "Mensuel"** (Monthly)

4. **Fill out the form:**
   - App Name: `testbasic` (or any unique name)
   - Organization Name: `Test Organization`
   - Admin Email: `your-email@example.com`

5. **Click "S'inscrire"** (Sign up)

6. **You'll be redirected to Stripe Checkout**

7. **Use Stripe test card:**
   - Card number: `4242 4242 4242 4242`
   - Expiry: Any future date (e.g., `12/34`)
   - CVC: Any 3 digits (e.g., `123`)
   - ZIP: Any 5 digits (e.g., `12345`)

8. **Click "Pay"**

---

## Step 7: Watch the Logs

### In Terminal 1 (Flask App):
You should see:
```
💳 Creating checkout session: plan=basic, frequency=monthly, price_id=price_...
```

### In Terminal 2 (Stripe CLI):
You should see:
```
[200] POST http://localhost:5000/webhook [evt_1...]
```

### Check Subscription Log:
```bash
tail -f subscribed_app.log
```

You should see the full deployment process:
- Webhook received
- Metadata extracted (plan, tier, billing_frequency)
- Container deployment
- Database record created
- Email setup

---

## Step 8: Verify the Deployment

### Check Database:
```bash
sqlite3 customers.db

SELECT subdomain, plan, billing_frequency, tier, payment_amount/100 as amount_dollars
FROM customers;

.quit
```

**Expected output:**
```
testbasic|basic|monthly|1|20.0
```

### Check Deployed Container:
```bash
ls -la deployed/testbasic/

# Should show:
# - docker-compose.yml
# - app/ (directory)
```

### Inspect docker-compose.yml:
```bash
cat deployed/testbasic/docker-compose.yml | grep TIER
```

**Expected output:**
```
              - TIER=1
              - BILLING_FREQUENCY=monthly
```

✅ **SUCCESS!** The TIER is set correctly!

### Check if Container is Running:
```bash
docker ps --filter name=minipass_testbasic
```

**You should see:**
```
CONTAINER ID   IMAGE     ...   NAMES
abc123def456   ...       ...   minipass_testbasic
```

---

## Step 9: Test All 6 Payment Flows

Now repeat Step 6 for all combinations:

| Test # | Plan | Toggle | Amount | Expected Tier |
|--------|------|--------|--------|---------------|
| 1 | 1 Activité | Mensuel | $20 | TIER=1 |
| 2 | 1 Activité | Annuel | $120 | TIER=1 |
| 3 | 15 Activités | Mensuel | $50 | TIER=2 |
| 4 | 15 Activités | Annuel | $300 | TIER=2 |
| 5 | 100 Activités | Mensuel | $120 | TIER=3 |
| 6 | 100 Activités | Annuel | $720 | TIER=3 |

**Use unique app names for each test:**
- `test1monthly`, `test1annual`
- `test2monthly`, `test2annual`
- `test3monthly`, `test3annual`

---

## Troubleshooting

### Problem: Webhook not received

**Check Terminal 2** - is `stripe listen` still running?

```bash
# Restart webhook forwarding
stripe listen --forward-to localhost:5000/webhook
```

**Copy the NEW webhook secret** and update `.env`, then restart Flask.

---

### Problem: "Subdomain already taken"

```bash
# Delete the test customer from database
sqlite3 customers.db

DELETE FROM customers WHERE subdomain = 'testbasic';

.quit
```

Or use a different app name.

---

### Problem: Flask app crashes

**Check the error** in Terminal 1.

**Common issues:**
- Missing environment variable → Check `.env` has all Stripe Price IDs
- Database locked → Close any open SQLite connections
- Port already in use → Kill the process using port 5000

```bash
# Kill process on port 5000
sudo lsof -t -i:5000 | xargs kill -9

# Restart Flask
python app.py
```

---

### Problem: Can't see Stripe CLI logs

Make sure you're in **Test Mode** in Stripe Dashboard:
1. Go to https://dashboard.stripe.com
2. Check top-left corner - should say "Test mode"
3. If it says "Live mode", toggle to Test mode

---

## Quick Reference: Testing Checklist

Before each test:
- [ ] Terminal 1: Flask app running (http://localhost:5000)
- [ ] Terminal 2: `stripe listen` running
- [ ] Terminal 3: `tail -f subscribed_app.log` (optional, for logs)
- [ ] `.env` has the webhook secret from stripe listen
- [ ] Stripe Dashboard in Test mode

For each payment flow:
- [ ] Correct plan selected
- [ ] Correct billing frequency (toggle)
- [ ] Unique app name
- [ ] Test card: 4242 4242 4242 4242
- [ ] Payment completes
- [ ] Webhook received (check Terminal 2)
- [ ] Database record created with correct tier
- [ ] Container deployed with TIER env var

---

## After Testing Locally: Deploy to VPS

Once all 6 payment flows work locally, you're ready to deploy to your VPS!

### On Your VPS:

1. **Pull the latest code:**
```bash
cd /path/to/MinipassWebSite
git pull origin main
```

2. **Restart Flask app:**
```bash
# If using systemd
sudo systemctl restart minipass

# If running manually
pkill -f "python app.py"
python app.py
```

3. **Configure Stripe webhook endpoint:**
   - Go to https://dashboard.stripe.com/webhooks
   - Add endpoint: `https://minipass.me/webhook`
   - Select event: `checkout.session.completed`
   - Copy the webhook signing secret
   - Update `.env` on VPS with the production webhook secret

4. **Test with real Stripe test mode:**
   - Use the same test card on your live VPS
   - Verify webhooks are received
   - Check logs on VPS

---

## Important Notes

### Test Mode vs Live Mode

**Test Mode (current):**
- Keys start with `pk_test_` and `sk_test_`
- Use test card 4242 4242 4242 4242
- No real charges
- Perfect for development

**Live Mode (production):**
- Keys start with `pk_live_` and `sk_live_`
- Real credit cards
- Real charges
- Only use when ready for customers!

### Your VPS is Currently in Test Mode

Based on your `.env`, your VPS is also using test keys. This is **good** for testing! When you're ready to accept real customers:

1. Create Live Products/Prices in Stripe Dashboard (Live mode)
2. Get Live API keys
3. Update `.env` on VPS with live keys
4. Configure live webhook endpoint
5. Test thoroughly before announcing to customers!

---

## Summary

**Quick Start (TL;DR):**

```bash
# Terminal 1: Flask
cd /home/kdresdell/Documents/DEV/minipass_env/MinipassWebSite
python app.py

# Terminal 2: Stripe CLI
stripe listen --forward-to localhost:5000/webhook
# Copy the whsec_... secret, update .env, restart Flask

# Browser
# Visit http://localhost:5000
# Use card: 4242 4242 4242 4242
# Test all 6 payment flows!
```

---

## Need Help?

If something doesn't work:
1. Check Terminal 1 for Flask errors
2. Check Terminal 2 for webhook delivery
3. Check `subscribed_app.log` for deployment details
4. Verify `.env` has all required values
5. Make sure Stripe Dashboard is in Test mode

Happy testing! 🚀

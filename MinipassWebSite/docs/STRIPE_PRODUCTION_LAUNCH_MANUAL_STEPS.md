# MiniPass Stripe Production Launch - Manual Steps

## Overview

This document contains the manual steps required to launch Stripe in production mode on your VPS (minipass.me).

**Your Setup:**
- **Local machine:** Development/testing with TEST keys (keep as-is)
- **VPS (minipass.me):** Production server - will receive LIVE keys

---

## Pre-Launch Checklist

### Already Completed
- [x] Stripe Account Activated (acct_1IPFwuGrhkirXbsP)
- [x] LIVE Products Created in Stripe
- [x] LIVE Prices Created in Stripe
- [x] Webhook code production-ready in app.py
- [x] `.env.production` template created locally
- [x] LIVE Webhook Endpoint Created (`MiniPass Production`)

### Needs Manual Action
- [ ] Step 1: Retrieve LIVE API Keys from Stripe Dashboard
- [ ] Step 2: Copy Webhook Signing Secret (webhook already created)
- [ ] Step 3: Deploy to Production VPS
- [ ] Step 4: Verify Production

---

## Step 1: Copy Your LIVE API Keys from Stripe Dashboard

**You're already in LIVE mode and your keys exist!** (confirmed from your screenshot)

1. Go to: https://dashboard.stripe.com/apikeys (you're already there)

2. **Copy Publishable Key:**
   - Find the row labeled "Publishable key" under "Standard keys"
   - Your key starts with: `pk_live_51IPFwuGrhkirXbsP...`
   - Click the copy icon or select and copy the full key

3. **Copy Secret Key:**
   - Find the row labeled "Secret key" (shows `sk_live_...L7e4`)
   - Click the **"..."** menu on the right side of that row
   - Select **"Reveal live key"** or click directly on the key to reveal it
   - Copy the full secret key (starts with `sk_live_...`)
   - **IMPORTANT:** Save this somewhere secure - you'll need it for Step 3

| Key Type | Your Key | Action |
|----------|----------|--------|
| Publishable key | `pk_live_51IPFwuGrhkirXbsP...` | Copy (fully visible) |
| Secret key | `sk_live_...L7e4` | Click to reveal, then copy |

---

## Step 2: Copy Webhook Signing Secret

**The webhook endpoint is already created!**

| Webhook Name | Endpoint URL | Events |
|--------------|--------------|--------|
| MiniPass Production | `https://minipass.me/webhook` | 4 events configured |

**Get your signing secret:**

1. Go to: https://dashboard.stripe.com/webhooks
2. **Ensure you're in LIVE MODE** (top-right corner)
3. Click on the **"MiniPass Production"** webhook endpoint
4. Find **"Signing secret"** section
5. Click **"Reveal"**
6. Copy the `whsec_...` value - you'll need it for Step 3

---

## Step 3: Deploy to Production VPS

### 3.1 SSH to your VPS

```bash
ssh user@minipass.me
```

### 3.2 Navigate to project directory

```bash
cd /path/to/MinipassWebSite
```

### 3.3 Backup current database

```bash
cp customers.db customers.db.backup.$(date +%Y%m%d_%H%M%S)
```

### 3.4 Backup current .env as .env.test

```bash
cp .env .env.test
```

### Update the file by the example

scp -P 2222 /home/kdresdell/Documents/DEV/minipass_env/MinipassWebSite/.env.production kdresdell@minipass.me:/home/kdresdell/minipass_env/MinipassWebSite/.env.production    



### 3.5 Update .env with LIVE credentials

Edit the `.env` file:

```bash
nano .env
```

Replace the contents with the following (fill in your actual values):

```env
# Flask Configuration
SECRET_KEY=166701d6a2c46085619cd304721f37fe644a1e1916a1d2ad1bb0632c92219630
FLASK_ENV=production

# Stripe LIVE Keys (from Step 1)
STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_ACTUAL_KEY_HERE
STRIPE_SECRET_KEY=sk_live_YOUR_ACTUAL_KEY_HERE

# Stripe Webhook Secret (from Step 2)
STRIPE_WEBHOOK_SECRET=whsec_YOUR_ACTUAL_SECRET_HERE

# Stripe LIVE Price IDs (already created - use exactly as shown)
STRIPE_PRICE_BASIC_MONTHLY=price_1SV1gpGrhkirXbsPpZYSgZwp
STRIPE_PRICE_BASIC_ANNUAL=price_1SV1gpGrhkirXbsPygpv6QkE
STRIPE_PRICE_PRO_MONTHLY=price_1SV1gbGrhkirXbsPNyMFCfUE
STRIPE_PRICE_PRO_ANNUAL=price_1SV1gbGrhkirXbsPMQ72KWjR
STRIPE_PRICE_ULTIMATE_MONTHLY=price_1SV1gLGrhkirXbsPzBIcLfuz
STRIPE_PRICE_ULTIMATE_ANNUAL=price_1SV1gLGrhkirXbsPBeQtyedT

# Production Email Configuration
MAIL_SERVER=mail.minipass.me
MAIL_PORT=587
MAIL_USERNAME=support@minipass.me
MAIL_PASSWORD=YOUR_SUPPORT_EMAIL_PASSWORD
MAIL_DEFAULT_SENDER=minipass <support@minipass.me>

PROD_MAIL_SERVER=mail.minipass.me
PROD_MAIL_PORT=587
PROD_MAIL_USERNAME=support@minipass.me
PROD_MAIL_PASSWORD=YOUR_SUPPORT_EMAIL_PASSWORD
PROD_MAIL_DEFAULT_SENDER=minipass <support@minipass.me>

# Admin Tools
ADMIN_PASSWORD=YOUR_SECURE_ADMIN_PASSWORD
```

### 3.6 Verify keys are LIVE (not test)

```bash
grep "STRIPE_SECRET_KEY" .env
# Output MUST show: sk_live_...

grep "STRIPE_PUBLISHABLE_KEY" .env
# Output MUST show: pk_live_...
```

### 3.7 Restart your application

Depending on your setup:

```bash
# If using systemctl
sudo systemctl restart minipass

# If using docker-compose
docker-compose restart

# If using gunicorn directly
pkill gunicorn && gunicorn app:app -b 0.0.0.0:5000 -D
```

---

## Step 4: Verify Production

### 4.1 Test checkout with real card

1. Visit https://minipass.me
2. Select a plan and proceed to checkout
3. Use a **REAL credit card** (NOT the test card 4242 4242 4242 4242)
4. Complete the payment

### 4.2 Check Stripe Dashboard (Live Mode)

1. Go to https://dashboard.stripe.com/payments
2. Ensure you're in **LIVE MODE**
3. Verify the payment appears and shows "Succeeded"

### 4.3 Check Webhook Delivery

1. Go to https://dashboard.stripe.com/webhooks
2. Click on your `https://minipass.me/webhook` endpoint
3. Check "Recent deliveries" - should show "Succeeded"

### 4.4 Verify Application Response

Check on your VPS:

- [ ] Customer record created in `customers.db`
- [ ] Docker container deployed for customer
- [ ] Deployment email sent to customer

```bash
# Check customer database
sqlite3 customers.db "SELECT * FROM customers ORDER BY created_at DESC LIMIT 1;"

# Check running containers
docker ps | grep customer_subdomain

# Check logs
tail -f subscribed_app.log
```

### 4.5 Clean Up Test

1. **Refund the test payment** in Stripe Dashboard
2. **Delete the test deployment** from your VPS:

```bash
# Remove test customer container
docker stop customer_subdomain && docker rm customer_subdomain

# Remove from database
sqlite3 customers.db "DELETE FROM customers WHERE subdomain='test_subdomain';"
```

---

## Quick Reference: LIVE Price IDs

Copy these exactly into your production `.env`:

```env
STRIPE_PRICE_BASIC_MONTHLY=price_1SV1gpGrhkirXbsPpZYSgZwp
STRIPE_PRICE_BASIC_ANNUAL=price_1SV1gpGrhkirXbsPygpv6QkE
STRIPE_PRICE_PRO_MONTHLY=price_1SV1gbGrhkirXbsPNyMFCfUE
STRIPE_PRICE_PRO_ANNUAL=price_1SV1gbGrhkirXbsPMQ72KWjR
STRIPE_PRICE_ULTIMATE_MONTHLY=price_1SV1gLGrhkirXbsPzBIcLfuz
STRIPE_PRICE_ULTIMATE_ANNUAL=price_1SV1gLGrhkirXbsPBeQtyedT
```

---

## Important: Existing Test Customers

If you have containers deployed during sandbox testing, they will continue to work after switching to LIVE keys.

**What keeps working:**
- Deployed containers run independently (no Stripe connection)
- Customers can log in and use their apps

**What won't work for TEST customers:**
- Cancel subscription button (Stripe error - test subscription doesn't exist in live mode)
- Automatic renewals (test subscriptions don't send webhooks to live endpoint)

**Recommended fix for beta testers:**
```bash
# Extend their subscription manually on VPS
sqlite3 customers.db "UPDATE customers SET subscription_end_date='2030-01-01' WHERE subdomain='their_subdomain';"
```

If they want to cancel later, handle it manually by deleting their container and database record.

---

## Troubleshooting

### Webhook returns 400/500 errors

1. Check webhook secret matches exactly
2. Verify endpoint URL is correct (https, not http)
3. Check VPS logs: `tail -f subscribed_app.log`

### Payment succeeds but no deployment

1. Check webhook delivery in Stripe Dashboard
2. Check application logs for errors
3. Verify database has customer record

### "Invalid signature" error

Your `STRIPE_WEBHOOK_SECRET` doesn't match. Get the correct one from:
Stripe Dashboard → Webhooks → Your endpoint → Signing secret → Reveal

---

## Files Reference

| Location | File | Purpose |
|----------|------|---------|
| Local Dev | `.env` | TEST keys (keep unchanged) |
| Local Dev | `.env.production` | Template for production |
| VPS | `.env` | LIVE keys (update this) |
| VPS | `.env.test` | Backup of test config |

---

## Support

If you encounter issues:
1. Check `subscribed_app.log` on VPS
2. Check Stripe Dashboard webhook logs
3. Verify all environment variables are set correctly

# MiniPass Production Launch Guide
## Transitioning from Stripe Test Mode to Live Mode

**Created:** 2025-01-15
**Status:** Ready for Production Launch
**Estimated Time:** ~35 minutes

---

## Key Concepts

### Test vs Live Mode

Your Stripe account has **4 API keys** total:
- **2 for Test Mode** (sandbox): `sk_test_...` and `pk_test_...`
- **2 for Live Mode**: `sk_live_...` and `pk_live_...`

**Important Facts:**
- Test and Live modes are **completely separate** - data doesn't transfer between them
- Products, Prices, and Customers created in test mode **don't exist** in live mode
- Your sandbox **stays active forever** - you keep it for testing new features
- You can continue testing locally with test keys even after going live
- This is normal - all Stripe users maintain both test and live environments

---

## Pre-Launch Checklist

### 1. Activate Your Stripe Account

- [ ] Complete business verification in Stripe Dashboard
- [ ] Add bank account for payouts
- [ ] Verify your business information is correct
- [ ] Ensure your account is fully activated for live payments

### 2. Retrieve Your Live API Keys

1. Go to [Stripe Dashboard](https://dashboard.stripe.com/apikeys)
2. Toggle from **Test Mode** to **Live Mode** (toggle in top right corner)
3. Copy your **Live** keys:
   - **Publishable key**: `pk_live_...` (safe to expose in frontend)
   - **Secret key**: `sk_live_...` ⚠️ **Shown only once! Save immediately!**
4. Store them securely in your password manager or KMS

**Security Note:** If you lose the live secret key, you cannot retrieve it. You'll need to rotate it and create a new one.

### 3. Create Products & Prices in Live Mode

**CRITICAL:** Products and Prices from test mode don't exist in live mode. You must recreate them.

#### Steps:

1. Switch to **Live Mode** in Stripe Dashboard (toggle in top right)
2. Navigate to **Products** → **Add product**

#### Products to Create:

**Product 1: MiniPass Basic**
- Name: `MiniPass Basic`
- Description: `1 Activity - Perfect for individual organizers`

**Product 2: MiniPass Pro**
- Name: `MiniPass Pro`
- Description: `15 Activities - Ideal for growing organizations`

**Product 3: MiniPass Ultimate**
- Name: `MiniPass Ultimate`
- Description: `100 Activities - Enterprise solution`

#### Prices to Create (6 total):

For each product, create 2 prices:

| Product | Billing | Amount | Price Name |
|---------|---------|--------|------------|
| Basic | Monthly | $20 CAD | Basic Monthly |
| Basic | Annual | $120 CAD | Basic Annual |
| Pro | Monthly | $50 CAD | Pro Monthly |
| Pro | Annual | $300 CAD | Pro Annual |
| Ultimate | Monthly | $120 CAD | Ultimate Monthly |
| Ultimate | Annual | $720 CAD | Ultimate Annual |

**Configuration:**
- Currency: `CAD`
- Billing period: One-time payment (or Recurring if switching to subscriptions)
- Tax behavior: Not taxable (adjust based on your requirements)

#### Record the Price IDs:

After creating each price, copy its Price ID (`price_...`). You'll need all 6 for step 4.

**Price ID Reference:**
```
STRIPE_PRICE_BASIC_MONTHLY=price_______________
STRIPE_PRICE_BASIC_ANNUAL=price_______________
STRIPE_PRICE_PRO_MONTHLY=price_______________
STRIPE_PRICE_PRO_ANNUAL=price_______________
STRIPE_PRICE_ULTIMATE_MONTHLY=price_______________
STRIPE_PRICE_ULTIMATE_ANNUAL=price_______________
```

### 4. Update Your Production `.env` File

Create a **new `.env.production`** file (keep your `.env` for local testing):

```env
# Flask Configuration
SECRET_KEY=<GENERATE_NEW_PRODUCTION_SECRET_KEY>
FLASK_ENV=production

# Stripe LIVE Keys (CRITICAL - use pk_live_ and sk_live_)
STRIPE_SECRET_KEY=sk_live_XXXXXXXXXXXXXXXXXXXXX
STRIPE_PUBLISHABLE_KEY=pk_live_XXXXXXXXXXXXXXXXXXXXX
STRIPE_WEBHOOK_SECRET=whsec_XXXXXXXXXXXXXXXXXXXXX  # Get this in step 5

# Stripe LIVE Price IDs (from step 3)
STRIPE_PRICE_BASIC_MONTHLY=price_XXXXXXXXXXXXX
STRIPE_PRICE_BASIC_ANNUAL=price_XXXXXXXXXXXXX
STRIPE_PRICE_PRO_MONTHLY=price_XXXXXXXXXXXXX
STRIPE_PRICE_PRO_ANNUAL=price_XXXXXXXXXXXXX
STRIPE_PRICE_ULTIMATE_MONTHLY=price_XXXXXXXXXXXXX
STRIPE_PRICE_ULTIMATE_ANNUAL=price_XXXXXXXXXXXXX

# Email Configuration (same as before)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_specific_password
MAIL_DEFAULT_SENDER=info@minipass.me
```

**Important:**
- Generate a NEW `SECRET_KEY` for production (use: `python -c "import secrets; print(secrets.token_hex(32))"`)
- Double-check all keys start with `sk_live_` and `pk_live_` (NOT `sk_test_`)
- Save this file securely - it contains sensitive credentials

### 5. Set Up Live Webhook Endpoint

**CRITICAL:** Test and Live webhooks are completely separate!

#### Steps:

1. Go to [Stripe Webhooks Dashboard](https://dashboard.stripe.com/webhooks)
2. Switch to **Live Mode** (toggle in top right)
3. Click **Add endpoint** button
4. Configure endpoint:
   - **Endpoint URL**: `https://minipass.me/webhook`
   - **Description**: `MiniPass Production Webhook`
   - **Events to send**: Select `checkout.session.completed`
   - **API Version**: Latest (or match your test webhook version)
5. Click **Add endpoint**
6. Click on the newly created endpoint
7. Click **Signing secret** → **Reveal**
8. Copy the `whsec_...` value
9. Add it to `.env.production` as `STRIPE_WEBHOOK_SECRET`

#### Webhook Security:

Your webhook handler in `app.py` already verifies signatures:
```python
event = stripe.Webhook.construct_event(
    payload, sig_header, webhook_secret
)
```

This prevents unauthorized webhook calls.

### 6. Verify Frontend Configuration

**File:** `templates/index.html` (or wherever Stripe.js is initialized)

Ensure your frontend uses the environment variable for the publishable key:

```javascript
// Should be using Jinja2 template variable:
const stripe = Stripe('{{ stripe_publishable_key }}');

// NOT hardcoded like:
// const stripe = Stripe('pk_test_...'); ❌
```

**Verify in `app.py`:**
```python
# Should be reading from environment
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
stripe_publishable_key = os.getenv('STRIPE_PUBLISHABLE_KEY')

# Pass to template
@app.route('/')
def index():
    return render_template('index.html',
                         stripe_publishable_key=stripe_publishable_key)
```

---

## Launch Day Deployment

### Step 1: Deploy Code with Production Environment

```bash
# SSH into your production server
ssh user@your-production-server

# Navigate to project directory
cd /home/kdresdell/Documents/DEV/minipass_env/MinipassWebSite

# Backup current production database
cp customers.db customers.db.backup.$(date +%Y%m%d_%H%M%S)

# Update code (if needed)
git pull origin main

# Copy production environment file
cp .env.production .env

# Verify the file was copied correctly
grep "STRIPE_SECRET_KEY" .env
# Should output: STRIPE_SECRET_KEY=sk_live_...

# Restart your Flask application
# (Your exact command may vary based on setup)

# Option A: If using systemd
sudo systemctl restart minipass

# Option B: If using docker-compose
docker-compose down && docker-compose up -d

# Option C: If running Flask directly
# Kill existing process and restart
pkill -f "python app.py"
python app.py &

# Check application is running
curl http://localhost:5000  # Should return homepage
```

### Step 2: Verify Live Mode is Active

#### Check 1: Environment Variables
```bash
# On production server
grep "STRIPE_SECRET_KEY" .env
# Should show: sk_live_... (NOT sk_test_)

grep "STRIPE_PUBLISHABLE_KEY" .env
# Should show: pk_live_... (NOT pk_test_)
```

#### Check 2: Test the Complete Payment Flow

**IMPORTANT:** Use a real credit card (test cards won't work in live mode!)

1. Visit https://minipass.me
2. Click "S'inscrire" (Sign up)
3. Select **Basic Monthly** plan ($20)
4. Fill in the form:
   - Subdomain: `testlaunch` (or any unique name)
   - Organization: `Test Launch Org`
   - Email: Your real email
5. Click through to Stripe Checkout
6. Enter **real credit card** details:
   - Use your own card for testing
   - Test cards like `4242 4242 4242 4242` will NOT work
7. Complete the payment
8. Wait for redirect to success page

#### Check 3: Verify Everything Worked

**In Stripe Dashboard:**
- [ ] Switch to **Live Mode**
- [ ] Go to [Payments](https://dashboard.stripe.com/payments)
- [ ] Verify payment appears with status "Succeeded"
- [ ] Go to [Webhooks](https://dashboard.stripe.com/webhooks)
- [ ] Click on your webhook endpoint
- [ ] Verify `checkout.session.completed` event shows "Succeeded"

**In Your Application:**
- [ ] Check `subscribed_app.log`:
  ```bash
  tail -50 subscribed_app.log
  # Look for: "✅ Deployment complete for testlaunch"
  ```
- [ ] Verify customer record created:
  ```bash
  sqlite3 customers.db "SELECT * FROM customers WHERE subdomain='testlaunch';"
  ```
- [ ] Check Docker container is running:
  ```bash
  docker ps | grep testlaunch
  ```

**In Email:**
- [ ] Check your email for deployment notification
- [ ] Verify credentials are included
- [ ] Test login at `https://testlaunch.minipass.me`

**In Customer App:**
- [ ] Visit `https://testlaunch.minipass.me`
- [ ] Log in with credentials from email
- [ ] Verify TIER=1 enforcement (can only create 1 activity)

#### Check 4: Clean Up Test Payment

After verification succeeds:

1. **Refund the test payment:**
   - Go to [Stripe Dashboard → Payments (Live)](https://dashboard.stripe.com/payments)
   - Find your $20 test payment
   - Click on it → **Refund** → **Refund $20.00**

2. **Delete the test deployment:**
   ```bash
   cd /home/kdresdell/Documents/DEV/minipass_env/MinipassWebSite
   python manage_app.py
   # Select and delete 'testlaunch'
   ```

### Step 3: Monitor Production Logs

```bash
# Watch logs in real-time
tail -f subscribed_app.log

# Check for errors
grep "ERROR" subscribed_app.log | tail -20

# Check webhook processing
grep "checkout.session.completed" subscribed_app.log | tail -10
```

---

## Post-Launch Monitoring

### First 24 Hours
- [ ] Monitor `subscribed_app.log` continuously
- [ ] Check Stripe Dashboard for webhook delivery status
- [ ] Test at least 2-3 signups with different plans
- [ ] Verify all emails are being sent correctly
- [ ] Test each tier's activity limits

### First Week
- [ ] Daily check of Stripe Dashboard for failed webhooks
- [ ] Review all customer deployments for errors
- [ ] Monitor email delivery rates
- [ ] Test pro and ultimate tier signups

### Ongoing
- [ ] Set up Stripe email notifications for:
  - Failed payments
  - Disputes
  - Webhook failures
- [ ] Weekly review of `subscribed_app.log`
- [ ] Monthly review of successful deployments vs. payments
- [ ] Keep test mode active for developing new features

### Stripe Dashboard Monitoring

**Key Pages to Bookmark:**
- [Live Payments](https://dashboard.stripe.com/payments)
- [Live Webhooks](https://dashboard.stripe.com/webhooks)
- [Live Customers](https://dashboard.stripe.com/customers)
- [Live Logs](https://dashboard.stripe.com/logs)

**Set Up Alerts:**
1. Go to [Settings → Notifications](https://dashboard.stripe.com/settings/notifications)
2. Enable email notifications for:
   - Failed webhook deliveries
   - Disputes opened
   - Payment failures

---

## Rollback Plan

If something goes wrong during launch:

### Emergency Rollback Steps

```bash
# 1. SSH to production server
ssh user@your-production-server

# 2. Navigate to project
cd /home/kdresdell/Documents/DEV/minipass_env/MinipassWebSite

# 3. Restore test environment
cp .env.test .env
# OR restore from backup:
# cp .env.backup .env

# 4. Restart application
sudo systemctl restart minipass
# OR: docker-compose down && docker-compose up -d

# 5. Verify test mode is active
grep "STRIPE_SECRET_KEY" .env
# Should show: sk_test_... (NOT sk_live_)

# 6. Test with test card
# Visit site and try checkout with: 4242 4242 4242 4242
```

### Post-Rollback
- [ ] Notify any customers who attempted payment
- [ ] Investigate root cause in logs
- [ ] Fix issues in test environment
- [ ] Re-test thoroughly before attempting launch again

---

## Local Development Setup

**IMPORTANT:** Keep using test mode locally! You'll maintain two separate environments:

### Local Development Environment

**File:** `.env` (on your local laptop)
```env
# Keep test keys for local dev
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_... (test webhook)

# Test Price IDs
STRIPE_PRICE_BASIC_MONTHLY=price_... (test)
STRIPE_PRICE_BASIC_ANNUAL=price_... (test)
# etc.
```

### Production Server Environment

**File:** `.env` (on production server)
```env
# Live keys for production
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_... (live webhook)

# Live Price IDs
STRIPE_PRICE_BASIC_MONTHLY=price_... (live)
STRIPE_PRICE_BASIC_ANNUAL=price_... (live)
# etc.
```

### Development Workflow

1. **Develop new features locally** using test keys and test cards
2. **Test thoroughly** in test mode
3. **Deploy to production** with live keys
4. **Monitor** production logs

This way you can safely test new features without affecting real customers!

---

## Common Questions

### Q: Do I need to recreate all 6 Products and Prices manually?
**A:** Yes, but it only takes ~10 minutes using the Stripe Dashboard or MCP tools. Test mode and live mode are completely separate.

### Q: Will my test data transfer to live mode?
**A:** No. Test customers, payments, products, and prices stay in test mode. Live mode starts completely fresh with no data.

### Q: Can I switch back to test mode after going live?
**A:** Yes! Just swap the API keys in your `.env` file. Both modes coexist independently.

### Q: What if I accidentally use test keys in production?
**A:** Payments will fail (test cards don't work with live keys, real cards don't work with test keys), and you'll see errors immediately in logs and Stripe Dashboard.

### Q: Should I delete my test Products/Prices?
**A:** No! Keep them for local development and testing new features. You'll use them forever.

### Q: What happens to the webhook endpoint in test mode?
**A:** Nothing. Test and live webhook endpoints are separate. Your test webhook continues working for local development.

### Q: Do I need to change my code?
**A:** No! Your code already uses environment variables. You just swap the `.env` file.

### Q: How do I test live mode locally?
**A:** You can temporarily use live keys in your local `.env`, but be careful - you'll create real charges! Better to test on a staging server.

### Q: What if my first real payment fails?
**A:** Check webhook logs in Stripe Dashboard. Common issues:
- Webhook URL not accessible (firewall, SSL issues)
- Webhook signature verification fails (wrong secret)
- Application error (check `subscribed_app.log`)

### Q: Can I have both test and live running simultaneously?
**A:** Not on the same server with the same code, since `.env` determines the mode. But you can have:
- Local dev (test mode)
- Production server (live mode)

---

## Troubleshooting

### Issue: Webhook returns 500 error

**Symptoms:**
- Payment succeeds but no deployment
- Webhook shows "Failed" in Stripe Dashboard

**Solutions:**
1. Check `subscribed_app.log` for errors
2. Verify webhook secret matches `.env`
3. Ensure application is running
4. Check webhook URL is accessible: `curl https://minipass.me/webhook`

### Issue: Payment succeeds but wrong tier deployed

**Symptoms:**
- Customer paid for Pro but got Basic limits

**Solutions:**
1. Verify Price IDs in `.env` match Stripe Dashboard
2. Check webhook metadata extraction in logs
3. Verify `PLAN_TO_TIER` mapping in `app.py`

### Issue: "No such price" error

**Symptoms:**
- Checkout fails with Stripe error
- Error mentions Price ID not found

**Solutions:**
1. Verify you created Prices in **Live Mode** (not test mode)
2. Double-check Price IDs in `.env.production`
3. Ensure you're using the correct Price IDs (copy from Stripe Dashboard)

### Issue: Test cards still working (shouldn't happen in live)

**Symptoms:**
- Card `4242 4242 4242 4242` works in production

**Solutions:**
1. **CRITICAL:** You're using test keys in production!
2. Immediately check `.env`:
   ```bash
   grep "STRIPE_SECRET_KEY" .env
   ```
3. If it shows `sk_test_`, you need to switch to live keys
4. Follow rollback plan to use correct keys

---

## Emergency Contacts & Resources

### Stripe Support
- **Dashboard:** https://dashboard.stripe.com
- **Support:** https://support.stripe.com (24/7 for live mode issues)
- **Status Page:** https://status.stripe.com
- **Documentation:** https://docs.stripe.com

### Monitoring URLs
- **Webhook Monitoring:** https://dashboard.stripe.com/webhooks
- **API Request Logs:** https://dashboard.stripe.com/logs
- **Payment Logs:** https://dashboard.stripe.com/payments
- **Event Logs:** https://dashboard.stripe.com/events

### Key Documentation
- [Going Live Checklist](https://docs.stripe.com/get-started/checklist/go-live)
- [Webhook Best Practices](https://docs.stripe.com/webhooks#best-practices)
- [Testing in Production](https://docs.stripe.com/testing#testing-interactively)

---

## Launch Checklist Summary

### Pre-Launch (Do Days Before)
- [ ] Activate Stripe account fully
- [ ] Retrieve live API keys and store securely
- [ ] Create 3 Products in live mode
- [ ] Create 6 Prices in live mode
- [ ] Record all 6 Price IDs
- [ ] Create `.env.production` file
- [ ] Set up live webhook endpoint
- [ ] Record webhook secret
- [ ] Verify frontend uses environment variable for publishable key

### Launch Day (Do During Deployment)
- [ ] Backup production database
- [ ] Update code if needed (`git pull`)
- [ ] Copy `.env.production` to `.env`
- [ ] Restart application
- [ ] Verify environment shows `sk_live_` keys
- [ ] Test complete payment flow with real card
- [ ] Verify payment in Stripe Dashboard
- [ ] Verify webhook fired successfully
- [ ] Verify deployment completed
- [ ] Verify customer app works with tier limits
- [ ] Refund test payment
- [ ] Delete test deployment

### Post-Launch (Do After)
- [ ] Monitor logs for 24 hours
- [ ] Set up Stripe email alerts
- [ ] Test all 6 pricing tiers within first week
- [ ] Document any issues encountered
- [ ] Keep test mode active for future development

---

## Success Criteria

Your launch is successful when:

✅ Real payments process and appear in Stripe Live Dashboard
✅ Webhooks fire and show "Succeeded" status
✅ Customer containers deploy automatically
✅ Customers receive deployment emails
✅ Customers can log in and use their apps
✅ Tier limits enforce correctly (1/15/100 activities)
✅ No errors in `subscribed_app.log`
✅ All 6 pricing options work correctly

---

## Timeline Estimate

**Total Time: ~35 minutes + testing**

| Task | Time |
|------|------|
| Activate Stripe account | 5 min (if already done) |
| Retrieve live API keys | 2 min |
| Create 3 Products | 5 min |
| Create 6 Prices | 10 min |
| Create `.env.production` | 5 min |
| Set up live webhook | 5 min |
| Deploy to production | 5 min |
| Test payment flow | 10 min |
| Verify and clean up | 5 min |
| **Total** | **~35 minutes** |

**Testing Period:** Plan for 1-2 days of monitoring after launch.

---

## Final Notes

**Remember:**
- The switch itself is simple - just swapping API keys and Price IDs
- The important part is thorough testing
- Keep test mode active forever for development
- Monitor closely for the first week
- Don't panic if something goes wrong - you can always rollback

**You've got this! 🚀**

Good luck with your launch!

---

**Document Version:** 1.0
**Last Updated:** 2025-01-15
**Related Documents:** `STRIPE_IMPLEMENTATION_PLAN.md`

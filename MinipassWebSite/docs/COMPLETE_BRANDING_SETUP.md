# ✅ Complete Your Stripe Branding Setup

## Current Status

✅ **Logo uploaded successfully to Stripe!**
- File ID: `file_1SWjL8GhJsN3FLG4Z2BtsHQC`
- Account: `acct_1RVfdVGhJsN3FLG4` (minipass_dev)

Now you just need to configure it in your Dashboard (takes 2 minutes).

---

## Quick Setup Steps

### Step 1: Configure Logo in Stripe Dashboard

1. **Open this link in your browser:**
   👉 https://dashboard.stripe.com/settings/branding

2. **Make sure you're in TEST MODE** (toggle in top-right corner)

3. **Under "Icon & Logo" section:**
   - Click **"Upload logo"** or **"Upload icon"**
   - Select the file: `/home/kdresdell/mp-logo-regular.png`
   - Wait for upload to complete (should take a few seconds)

   **Alternatively**, if the logo doesn't appear:
   - The logo with File ID `file_1SWjL8GhJsN3FLG4Z2BtsHQC` is already in your Stripe account
   - Click on the logo upload area and it may show in your recently uploaded files

4. **Preview**: You should see your Minipass logo in the preview on the right side

### Step 2: Set Business Name

1. **Open this link:**
   👉 https://dashboard.stripe.com/settings/public

2. **Under "Business details" section:**
   - Find the **"Business name"** field
   - Enter: `MiniPass - Simplified Activity Management`
   - Click **"Save"**

### Step 3: Verify Your Settings

1. Return to: https://dashboard.stripe.com/settings/branding
2. Confirm you see:
   - ✅ Your Minipass logo in the preview
   - ✅ Business name: "MiniPass - Simplified Activity Management"

---

## 🧪 Test Your Branded Checkout

### Test the Checkout Flow

1. **Start your Flask app** (if not already running):
   ```bash
   cd /home/kdresdell/Documents/DEV/minipass_env/MinipassWebSite
   python3 app.py
   ```

2. **Open your website**: http://localhost:5000

3. **Select any subscription plan**:
   - Basic ($20/month or $10/month annual)
   - Pro ($50/month or $25/month annual)
   - Ultimate ($60/month or $120/month annual)

4. **Fill out the signup form**:
   - App name: (anything)
   - Organization: (anything)
   - Email: test@example.com
   - Password: (anything)
   - Click **"Subscribe"**

5. **You'll be redirected to Stripe Checkout**:
   - ✅ You should see your **Minipass logo** at the top!
   - ✅ You should see **"MiniPass - Simplified Activity Management"**
   - ✅ Professional, branded checkout page!

### Use Stripe Test Cards

For testing (Test Mode only):
- **Success**: `4242 4242 4242 4242`
- **Decline**: `4000 0000 0000 0002`
- **3D Secure**: `4000 0027 6000 3184`

Use:
- Any future expiration (e.g., `12/25`)
- Any 3-digit CVC (e.g., `123`)
- Any valid ZIP code (e.g., `12345`)

---

## 🚀 Going Live (When Ready)

When you're ready to switch to production:

1. **Switch to LIVE MODE** in Stripe Dashboard (toggle in top-right)
2. **Repeat the same setup**:
   - Upload logo at: https://dashboard.stripe.com/settings/branding
   - Set business name at: https://dashboard.stripe.com/settings/public
3. Test and Live modes have separate branding configurations

---

## ✨ Where Your Branding Appears

Once configured, your Minipass logo and business name will automatically appear on:

- ✅ Checkout pages (when customers subscribe)
- ✅ Payment Links (if you create any)
- ✅ Customer Portal (for managing subscriptions)
- ✅ Hosted Invoice Pages
- ✅ Invoice PDFs
- ✅ Email receipts sent by Stripe

**No code changes needed!** Your existing code in `app.py` already works with the branding.

---

## 📸 What It Should Look Like

Before and After:

**BEFORE**: Plain Stripe checkout
- Generic "Subscribe" header
- No logo
- No business name

**AFTER**: Branded Minipass checkout
- **Minipass logo** at the top
- **"MiniPass - Simplified Activity Management"** displayed
- Professional, trustworthy appearance

---

## 🐛 Troubleshooting

### Logo doesn't appear

**Solutions**:
1. Make sure you're in **TEST MODE** (matches where you configured branding)
2. Hard refresh your browser: `Ctrl + Shift + R` (Windows/Linux) or `Cmd + Shift + R` (Mac)
3. Try incognito/private browsing mode
4. Wait 1-2 minutes for branding to propagate

### Business name doesn't show

**Solutions**:
1. Verify you saved the business name at: https://dashboard.stripe.com/settings/public
2. Refresh the checkout page
3. Wait 1-2 minutes for changes to take effect

### "Test mode" vs "Live mode" confusion

**Remember**:
- **Test Mode** = Sandbox, for testing only (test cards work)
- **Live Mode** = Production, real money (real cards only)
- They have **separate branding configurations**
- You must configure branding in BOTH modes

---

## 📁 Files Reference

- **Logo File**: `/home/kdresdell/mp-logo-regular.png`
- **Stripe File ID**: `file_1SWjL8GhJsN3FLG4Z2BtsHQC`
- **Upload Script**: `upload_logo_to_stripe.py`
- **Main App**: `app.py` (checkout session at lines 154-206)

---

## 🎯 Summary

You're almost done! Just two quick steps:

1. ✅ Logo uploaded to Stripe ← **DONE!**
2. ⏳ Configure in Dashboard ← **Do this now** (2 minutes)
3. ⏳ Test the checkout page ← **Verify it works**

**Next**: Open https://dashboard.stripe.com/settings/branding and follow Step 1 above!

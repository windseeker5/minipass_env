# Stripe Checkout Branding Setup Guide

This guide will help you add the Minipass logo and branding to your Stripe checkout pages.

## Quick Summary

- **Logo**: `/home/kdresdell/mp-logo-regular.png` (✅ Verified: 613×109px, PNG, 12KB)
- **Business Name**: "MiniPass - Simplified Activity Management"
- **Colors**: Using Stripe defaults (no custom colors)
- **Method**: Dashboard configuration (applies to all checkouts automatically)

---

## Method 1: Automated Upload (Recommended)

### Step 1: Run the Upload Script

```bash
cd /home/kdresdell/Documents/DEV/minipass_env/MinipassWebSite
python3 upload_logo_to_stripe.py
```

This script will:
1. Upload your logo to Stripe
2. Configure your account branding settings
3. Set the business name to "MiniPass - Simplified Activity Management"

### Expected Output

```
============================================================
Stripe Branding Configuration Script
============================================================

[Step 1/2] Uploading logo to Stripe...
Uploading logo from: /home/kdresdell/mp-logo-regular.png
✅ Logo uploaded successfully!
   File ID: file_xxxxxxxxxxxxx
   URL: https://files.stripe.com/...

[Step 2/2] Updating account branding...
   Business Name: MiniPass - Simplified Activity Management
   Logo File ID: file_xxxxxxxxxxxxx
✅ Branding settings updated successfully!

============================================================
✅ SUCCESS! Your Stripe checkout is now branded!
============================================================
```

---

## Method 2: Manual Dashboard Configuration

If you prefer to upload manually or encounter any issues with the script:

### Step 1: Access Stripe Dashboard

1. Go to: https://dashboard.stripe.com/settings/branding
2. Make sure you're in **Test Mode** (toggle in top right) to test first

### Step 2: Upload Logo

1. Under **"Icon & Logo"** section:
   - Click **"Upload logo"**
   - Select `/home/kdresdell/mp-logo-regular.png`
   - Wait for upload to complete

### Step 3: Set Business Name

1. Go to: https://dashboard.stripe.com/settings/public
2. Under **"Business details"**:
   - Set **"Business name"** to: `MiniPass - Simplified Activity Management`
   - Save changes

### Step 4: Verify Settings

1. Return to: https://dashboard.stripe.com/settings/branding
2. Confirm your logo appears in the preview
3. Confirm business name is displayed correctly

---

## Testing Your Branded Checkout

### Test in Sandbox Mode

1. Make sure Stripe is in **Test Mode** (toggle in Dashboard)
2. Go to your website: http://localhost:5000 (or your test URL)
3. Select any subscription plan (Basic, Pro, or Ultimate)
4. Fill out the signup form
5. Click "Subscribe" to proceed to checkout

### What You Should See

On the Stripe checkout page, you should now see:

✅ **Your Minipass logo** at the top of the page
✅ **Business name**: "MiniPass - Simplified Activity Management"
✅ Professional, branded checkout experience

### Test with Stripe Test Cards

Use these test card numbers:
- **Success**: `4242 4242 4242 4242`
- **Decline**: `4000 0000 0000 0002`
- **3D Secure**: `4000 0027 6000 3184`

- Use any future expiration date (e.g., 12/25)
- Use any 3-digit CVC
- Use any valid ZIP code

---

## Branding Applies To

Once configured, your branding will automatically appear on:

- ✅ Stripe Checkout pages (subscription purchases)
- ✅ Payment Links (if you create any)
- ✅ Customer Portal (for subscription management)
- ✅ Hosted Invoice Pages
- ✅ Invoice PDFs
- ✅ Email receipts sent by Stripe

**No code changes required!** Your existing checkout code in `app.py` will automatically use the new branding.

---

## Switching to Production

When you're ready to go live:

1. **Switch to Live Mode** in Stripe Dashboard (toggle in top right)
2. **Re-run the upload script** OR **manually upload logo again** in Live Mode
   - Test and Live modes have separate branding configurations
   - You need to configure branding for both modes

```bash
# Make sure your .env has STRIPE_SECRET_KEY for LIVE mode
python3 upload_logo_to_stripe.py
```

---

## Troubleshooting

### Script Error: "STRIPE_SECRET_KEY not found"

**Solution**: Verify your `.env` file contains:
```
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxx
```

### Script Error: "File upload failed"

**Possible causes**:
1. Logo file not found at specified path
2. File size exceeds 512KB (yours is only 12KB, so this shouldn't happen)
3. Invalid file format (yours is PNG, which is valid)

**Solution**: Try the manual Dashboard method instead

### Logo doesn't appear on checkout

**Possible causes**:
1. Branding configured in Test mode, but you're testing in Live mode (or vice versa)
2. Browser cache - try hard refresh (Ctrl+Shift+R) or incognito mode
3. Logo upload still processing (wait 1-2 minutes)

**Solution**:
- Verify you're in the correct mode (Test vs Live)
- Clear browser cache and retry
- Check Dashboard to confirm logo is visible in preview

### Business name doesn't show

**Solution**:
- Verify business name is set at: https://dashboard.stripe.com/settings/public
- Branding settings can take 1-2 minutes to propagate

---

## Additional Customization (Optional)

If you want to add more customization in the future, you can:

### 1. Add Custom Colors

Edit `upload_logo_to_stripe.py` and modify the branding section:

```python
settings={
    'branding': {
        'logo': logo_file_id,
        'primary_color': '#FF6B6B',     # Your brand's primary color
        'secondary_color': '#4ECDC4'    # Your brand's accent color
    }
}
```

### 2. Add Terms of Service Links

Edit `app.py` at line 172, modify the checkout session creation:

```python
checkout_session = stripe.checkout.Session.create(
    # ... existing parameters ...
    custom_text={
        'terms_of_service_acceptance': {
            'message': 'I agree to the [Terms of Service](https://minipass.me/terms)'
        }
    },
    consent_collection={
        'terms_of_service': 'required'
    }
)
```

### 3. Add Support Contact Info

Configure at: https://dashboard.stripe.com/settings/public
- Support email
- Support phone
- Support website

These will appear on the checkout page for customer confidence.

---

## File Locations

- **Upload Script**: `MinipassWebSite/upload_logo_to_stripe.py`
- **Logo File**: `/home/kdresdell/mp-logo-regular.png`
- **This Guide**: `MinipassWebSite/STRIPE_BRANDING_GUIDE.md`
- **Main App**: `MinipassWebSite/app.py` (lines 154-206: checkout session creation)

---

## Support

- **Stripe Branding Docs**: https://docs.stripe.com/get-started/account/branding
- **Stripe Dashboard**: https://dashboard.stripe.com/settings/branding
- **Test Mode Toggle**: Top right corner of Stripe Dashboard

---

**Ready to test?** Run the upload script or configure manually via Dashboard, then test your checkout flow!

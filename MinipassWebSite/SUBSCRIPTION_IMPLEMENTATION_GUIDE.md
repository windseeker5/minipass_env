# Stripe Recurring Subscription Implementation Guide

**Date:** 2025-11-13
**Project:** MinipassWebSite → Customer App Integration
**Goal:** Enable automatic recurring subscriptions with customer self-service cancellation

---

## Part 1: What Has Been Completed (MinipassWebSite)

### 1.1 Stripe Configuration ✅

Created 6 recurring subscription prices in Stripe:

| Plan | Frequency | Price ID | Amount |
|------|-----------|----------|--------|
| Basic | Monthly | `price_1ST84NGhJsN3FLG4y8PczQY2` | $20 CAD/month |
| Basic | Annual | `price_1ST84VGhJsN3FLG47Y6Utmid` | $120 CAD/year |
| Pro | Monthly | `price_1ST84XGhJsN3FLG4Vrfof1rP` | $50 CAD/month |
| Pro | Annual | `price_1ST84YGhJsN3FLG4RsKzYVwa` | $300 CAD/year |
| Ultimate | Monthly | `price_1ST84ZGhJsN3FLG4LzhrjkRS` | $120 CAD/month |
| Ultimate | Annual | `price_1ST84bGhJsN3FLG4fSdWgezx` | $720 CAD/year |

**File Modified:** `MinipassWebSite/.env` (lines 8-14)

---

### 1.2 Database Schema Updates ✅

**Migration:** `migrations/add_stripe_ids.py`

Added columns to `customers` table:
- `stripe_customer_id` TEXT - Stripe Customer ID (e.g., cus_xxx)
- `stripe_subscription_id` TEXT - Stripe Subscription ID (e.g., sub_xxx)

**Files Modified:**
- `utils/customer_helpers.py` - Updated `insert_customer()` function signature
- `utils/customer_helpers.py` - Added helper functions:
  - `update_customer_stripe_ids(subdomain, stripe_customer_id, stripe_subscription_id)`
  - `get_customer_by_stripe_subscription_id(stripe_subscription_id)`

---

### 1.3 Checkout Flow Changes ✅

**File:** `MinipassWebSite/app.py` (lines 171-198)

**Key Change:** Changed from one-time payment to recurring subscription

```python
# OLD: mode="payment"
# NEW: mode="subscription"

session_obj = stripe.checkout.Session.create(
    mode="subscription",  # ← CHANGED
    line_items=[{"price": stripe_price_id, "quantity": 1}],
    subscription_data={
        "metadata": {
            "app_name": app_name,
            "plan": plan,
            "billing_frequency": billing_frequency,
            "tier": tier
        }
    }
)
```

**Result:** Stripe now automatically:
- Charges customer monthly/annually
- Handles payment retries
- Sends renewal confirmations

---

### 1.4 Webhook Handlers ✅

**File:** `MinipassWebSite/app.py` (lines 414-522)

Added handlers for 3 new Stripe events:

#### 1. `invoice.payment_succeeded` (lines 414-457)
**Triggers:** Every successful renewal payment
**Action:** Updates `subscription_end_date` in database

```python
if billing_frequency == "monthly":
    new_end_date = datetime.now() + timedelta(days=30)
else:  # annual
    new_end_date = datetime.now() + timedelta(days=365)
```

#### 2. `invoice.payment_failed` (lines 459-490)
**Triggers:** When renewal payment fails
**Action:** Sets `subscription_status = 'past_due'` in database
**TODO:** Send email notification to customer

#### 3. `customer.subscription.deleted` (lines 492-520)
**Triggers:** When subscription is cancelled
**Action:** Sets `subscription_status = 'cancelled'` in database
**Note:** Container remains deployed until `subscription_end_date`

---

### 1.5 Subscription Info File ✅

**File:** `MinipassWebSite/app.py` (lines 399-423)

After deployment, writes `subscription.json` to customer app:

**Location:** `/home/kdresdell/minipass_customers/{app_name}/app/instance/subscription.json`

**Content:**
```json
{
  "stripe_customer_id": "cus_xxx",
  "stripe_subscription_id": "sub_xxx",
  "plan": "basic",
  "billing_frequency": "monthly",
  "subscription_start_date": "2025-11-13T16:33:03.123456",
  "subscription_end_date": "2025-12-13T16:33:03.123456",
  "stripe_price_id": "price_xxx",
  "tier": 1
}
```

---

## Part 2: What Needs to Be Done (Customer App)

### 2.1 Environment Variables Required

Your customer app needs Stripe API access to cancel subscriptions.

**File:** `/app/.env` or passed via Docker environment

```bash
STRIPE_SECRET_KEY=sk_test_51RVfdVGhJsN3FLG4yXK6EVBO2ZdazFLWjFpAFj5OYIJSqAJN2jj6ZBVszNUzPGvzYcm5WJAg0kmGNNDWRByl96vN00z6vPTibs
```

**Update Docker Deployment:**
In `utils/deploy_helpers.py`, add to docker-compose environment section:

```yaml
environment:
  - STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
```

---

### 2.2 Backend: Subscription Cancellation Endpoint

**File:** `/app/app.py` (add new route)

```python
@app.route('/settings/cancel-subscription', methods=['POST'])
def cancel_subscription():
    """Cancel subscription at period end"""
    if "admin" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    # Load subscription info
    subscription_file = os.path.join('instance', 'subscription.json')

    if not os.path.exists(subscription_file):
        return jsonify({"error": "Subscription info not found"}), 404

    with open(subscription_file, 'r') as f:
        subscription_info = json.load(f)

    subscription_id = subscription_info.get('stripe_subscription_id')

    if not subscription_id:
        return jsonify({"error": "Subscription ID not found"}), 400

    try:
        # Cancel at period end (customer keeps access until end date)
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        updated_sub = stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True
        )

        # Update local file
        subscription_info['cancel_at_period_end'] = True
        subscription_info['cancelled_at'] = datetime.now().isoformat()

        with open(subscription_file, 'w') as f:
            json.dump(subscription_info, f, indent=2)

        return jsonify({
            "success": True,
            "message": "Subscription cancelled. Access continues until end of billing period.",
            "end_date": subscription_info['subscription_end_date']
        })

    except stripe.error.StripeError as e:
        return jsonify({"error": str(e)}), 500
```

---

### 2.3 Frontend: Update Your Current Plan Page

**Your existing file:** `/app/templates/current_plan.html`

#### Step 1: Load subscription info in your route handler

```python
@app.route('/settings/current-plan')
def current_plan():
    if "admin" not in session:
        return redirect(url_for("login"))

    # YOUR EXISTING CODE for tier_info and usage_info...

    # ADD THIS: Load subscription details
    subscription_file = os.path.join('instance', 'subscription.json')
    subscription_info = None

    if os.path.exists(subscription_file):
        with open(subscription_file, 'r') as f:
            subscription_info = json.load(f)

    return render_template('current_plan.html',
                         tier_info=tier_info,
                         usage_info=usage_info,
                         upgrade_options=upgrade_options,
                         subscription_info=subscription_info)  # ← ADD THIS
```

#### Step 2: Add subscription details card to template

Add this **after** your existing "Your Subscription" card:

```html
<!-- Subscription Management Card -->
{% if subscription_info %}
<div class="card bg-white mb-3">
  <div class="card-header">
    <h2 class="card-title mb-0">Subscription Details</h2>
  </div>
  <div class="card-body">
    <div class="row">
      <div class="col-md-6 mb-3">
        <div class="text-muted small mb-1">BILLING FREQUENCY</div>
        <div class="h4">
          {{ subscription_info.billing_frequency|capitalize }}
          <span class="text-muted">
            ({% if subscription_info.billing_frequency == 'monthly' %}Renews monthly{% else %}Renews annually{% endif %})
          </span>
        </div>
      </div>

      <div class="col-md-6 mb-3">
        <div class="text-muted small mb-1">NEXT BILLING DATE</div>
        <div class="h4">{{ subscription_info.subscription_end_date[:10] }}</div>
      </div>
    </div>

    <div class="row">
      <div class="col-md-12">
        {% if subscription_info.cancel_at_period_end %}
          <!-- Cancellation pending -->
          <div class="alert alert-warning">
            <i class="ti ti-alert-circle me-2"></i>
            <strong>Cancellation Scheduled</strong><br>
            Your subscription will end on <strong>{{ subscription_info.subscription_end_date[:10] }}</strong>.
            You'll retain access until then.
          </div>
        {% else %}
          <!-- Active subscription - show cancel button -->
          <button class="btn btn-outline-danger"
                  onclick="cancelSubscription()"
                  id="cancelBtn">
            <i class="ti ti-x me-2"></i>Cancel Subscription
          </button>
        {% endif %}
      </div>
    </div>
  </div>
</div>
{% endif %}

<script>
function cancelSubscription() {
  if (!confirm('Are you sure you want to cancel your subscription? You will retain access until the end of your billing period.')) {
    return;
  }

  const btn = document.getElementById('cancelBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Cancelling...';

  fetch('/settings/cancel-subscription', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      alert('Subscription cancelled successfully. You will retain access until ' + data.end_date);
      window.location.reload();
    } else {
      alert('Error: ' + data.error);
      btn.disabled = false;
      btn.innerHTML = '<i class="ti ti-x me-2"></i>Cancel Subscription';
    }
  })
  .catch(error => {
    alert('Network error. Please try again.');
    btn.disabled = false;
    btn.innerHTML = '<i class="ti ti-x me-2"></i>Cancel Subscription';
  });
}
</script>
```

---

## Part 3: Testing Checklist

### 3.1 Test New Subscription Flow

1. **Sign up for a test subscription:**
   - Go to minipass.me
   - Click "M'abonner" for Basic Monthly plan
   - Use Stripe test card: `4242 4242 4242 4242`
   - Complete checkout

2. **Verify deployment:**
   - Check that customer app is deployed
   - Check that `/instance/subscription.json` exists in customer folder
   - Verify file contains stripe_subscription_id

3. **Test customer portal:**
   - Log into your deployed app
   - Navigate to Settings → Current Plan
   - Verify subscription details are displayed
   - Test "Cancel Subscription" button
   - Confirm cancellation in Stripe dashboard

### 3.2 Test Webhook Handlers

1. **Test renewal (simulate):**
   - In Stripe Dashboard → Billing → Subscriptions
   - Find test subscription
   - Click "..." → Send test invoice
   - Check that database `subscription_end_date` is updated

2. **Test cancellation webhook:**
   - Cancel subscription in Stripe Dashboard
   - Check that database `subscription_status` = 'cancelled'

---

## Part 4: Cleanup & Rollback

### If Something Goes Wrong

#### Rollback Database:
```bash
cd MinipassWebSite
mv customers_backup_20251113_163303.db customers.db
```

#### Rollback Stripe Prices:
The old one-time prices still exist in Stripe. To revert:
1. Update `.env` with old price IDs (backed up in Git)
2. Change `mode="subscription"` back to `mode="payment"` in app.py

#### Remove Test Customer:
```bash
cd MinipassWebSite
python manage_app.py
# Select customer to delete
```

---

## Part 5: Files Modified Summary

### MinipassWebSite (Marketing/Subscription Site)
```
✅ .env                                    - Updated Stripe price IDs
✅ app.py                                  - Checkout + webhook changes
✅ utils/customer_helpers.py               - Added Stripe ID functions
✅ migrations/add_stripe_ids.py            - Database migration (NEW)
```

### Customer App (To Be Modified by You)
```
⏳ app.py                                  - Add cancel endpoint
⏳ templates/current_plan.html             - Add subscription UI
⏳ .env or docker-compose.yml              - Add STRIPE_SECRET_KEY
```

---

## Part 6: Important Notes

### Security
- **Never expose Stripe secret key in frontend code**
- All Stripe API calls must happen server-side
- Cancellation endpoint requires admin session

### Billing Cycle
- Cancellation uses `cancel_at_period_end=True`
- Customer retains access until current period ends
- No prorated refunds (Stripe default behavior)
- Next renewal will not happen

### Database Sync
- `subscription_end_date` is updated by webhooks on renewal
- Customer app reads from `subscription.json` file
- MinipassWebSite database is the source of truth

### TODO Items
1. Send email notification when payment fails (`invoice.payment_failed`)
2. Add scheduled job to stop containers after `subscription_end_date`
3. Add "Update Payment Method" feature (Stripe Customer Portal)
4. Add subscription upgrade/downgrade flow

---

## Questions or Issues?

If you encounter issues during implementation:

1. **Check logs:**
   - MinipassWebSite: `./subscribed_app.log`
   - Customer app: Docker logs

2. **Verify Stripe webhook:**
   - Dashboard → Developers → Webhooks
   - Check that webhook URL is `https://minipass.me/webhook`
   - Verify events are being received

3. **Database queries:**
   ```python
   # Check customer record
   from utils.customer_helpers import get_customer_by_subdomain
   customer = get_customer_by_subdomain('testapp')
   print(customer)
   ```

---

**End of Implementation Guide**

# MiniPass Multi-Tier Subscription System - Implementation Plan

## Executive Summary
Upgrade the MiniPass deployment system to support 3 tiers × 2 billing frequencies (6 payment options) with proper tier differentiation. The customer app TIER enforcement is already implemented - we just need to connect the payment flow to deployment.

## Pricing Structure (Confirmed)

### Monthly Pricing (Full Price)
- **Basic**: $20/month
- **Pro**: $50/month
- **Ultimate**: $120/month

### Annual Pricing (50% Discount)
- **Basic**: $10/month (billed $120/year)
- **Pro**: $25/month (billed $300/year)
- **Ultimate**: $60/month (billed $720/year)

### Tier Mapping
- Basic → TIER=1 (1 activity limit)
- Pro → TIER=2 (15 activities limit)
- Ultimate → TIER=3 (100 activities limit)

## Current Issues Identified

### Critical Bugs
1. **SHOWSTOPPER**: Plan not passed to Stripe metadata - webhook cannot determine which tier customer paid for
2. **Frontend Bug**: Badge shows "ÉCONOMISEZ 25%" but should be "ÉCONOMISEZ 50%"
3. **No Tier Differentiation**: All deployments use same configuration regardless of plan
4. **No Subscription Tracking**: Billing frequency and subscription dates not stored in database

### What's Already Working ✅
- Frontend toggle switches between monthly/annual pricing correctly
- All 6 prices display correctly when toggling
- Customer app (`/app`) already has TIER=1/2/3 enforcement implemented
- Activity limits (1/15/100) already working in customer app
- Email integration (mail_integration.py) working correctly
- Deployment email notifications working

### Legacy Code to Archive
- `utils/mail_server_helpers.py` - Unused old mail integration approach

---

## Implementation Phases

### PHASE 1: Stripe Product & Price Setup

**Objective**: Create Stripe Products and Prices using Stripe MCP server

**Steps**:
1. Use Stripe MCP to create 3 Products:
   - "MiniPass Basic"
   - "MiniPass Pro"
   - "MiniPass Ultimate"

2. Create 6 Prices (using one-time payment mode for now):
   - Basic Monthly: $20 CAD
   - Basic Annual: $120 CAD
   - Pro Monthly: $50 CAD
   - Pro Annual: $300 CAD
   - Ultimate Monthly: $120 CAD
   - Ultimate Annual: $720 CAD

3. Store Price IDs in `.env` file:
```env
# Stripe Configuration
STRIPE_SECRET_KEY=sk_...
STRIPE_PUBLISHABLE_KEY=pk_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Stripe Price IDs (add these)
STRIPE_PRICE_BASIC_MONTHLY=price_xxx
STRIPE_PRICE_BASIC_ANNUAL=price_xxx
STRIPE_PRICE_PRO_MONTHLY=price_xxx
STRIPE_PRICE_PRO_ANNUAL=price_xxx
STRIPE_PRICE_ULTIMATE_MONTHLY=price_xxx
STRIPE_PRICE_ULTIMATE_ANNUAL=price_xxx
```

**MCP Commands to Execute**:
```python
# Create Products
mcp__stripe__create_product(name="MiniPass Basic", description="1 Activity - Perfect for individual organizers")
mcp__stripe__create_product(name="MiniPass Pro", description="15 Activities - Ideal for growing organizations")
mcp__stripe__create_product(name="MiniPass Ultimate", description="100 Activities - Enterprise solution")

# Create Prices (will be done in implementation)
```

**Deliverable**: 6 Stripe Price IDs added to `.env` file

---

### PHASE 2: Database Schema Migration

**Objective**: Add subscription tracking fields to customers table

**File**: Create `migrations/add_subscription_tracking.py`

**New Columns to Add**:
```sql
ALTER TABLE customers ADD COLUMN billing_frequency TEXT DEFAULT 'monthly';
ALTER TABLE customers ADD COLUMN subscription_start_date TEXT;
ALTER TABLE customers ADD COLUMN subscription_end_date TEXT;
ALTER TABLE customers ADD COLUMN stripe_price_id TEXT;
ALTER TABLE customers ADD COLUMN stripe_checkout_session_id TEXT;
ALTER TABLE customers ADD COLUMN payment_amount INTEGER;  -- in cents
ALTER TABLE customers ADD COLUMN currency TEXT DEFAULT 'cad';
ALTER TABLE customers ADD COLUMN subscription_status TEXT DEFAULT 'active';
```

**Migration Script Logic**:
1. Backup existing `customers.db`
2. Add new columns with defaults
3. For existing customers, set:
   - `billing_frequency = 'monthly'`
   - `subscription_start_date = created_at`
   - `subscription_end_date = created_at + 30 days`
   - `subscription_status = 'active'`
4. Verify migration succeeded

**File**: Update `utils/customer_helpers.py`

**Changes Required**:
1. Update `init_db()` CREATE TABLE statement to include new columns
2. Update `add_customer()` function signature:
```python
def add_customer(email, subdomain, app_name, plan, password, port,
                email_address, email_password, forwarding_email, organization_name,
                billing_frequency='monthly', subscription_start_date=None, subscription_end_date=None,
                stripe_price_id=None, stripe_checkout_session_id=None,
                payment_amount=None, currency='cad', subscription_status='active'):
```

3. Update INSERT statement to include all new fields

**Deliverable**: Database migration completed, customer_helpers.py updated

---

### PHASE 3: Frontend Minor Fix

**Objective**: Fix discount badge text

**File**: `templates/index.html`

**Change**: Line ~430 (in pricing section)
```html
<!-- BEFORE -->
<span class="badge bg-success">ÉCONOMISEZ 25%</span>

<!-- AFTER -->
<span class="badge bg-success">ÉCONOMISEZ 50%</span>
```

**Verification**:
- Monthly/Annual toggle still works
- All 6 prices display correctly
- Badge shows correct 50% discount

**Deliverable**: Badge text corrected

---

### PHASE 4: Backend Payment Flow (CRITICAL FIX)

**Objective**: Fix checkout session creation to pass proper metadata and use Stripe Price IDs

**File**: `app.py`

#### A. Add Configuration Constants (top of file, after imports)

```python
# Stripe Price ID Configuration
STRIPE_PRICES = {
    'basic_monthly': os.getenv('STRIPE_PRICE_BASIC_MONTHLY'),
    'basic_annual': os.getenv('STRIPE_PRICE_BASIC_ANNUAL'),
    'pro_monthly': os.getenv('STRIPE_PRICE_PRO_MONTHLY'),
    'pro_annual': os.getenv('STRIPE_PRICE_PRO_ANNUAL'),
    'ultimate_monthly': os.getenv('STRIPE_PRICE_ULTIMATE_MONTHLY'),
    'ultimate_annual': os.getenv('STRIPE_PRICE_ULTIMATE_ANNUAL'),
}

# Plan to Tier mapping (for customer container TIER env var)
PLAN_TO_TIER = {
    'basic': 1,
    'pro': 2,
    'ultimate': 3
}

# Validate all Price IDs are configured
missing_prices = [k for k, v in STRIPE_PRICES.items() if not v]
if missing_prices:
    logging.error(f"Missing Stripe Price IDs in .env: {missing_prices}")
```

#### B. Update `/start-checkout` Route (around line 107-157)

**Current Issues**:
- Plan selected but not added to metadata
- Using dynamic price calculation instead of Price IDs
- Not capturing billing_frequency

**Required Changes**:

```python
@app.route('/start-checkout', methods=['POST'])
def start_checkout():
    # Existing form data extraction
    app_name = request.form.get('app_name', '').strip().lower()
    organization_name = request.form.get('organization_name', '').strip()
    admin_email = request.form.get('email', '').strip()
    plan = request.form.get('plan', 'basic').lower()

    # NEW: Get billing frequency from form
    billing_frequency = request.form.get('billing_frequency', 'monthly').lower()

    # Validate plan
    if plan not in PLAN_TO_TIER:
        return jsonify({'error': f'Invalid plan: {plan}'}), 400

    # Existing subdomain validation...
    if is_subdomain_taken(app_name):
        return jsonify({'error': 'Subdomain already taken'}), 400

    # Generate password (existing code)...
    admin_password = generate_secure_password()

    # NEW: Build price key and get Stripe Price ID
    price_key = f"{plan}_{billing_frequency}"
    stripe_price_id = STRIPE_PRICES.get(price_key)

    if not stripe_price_id:
        logging.error(f"Stripe Price ID not found for: {price_key}")
        return jsonify({'error': 'Price configuration error'}), 500

    # Store in session (existing)
    session['checkout_data'] = {
        'app_name': app_name,
        'organization_name': organization_name,
        'admin_email': admin_email,
        'admin_password': admin_password,
        'plan': plan,
        'billing_frequency': billing_frequency,  # NEW
        'tier': PLAN_TO_TIER[plan]  # NEW
    }

    try:
        # Create Stripe Checkout Session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': stripe_price_id,  # NEW: Use Price ID instead of dynamic
                'quantity': 1,
            }],
            mode='payment',  # one-time payment
            success_url=url_for('success', _external=True),
            cancel_url=url_for('index', _external=True),
            metadata={
                'app_name': app_name,
                'organization_name': organization_name,
                'admin_email': admin_email,
                'forwarding_email': admin_email,
                'admin_password': admin_password,
                'plan': plan,  # CRITICAL FIX: Add plan!
                'billing_frequency': billing_frequency,  # CRITICAL FIX: Add frequency!
                'tier': str(PLAN_TO_TIER[plan])  # CRITICAL FIX: Add tier!
            }
        )

        return jsonify({'url': checkout_session.url})

    except Exception as e:
        logging.error(f"Stripe checkout error: {e}")
        return jsonify({'error': 'Payment setup failed'}), 500
```

**JavaScript Changes Required** (if not already passing billing_frequency):
```javascript
// In signup modal form submission
const formData = new FormData();
formData.append('app_name', appName);
formData.append('organization_name', orgName);
formData.append('email', email);
formData.append('plan', currentPlan);
formData.append('billing_frequency', currentBillingFrequency);  // NEW: Add this
```

**Deliverable**: Checkout creates sessions with complete metadata and correct Price IDs

---

### PHASE 5: Webhook Handler (Deployment Integration)

**Objective**: Extract tier information from webhook and pass to deployment

**File**: `app.py` (webhook route around line 170-313)

**Current Issues**:
- Plan defaults to "basic" because metadata missing
- No subscription date tracking
- No billing frequency storage
- Not passing tier to deployment

**Required Changes**:

```python
@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    if event['type'] == 'checkout.session.completed':
        session_data = event['data']['object']

        # Check idempotency (existing)...
        if is_event_processed(event['id']):
            return jsonify({'status': 'already processed'}), 200

        # Extract metadata
        metadata = session_data.get('metadata', {})
        app_name = metadata.get('app_name')
        organization_name = metadata.get('organization_name')
        admin_email = metadata.get('admin_email')
        forwarding_email = metadata.get('forwarding_email')
        admin_password = metadata.get('admin_password')

        # NEW: Extract plan, billing_frequency, and tier
        plan = metadata.get('plan', 'basic').lower()
        billing_frequency = metadata.get('billing_frequency', 'monthly').lower()
        tier = metadata.get('tier', '1')

        # NEW: Calculate subscription dates
        from datetime import datetime, timedelta
        subscription_start_date = datetime.now().isoformat()

        if billing_frequency == 'monthly':
            end_date = datetime.now() + timedelta(days=30)
        else:  # annual
            end_date = datetime.now() + timedelta(days=365)

        subscription_end_date = end_date.isoformat()

        # NEW: Extract payment information
        payment_amount = session_data.get('amount_total')  # in cents
        currency = session_data.get('currency', 'cad')

        # Get stripe_price_id from line_items
        stripe_price_id = None
        line_items = session_data.get('line_items', {}).get('data', [])
        if line_items:
            stripe_price_id = line_items[0].get('price', {}).get('id')

        stripe_checkout_session_id = session_data.get('id')

        # Validation...
        if not all([app_name, admin_email, admin_password]):
            logger.error("Missing required metadata in webhook")
            return jsonify({'error': 'Missing metadata'}), 400

        # Initialize database (existing)...
        init_db()

        # Check subdomain (existing)...
        if is_subdomain_taken(app_name):
            logger.error(f"Subdomain collision: {app_name}")
            return jsonify({'error': 'Subdomain taken'}), 409

        # Get port (existing)...
        port = get_next_available_port()

        # Generate email address (existing)...
        email_address = f"{app_name}_app@minipass.me"
        email_password = admin_password

        # Deploy container - UPDATED with tier parameter
        logger.info(f"Deploying container for {app_name} (plan={plan}, tier={tier}, frequency={billing_frequency})")

        deploy_success = deploy_customer_container(
            app_name=app_name,
            admin_email=admin_email,
            admin_password=admin_password,
            plan=plan,
            port=port,
            organization_name=organization_name,
            tier=int(tier),  # NEW: Pass tier!
            billing_frequency=billing_frequency  # NEW: Pass frequency (optional)
        )

        if not deploy_success:
            logger.error(f"Deployment failed for {app_name}")
            send_support_error_email(admin_email, app_name, "Container deployment failed")
            return jsonify({'error': 'Deployment failed'}), 500

        # Create customer record - UPDATED with new fields
        add_customer(
            email=admin_email,
            subdomain=app_name,
            app_name=app_name,
            plan=plan,
            password=admin_password,
            port=port,
            email_address=email_address,
            email_password=email_password,
            forwarding_email=forwarding_email,
            organization_name=organization_name,
            billing_frequency=billing_frequency,  # NEW
            subscription_start_date=subscription_start_date,  # NEW
            subscription_end_date=subscription_end_date,  # NEW
            stripe_price_id=stripe_price_id,  # NEW
            stripe_checkout_session_id=stripe_checkout_session_id,  # NEW
            payment_amount=payment_amount,  # NEW
            currency=currency,  # NEW
            subscription_status='active'  # NEW
        )

        # Setup email (existing)...
        email_success, email_address_created, email_error = setup_customer_email_complete(
            app_name, email_password, forwarding_email
        )

        # Send deployment notification (existing)...
        app_url = f"https://{app_name}.minipass.me"
        email_info = {
            'email_address': email_address_created,
            'email_password': email_password,
            'forwarding_setup': email_success
        } if email_success else None

        send_user_deployment_email(admin_email, app_url, admin_password, email_info)

        # Mark as deployed (existing)...
        mark_customer_deployed(app_name)

        # Mark event processed (existing)...
        mark_event_processed(event['id'], event['type'])

        logger.info(f"✅ Deployment complete for {app_name}")
        return jsonify({'status': 'success'}), 200

    return jsonify({'status': 'ignored'}), 200
```

**Deliverable**: Webhook properly extracts and stores all subscription data, passes tier to deployment

---

### PHASE 6: Deployment Configuration

**Objective**: Pass TIER environment variable to customer containers

**File**: `utils/deploy_helpers.py`

#### A. Update Function Signature (line 163)

```python
def deploy_customer_container(app_name, admin_email, admin_password, plan, port,
                             organization_name=None, tier=1, billing_frequency='monthly'):
    """
    Deploys a customer container with tier-specific configuration.

    Args:
        app_name: Subdomain/app name
        admin_email: Admin user email
        admin_password: Admin user password
        plan: Plan name (basic/pro/ultimate)
        port: Port number for container
        organization_name: Organization name (optional)
        tier: Tier number (1=Basic, 2=Pro, 3=Ultimate)
        billing_frequency: 'monthly' or 'annual'
    """
```

#### B. Update Docker Compose Environment Section (line 248-252)

```python
# Current compose_content generation around line 236-268
compose_content = textwrap.dedent(f"""\
    version: '3.8'

    services:
      flask-app:
        container_name: minipass_{app_name}
        build:
          context: ./app

        volumes:
          - ./app:/app
          - ./app/instance:/app/instance

        environment:
          - FLASK_ENV=dev
          - ADMIN_EMAIL={admin_email}
          - ADMIN_PASSWORD={admin_password}
          - ORG_NAME={organization_name or app_name}

          # NEW: Tier Configuration (CRITICAL!)
          - TIER={tier}
          - BILLING_FREQUENCY={billing_frequency}

          # NGINX reverse proxy support
          - VIRTUAL_HOST={app_name}.minipass.me
          - VIRTUAL_PORT=5000
          - LETSENCRYPT_HOST={app_name}.minipass.me
          - LETSENCRYPT_EMAIL=kdresdell@gmail.com

        restart: unless-stopped
        networks:
          - proxy

    networks:
      proxy:
        external:
          name: minipass_env_proxy
    """)
```

#### C. Add Logging for Tier Configuration

```python
logger.info(f"📊 Deploying with configuration:")
logger.info(f"   Plan: {plan}")
logger.info(f"   Tier: {tier}")
logger.info(f"   Billing: {billing_frequency}")
logger.info(f"   Activity Limit: {1 if tier==1 else 15 if tier==2 else 100}")
```

**Deliverable**: Customer containers receive TIER env var and enforce limits

---

### PHASE 7: Testing & Validation

**Objective**: Comprehensive testing of all 6 payment flows

#### Test Cases

**Test 1: Basic Monthly ($20 CAD)**
1. Select "1 Activité" plan
2. Keep toggle on "Mensuel"
3. Fill form and complete checkout
4. Verify:
   - ✅ Stripe charges $20
   - ✅ Webhook receives plan=basic, billing_frequency=monthly, tier=1
   - ✅ Database: payment_amount=2000, billing_frequency=monthly
   - ✅ Container deployed with TIER=1
   - ✅ Customer app allows max 1 activity
   - ✅ Email sent successfully

**Test 2: Basic Annual ($120 CAD)**
1. Select "1 Activité" plan
2. Switch toggle to "Annuel"
3. Fill form and complete checkout
4. Verify:
   - ✅ Stripe charges $120
   - ✅ Webhook receives plan=basic, billing_frequency=annual, tier=1
   - ✅ Database: payment_amount=12000, billing_frequency=annual
   - ✅ subscription_end_date = start + 365 days
   - ✅ Container deployed with TIER=1
   - ✅ Customer app allows max 1 activity

**Test 3: Pro Monthly ($50 CAD)**
1. Select "15 Activités" plan
2. Keep toggle on "Mensuel"
3. Fill form and complete checkout
4. Verify:
   - ✅ Stripe charges $50
   - ✅ Webhook receives plan=pro, billing_frequency=monthly, tier=2
   - ✅ Database: payment_amount=5000, billing_frequency=monthly
   - ✅ Container deployed with TIER=2
   - ✅ Customer app allows max 15 activities

**Test 4: Pro Annual ($300 CAD)**
1. Select "15 Activités" plan
2. Switch toggle to "Annuel"
3. Fill form and complete checkout
4. Verify:
   - ✅ Stripe charges $300
   - ✅ Webhook receives plan=pro, billing_frequency=annual, tier=2
   - ✅ Database: payment_amount=30000, billing_frequency=annual
   - ✅ Container deployed with TIER=2
   - ✅ Customer app allows max 15 activities

**Test 5: Ultimate Monthly ($120 CAD)**
1. Select "100 Activités" plan
2. Keep toggle on "Mensuel"
3. Fill form and complete checkout
4. Verify:
   - ✅ Stripe charges $120
   - ✅ Webhook receives plan=ultimate, billing_frequency=monthly, tier=3
   - ✅ Database: payment_amount=12000, billing_frequency=monthly
   - ✅ Container deployed with TIER=3
   - ✅ Customer app allows max 100 activities

**Test 6: Ultimate Annual ($720 CAD)**
1. Select "100 Activités" plan
2. Switch toggle to "Annuel"
3. Fill form and complete checkout
4. Verify:
   - ✅ Stripe charges $720
   - ✅ Webhook receives plan=ultimate, billing_frequency=annual, tier=3
   - ✅ Database: payment_amount=72000, billing_frequency=annual
   - ✅ Container deployed with TIER=3
   - ✅ Customer app allows max 100 activities

#### Edge Case Testing

**Test 7: Subdomain Collision**
- Try to deploy with existing subdomain
- Verify: Checkout fails with error message

**Test 8: Email Setup Failure**
- Simulate mail server down
- Verify: App still deploys, logs warning, notifies support

**Test 9: Deployment Failure**
- Simulate Docker error
- Verify: Payment succeeded but deployment failed, support notified

**Test 10: Webhook Idempotency**
- Send same webhook event twice
- Verify: Only processed once, second request returns "already processed"

**Test 11: Invalid Plan in Metadata**
- Manually create checkout with invalid plan
- Verify: Defaults to basic plan, logs warning

**Test 12: Missing Price ID**
- Remove one Price ID from .env
- Verify: Checkout fails with clear error message

#### Migration Testing

**Test 13: Existing Customers**
- Run migration on database with existing customers
- Verify: Existing customers get default values, still functional

#### Integration Testing

**Test 14: Full User Journey**
1. User visits minipass.me
2. Browses pricing, toggles monthly/annual
3. Clicks "S'inscrire"
4. Fills form with unique subdomain
5. Completes payment
6. Receives email with credentials
7. Logs into {subdomain}.minipass.me
8. Creates activities up to tier limit
9. Hits limit and sees error message

#### Performance Testing

**Test 15: Concurrent Deployments**
- Trigger 3 deployments simultaneously
- Verify: All deploy successfully, no port conflicts

#### Logging Verification

**Test 16: Log Monitoring**
- Review `subscribed_app.log` during test deployments
- Verify: All operations logged with proper context
- Check for any error/warning messages

**Deliverable**: All 6 payment flows tested and validated, edge cases handled

---

## Critical Files Modified Summary

| File | Changes | Lines | Priority |
|------|---------|-------|----------|
| `.env` | Add 6 Stripe Price IDs | +6 | CRITICAL |
| `migrations/add_subscription_tracking.py` | NEW - Database migration script | ~100 | HIGH |
| `utils/customer_helpers.py` | Update add_customer(), init_db() | ~50 | HIGH |
| `templates/index.html` | Fix 25%→50% discount badge | 1 | LOW |
| `app.py` | Fix /start-checkout route | ~40 | CRITICAL |
| `app.py` | Update webhook handler | ~60 | CRITICAL |
| `utils/deploy_helpers.py` | Add TIER env var to docker-compose | ~10 | CRITICAL |

## Files NOT Modified (Already Working)
- ✅ `utils/email_helpers.py` - Email notifications working
- ✅ `utils/mail_integration.py` - Mail server integration working
- ✅ Customer app `/app` - TIER enforcement already implemented
- ✅ `templates/base.html` - No changes needed
- ✅ `static/*` - No frontend JS changes needed (toggle already works)

## Files to Archive
- 🗑️ `utils/mail_server_helpers.py` - Legacy code, not used

---

## Risk Mitigation Strategy

### Before Implementation
1. **Backup Strategy**
   - Backup `customers.db` database
   - Backup `.env` file
   - Create git branch for implementation
   - Document rollback procedure

2. **Testing Environment**
   - Use Stripe test mode for all testing
   - Test on development server first
   - Don't deploy to production until fully validated

3. **Monitoring**
   - Monitor `subscribed_app.log` during testing
   - Watch for webhook delivery in Stripe Dashboard
   - Check container deployment status

### During Implementation
1. **Incremental Deployment**
   - Complete one phase at a time
   - Test after each phase before proceeding
   - Don't skip testing steps

2. **Validation Checks**
   - Verify Stripe Price IDs work before proceeding
   - Test database migration on copy of production DB
   - Validate webhook receives correct data

3. **Error Handling**
   - Add validation for missing Price IDs
   - Handle case where tier is missing from metadata
   - Graceful degradation for email setup failures

### Rollback Plan
If critical issues found:
1. Revert code changes via git
2. Restore `customers.db` from backup
3. Restore `.env` from backup
4. Restart Flask application
5. Verify existing customers still work

---

## Estimated Timeline

### Phase 1: Stripe Setup
- Create Products: 15 minutes
- Create Prices: 15 minutes
- Update .env: 5 minutes
- **Total: 35 minutes**

### Phase 2: Database Migration
- Write migration script: 30 minutes
- Test on dev database: 15 minutes
- Update customer_helpers.py: 20 minutes
- **Total: 65 minutes**

### Phase 3: Frontend Fix
- Update badge text: 2 minutes
- Test toggle: 3 minutes
- **Total: 5 minutes**

### Phase 4: Backend Payment Flow
- Add config constants: 10 minutes
- Update /start-checkout: 30 minutes
- Test checkout creation: 15 minutes
- **Total: 55 minutes**

### Phase 5: Webhook Handler
- Update webhook extraction: 30 minutes
- Add date calculations: 10 minutes
- Update deployment call: 10 minutes
- Test webhook processing: 20 minutes
- **Total: 70 minutes**

### Phase 6: Deployment Config
- Update function signature: 5 minutes
- Add TIER env var: 10 minutes
- Test container deployment: 15 minutes
- **Total: 30 minutes**

### Phase 7: Testing
- Test all 6 flows: 60 minutes
- Edge case testing: 30 minutes
- Integration testing: 30 minutes
- **Total: 120 minutes**

### Documentation & Cleanup
- Update README: 15 minutes
- Document Stripe setup: 20 minutes
- Create runbook: 20 minutes
- **Total: 55 minutes**

**GRAND TOTAL: ~6 hours of focused development work**

---

## Success Criteria Checklist

### Stripe Configuration
- [ ] 3 Products created in Stripe Dashboard
- [ ] 6 Prices created with correct amounts
- [ ] All Price IDs stored in .env
- [ ] Price IDs validated and accessible

### Database
- [ ] Migration script created and tested
- [ ] All new columns added to customers table
- [ ] Existing customers migrated successfully
- [ ] customer_helpers.py updated and tested

### Frontend
- [ ] Badge shows "ÉCONOMISEZ 50%"
- [ ] Toggle switches between monthly/annual
- [ ] All 6 prices display correctly
- [ ] Form submits billing_frequency

### Backend
- [ ] /start-checkout uses Stripe Price IDs
- [ ] Plan and billing_frequency in Stripe metadata
- [ ] Tier mapped correctly (basic=1, pro=2, ultimate=3)
- [ ] Error handling for missing Price IDs

### Webhook
- [ ] Extracts plan from metadata
- [ ] Extracts billing_frequency from metadata
- [ ] Calculates subscription dates correctly
- [ ] Stores all new fields in database
- [ ] Passes tier to deployment function

### Deployment
- [ ] TIER env var passed to containers
- [ ] docker-compose.yml generated correctly
- [ ] Containers deploy successfully
- [ ] Activity limits enforced in customer app

### Testing
- [ ] All 6 payment flows tested end-to-end
- [ ] Edge cases handled gracefully
- [ ] No duplicate deployments (idempotency works)
- [ ] Email notifications working
- [ ] Logs show complete operation details

### Documentation
- [ ] Implementation plan documented (this file)
- [ ] Stripe setup guide created
- [ ] Deployment runbook updated
- [ ] Rollback procedure documented

---

## Post-Implementation Improvements (Future)

### Phase 8: Admin Dashboard (Optional)
- Create `/admin` route to view all customers
- Show subscription status, tier, expiry dates
- Add ability to manually extend subscriptions
- View deployment logs per customer

### Phase 9: Subscription Lifecycle (Recommended for Production)
- Switch from one-time payments to recurring subscriptions
- Add webhook handlers for:
  - `customer.subscription.updated` (plan changes)
  - `customer.subscription.deleted` (cancellations)
  - `invoice.payment_succeeded` (renewals)
  - `invoice.payment_failed` (dunning)
- Automatic subscription renewal tracking
- Email notifications for expiring subscriptions

### Phase 10: Feature Enhancement
- Add "Experience Surveys" feature for Pro tier
- Add "AI Co-pilot" feature for Ultimate tier
- Tier-specific UI customization
- Usage analytics per customer

### Phase 11: Monitoring & Alerts
- Set up monitoring for failed deployments
- Alert on webhook processing errors
- Track conversion rates by tier
- Monitor churn and renewals

---

## Contact & Support

**Developer**: Claude Code Assistant
**Date Created**: 2025-01-10
**Version**: 1.0
**Status**: Ready for Implementation

For questions or issues during implementation, refer to:
- Stripe API Documentation: https://stripe.com/docs/api
- Flask Documentation: https://flask.palletsprojects.com/
- Docker Compose Reference: https://docs.docker.com/compose/

---

## Appendix

### A. Stripe Price ID Reference
After Phase 1 completion, fill in actual Price IDs:

| Plan | Frequency | Amount | Price ID |
|------|-----------|--------|----------|
| Basic | Monthly | $20 | `price_____________` |
| Basic | Annual | $120 | `price_____________` |
| Pro | Monthly | $50 | `price_____________` |
| Pro | Annual | $300 | `price_____________` |
| Ultimate | Monthly | $120 | `price_____________` |
| Ultimate | Annual | $720 | `price_____________` |

### B. Database Schema Reference

**Complete customers table schema after migration:**
```sql
CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    subdomain TEXT UNIQUE NOT NULL,
    app_name TEXT NOT NULL,
    plan TEXT NOT NULL,
    admin_password TEXT NOT NULL,
    port INTEGER NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    deployed INTEGER DEFAULT 0,
    email_address TEXT,
    email_password TEXT,
    forwarding_email TEXT,
    email_created TEXT,
    email_status TEXT DEFAULT 'pending',
    organization_name TEXT,
    -- NEW FIELDS --
    billing_frequency TEXT DEFAULT 'monthly',
    subscription_start_date TEXT,
    subscription_end_date TEXT,
    stripe_price_id TEXT,
    stripe_checkout_session_id TEXT,
    payment_amount INTEGER,
    currency TEXT DEFAULT 'cad',
    subscription_status TEXT DEFAULT 'active'
);
```

### C. Environment Variables Reference

**Required .env variables:**
```env
# Flask
SECRET_KEY=...
FLASK_ENV=production

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Stripe Price IDs
STRIPE_PRICE_BASIC_MONTHLY=price_...
STRIPE_PRICE_BASIC_ANNUAL=price_...
STRIPE_PRICE_PRO_MONTHLY=price_...
STRIPE_PRICE_PRO_ANNUAL=price_...
STRIPE_PRICE_ULTIMATE_MONTHLY=price_...
STRIPE_PRICE_ULTIMATE_ANNUAL=price_...

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=...
MAIL_PASSWORD=...
MAIL_DEFAULT_SENDER=info@minipass.me
```

### D. Tier Configuration Reference

| Tier | Plan | Activities | Price/Month | Price/Year |
|------|------|------------|-------------|------------|
| 1 | Basic | 1 | $20 | $120 |
| 2 | Pro | 15 | $50 | $300 |
| 3 | Ultimate | 100 | $120 | $720 |

---

**END OF IMPLEMENTATION PLAN**

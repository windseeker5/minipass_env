# Implementation Plan: Move Stripe Subscription Data from .env to Database Settings

**Document Version:** 1.0
**Created:** 2025-11-24
**Author:** Claude Code
**Status:** Ready for Implementation

---

## Executive Summary

This plan refactors the Minipass deployment system to store all customer-specific Stripe subscription data in the database `Setting` table instead of `.env` files. This enables easy tier upgrades without container restarts and provides clean separation between infrastructure configuration and customer data.

**Key Changes:**
1. New deployment function writes Stripe data to database
2. Customer app reads from database instead of environment variables
3. Beta testers get empty settings with special UI message
4. `.env` files contain only shared API keys

**Timeline:** 6-8 hours for complete implementation and testing

---

## Part 1: Deployment Script Changes (MinipassWebSite)

### 1.1 New Function: `set_stripe_subscription_settings_to_database()`

**File:** `MinipassWebSite/utils/deploy_helpers.py`
**Location:** After line 276 (after `set_email_settings_to_database()`)

**Function signature:**
```python
def set_stripe_subscription_settings_to_database(
    db_path,
    stripe_customer_id,
    stripe_subscription_id,
    payment_amount,
    subscription_renewal_date,
    tier,
    billing_frequency
):
    """
    Sets Stripe subscription configuration in the Setting table.
    Mirrors the pattern from set_email_settings_to_database().

    Args:
        db_path (str): Path to the app's database
        stripe_customer_id (str): Stripe customer ID (e.g., 'cus_xxx')
        stripe_subscription_id (str): Stripe subscription ID (e.g., 'sub_xxx')
        payment_amount (str): Payment amount in cents (e.g., '7200')
        subscription_renewal_date (str): ISO datetime string
        tier (int): Tier number (1, 2, or 3)
        billing_frequency (str): 'monthly' or 'annual'
    """
```

**Settings to write:**
- `STRIPE_CUSTOMER_ID`
- `STRIPE_SUBSCRIPTION_ID`
- `PAYMENT_AMOUNT`
- `SUBSCRIPTION_RENEWAL_DATE`
- `MINIPASS_TIER`
- `BILLING_FREQUENCY`

**Implementation pattern:** (Mirror lines 181-276)
1. Log operation start with context parameters
2. Connect to database
3. Verify Setting table exists
4. For each setting: Check if exists, UPDATE or INSERT
5. Commit and close
6. Log operation end with success/failure

### 1.2 Update `.env` Generation

**File:** `MinipassWebSite/utils/deploy_helpers.py`
**Lines:** 519-555

**Remove these lines:**
```python
STRIPE_CUSTOMER_ID={stripe_data.get('customer_id', '')}
STRIPE_SUBSCRIPTION_ID={stripe_data.get('subscription_id', '')}
PAYMENT_AMOUNT={stripe_data.get('payment_amount', '')}
SUBSCRIPTION_RENEWAL_DATE={stripe_data.get('renewal_date', '')}
MINIPASS_TIER={tier}
BILLING_FREQUENCY={billing_frequency}
```

**Keep these:**
```python
FLASK_SECRET_KEY={secret_key}
STRIPE_SECRET_KEY={parent_env_vars.get('STRIPE_SECRET_KEY', '')}
GOOGLE_MAPS_API_KEY={parent_env_vars.get('GOOGLE_MAPS_API_KEY', '')}
GOOGLE_AI_API_KEY={parent_env_vars.get('GOOGLE_AI_API_KEY', '')}
GROQ_API_KEY={parent_env_vars.get('GROQ_API_KEY', '')}
UNSPLASH_ACCESS_KEY={parent_env_vars.get('UNSPLASH_ACCESS_KEY', '')}
# Chatbot configuration
```

### 1.3 Call New Function During Deployment

**File:** `MinipassWebSite/utils/deploy_helpers.py`
**Location:** After line 657 (after `set_email_settings_to_database()` call)

**Add:**
```python
# Step 6d: Configure Stripe subscription settings in Setting table
logger.info(f"[{app_name}] 💳 Step 2g: Configuring Stripe subscription settings")
set_stripe_subscription_settings_to_database(
    db_path,
    stripe_data.get('customer_id', ''),
    stripe_data.get('subscription_id', ''),
    stripe_data.get('payment_amount', ''),
    stripe_data.get('renewal_date', ''),
    tier,
    billing_frequency
)
logger.info(f"[{app_name}] ✅ Stripe settings saved to Setting table")
```

### 1.4 Simplify docker-compose.yml Generation

**File:** `MinipassWebSite/utils/deploy_helpers.py`
**Lines:** 684-759 (docker-compose generation)

**Remove from environment section:**
```yaml
- ADMIN_EMAIL={admin_email}
- ADMIN_PASSWORD={admin_password}
- ORG_NAME={organization_name or app_name}
- TIER={tier}
- BILLING_FREQUENCY={billing_frequency}
```

**Keep only:**
```yaml
# Production mode:
- VIRTUAL_HOST={app_name}.minipass.me
- VIRTUAL_PORT=8889
- LETSENCRYPT_HOST={app_name}.minipass.me
- LETSENCRYPT_EMAIL=kdresdell@gmail.com

# Local mode:
- (just port mapping, no environment variables)
```

---

## Part 2: Customer App Changes (app/)

### 2.1 Update `get_subscription_tier()`

**File:** `app/app.py`
**Lines:** 220-224

**Current:**
```python
def get_subscription_tier():
    """Get current subscription tier from environment variable.
    Returns: 1 (Starter), 2 (Professional), or 3 (Enterprise)
    """
    return int(os.getenv('MINIPASS_TIER', '1'))
```

**Change to:**
```python
def get_subscription_tier():
    """Get current subscription tier from database Setting table.
    Fallback to environment variable for backwards compatibility.
    Returns: 1 (Starter), 2 (Professional), or 3 (Enterprise)
    """
    tier = get_setting('MINIPASS_TIER', '1')
    return int(tier) if tier else 1
```

### 2.2 Update `get_subscription_metadata()`

**File:** `app/app.py`
**Lines:** 320-361

**Replace all `os.getenv()` calls:**
```python
# Line 333: Renewal date
renewal_date_str = get_setting('SUBSCRIPTION_RENEWAL_DATE')

# Line 345: Payment amount
amount_str = get_setting('PAYMENT_AMOUNT')

# Line 355: Subscription ID
subscription_id = get_setting('STRIPE_SUBSCRIPTION_ID')

# Line 356: Customer ID
customer_id = get_setting('STRIPE_CUSTOMER_ID')

# Line 357: Billing frequency
billing_frequency = get_setting('BILLING_FREQUENCY', 'monthly')
```

### 2.3 Add Beta Tester Detection

**File:** `app/app.py`
**Function:** `get_subscription_metadata()`
**Location:** Around line 360 (at the beginning of the function)

**Add this check:**
```python
# Check if this is a beta tester (no Stripe subscription)
stripe_sub_id = get_setting('STRIPE_SUBSCRIPTION_ID', '')
tier_value = get_setting('MINIPASS_TIER', '')

if not stripe_sub_id or not tier_value:
    # Beta tester - show appreciation message
    return {
        'is_beta_tester': True,
        'tier': 3,  # Give Enterprise features
        'tier_name': 'Beta Tester',
        'tier_display': 'Beta Tester - Thank You!',
        'tier_price': 'Complimentary',
        'tier_activities': 100,  # Unlimited
        'activity_count': get_activity_count(),
        'activity_usage_display': 'Unlimited',
        'next_billing_date': None,
        'formatted_next_billing': 'N/A',
        'payment_amount': None,
        'formatted_payment_amount': 'N/A',
        'subscription_id': '',
        'customer_id': '',
        'billing_frequency': '',
        'is_paid_subscriber': False
    }

# Regular paid subscriber - continue with normal logic...
```

### 2.4 Update `get_subscription_details()`

**File:** `app/app.py`
**Lines:** 410-434

**Replace:**
```python
# Line 416
subscription_id = get_setting('STRIPE_SUBSCRIPTION_ID')
```

### 2.5 Update Current Plan Template

**File:** `app/templates/current_plan.html`

**Add beta tester message:** (after line 25, in the subscription card)
```html
{% if subscription_metadata.is_beta_tester %}
    <div class="alert alert-info" role="alert">
        <h4 class="alert-title">🎉 Thank you for being a Beta Tester!</h4>
        <div class="text-secondary">
            We greatly appreciate your help in improving Minipass. You have full access to all
            Enterprise features as our thank you. If you'd like to subscribe to continue using
            Minipass after the beta period, please contact us.
        </div>
    </div>
    <div class="card">
        <div class="card-body">
            <h3 class="card-title">Beta Tester Access</h3>
            <p class="text-secondary">All features unlocked - unlimited activities</p>
        </div>
    </div>
{% else %}
    <!-- Existing subscription display code -->
    ...
{% endif %}
```

---

## Part 3: Beta Tester Migration

### 3.1 Add TASK 18 to upgrade_production_database.py

**File:** `app/migrations/upgrade_production_database.py`
**Location:** After line 1329 (after task16_add_ai_answer_column)

**New function:**
```python
# ============================================================================
# TASK 18: Add Stripe Subscription Settings for Beta Testers
# ============================================================================
def task18_add_stripe_subscription_settings(cursor):
    """Add Stripe subscription setting keys with empty values for beta testers"""
    log("💳", "TASK 18: Adding Stripe subscription settings", Colors.BLUE)

    # Check if setting table exists
    if not check_table_exists(cursor, 'setting'):
        log("⏭️ ", "  setting table doesn't exist, skipping", Colors.YELLOW)
        return True

    stripe_settings = [
        ('STRIPE_CUSTOMER_ID', ''),
        ('STRIPE_SUBSCRIPTION_ID', ''),
        ('PAYMENT_AMOUNT', ''),
        ('SUBSCRIPTION_RENEWAL_DATE', ''),
        ('MINIPASS_TIER', ''),
        ('BILLING_FREQUENCY', '')
    ]

    added = 0
    skipped = 0

    for key, default_value in stripe_settings:
        # Check if setting already exists
        cursor.execute("SELECT id, value FROM setting WHERE key = ?", (key,))
        existing = cursor.fetchone()

        if existing:
            log("⏭️ ", f"  {key} already exists", Colors.YELLOW)
            skipped += 1
        else:
            try:
                cursor.execute("""
                    INSERT INTO setting (key, value)
                    VALUES (?, ?)
                """, (key, default_value))
                log("✅", f"  Added {key} with empty value", Colors.GREEN)
                added += 1
            except sqlite3.OperationalError as e:
                log("❌", f"  Failed to add {key}: {e}", Colors.RED)
                raise

    log("📊", f"  Summary: {added} settings added, {skipped} already existed")
    log("ℹ️ ", "  Empty values indicate beta tester - will show appreciation message", Colors.BLUE)
    return True
```

### 3.2 Update tasks list in main()

**File:** `app/migrations/upgrade_production_database.py`
**Lines:** 1480-1498

**Add to tasks list:**
```python
tasks = [
    # ... existing tasks ...
    ("AI Answer Column", task16_add_ai_answer_column),
    ("Stripe Subscription Settings", task18_add_stripe_subscription_settings),  # NEW
    ("Remove Organizations", task17_remove_organizations_table),
    ("Financial Views", task15_create_financial_views),
]
```

---

## Part 4: Testing Strategy

### 4.1 Unit Tests for Deployment Functions

**New file:** `MinipassWebSite/tests/test_stripe_settings_deployment.py`

**Test cases:**

1. **test_set_stripe_subscription_settings_insert()**
   - Setup: Create empty test database with Setting table
   - Action: Call `set_stripe_subscription_settings_to_database()` with sample data
   - Assert: All 6 settings inserted with correct values
   - Verify: Query Setting table and check each key/value pair

2. **test_set_stripe_subscription_settings_update()**
   - Setup: Database with existing Stripe settings
   - Action: Call function with new values
   - Assert: Settings updated (not duplicated)
   - Verify: Only one row per key exists, values changed

3. **test_stripe_settings_with_empty_values()**
   - Setup: Empty database
   - Action: Call function with empty strings for all values
   - Assert: Settings created with empty values
   - Verify: Beta tester scenario works

4. **test_env_file_without_stripe_data()**
   - Setup: Mock deployment parameters
   - Action: Generate .env file content
   - Assert: No STRIPE_CUSTOMER_ID, MINIPASS_TIER, etc. in output
   - Assert: STRIPE_SECRET_KEY (API key) IS present
   - Verify: Shared API keys preserved

5. **test_docker_compose_without_tier_vars()**
   - Setup: Mock deployment for production mode
   - Action: Generate docker-compose.yml content
   - Assert: No TIER, BILLING_FREQUENCY in environment section
   - Assert: VIRTUAL_HOST, LETSENCRYPT_HOST still present
   - Verify: Only proxy config remains

### 4.2 Unit Tests for Customer App Functions

**New file:** `app/tests/test_subscription_settings.py`

**Test cases:**

1. **test_get_subscription_tier_from_database()**
   ```python
   # Setup: Mock Setting table with MINIPASS_TIER=2
   # Action: Call get_subscription_tier()
   # Assert: Returns 2
   # Verify: Database query executed, env not checked
   ```

2. **test_get_subscription_tier_default_when_missing()**
   ```python
   # Setup: Empty Setting table, no env var
   # Action: Call get_subscription_tier()
   # Assert: Returns 1 (default)
   ```

3. **test_get_subscription_tier_fallback_to_env()**
   ```python
   # Setup: No database setting, but MINIPASS_TIER=3 in env
   # Action: Call get_subscription_tier()
   # Assert: Returns 3
   # Verify: get_setting() fallback works
   ```

4. **test_get_subscription_metadata_full_data()**
   ```python
   # Setup: Mock all 6 Stripe settings in database
   # Action: Call get_subscription_metadata()
   # Assert: All fields populated correctly
   # Verify: Data type conversions (cents to dollars, ISO date parsing)
   # Verify: is_beta_tester = False
   ```

5. **test_get_subscription_metadata_beta_tester()**
   ```python
   # Setup: Empty Setting table (no MINIPASS_TIER or STRIPE_SUBSCRIPTION_ID)
   # Action: Call get_subscription_metadata()
   # Assert: is_beta_tester = True
   # Assert: tier = 3 (Enterprise features)
   # Assert: tier_display = 'Beta Tester - Thank You!'
   # Assert: payment_amount = None
   # Verify: Appreciation message fields present
   ```

6. **test_get_subscription_details_from_database()**
   ```python
   # Setup: Mock STRIPE_SUBSCRIPTION_ID in Setting table
   # Mock Stripe API response
   # Action: Call get_subscription_details()
   # Assert: Calls Stripe API with correct subscription ID
   # Assert: Returns subscription status
   # Verify: Uses get_setting() not os.getenv()
   ```

7. **test_current_plan_page_paid_subscriber()**
   ```python
   # Setup: Mock session, set all Stripe settings
   # Action: GET /current-plan
   # Assert: Status code 200
   # Verify: Template shows subscription info
   # Verify: No beta tester message
   ```

8. **test_current_plan_page_beta_tester()**
   ```python
   # Setup: Mock session, empty Setting table
   # Action: GET /current-plan
   # Assert: Status code 200
   # Verify: Template shows "Thank you for being a Beta Tester!"
   # Verify: No billing information displayed
   # Verify: "All features unlocked" message present
   ```

### 4.3 Integration Test for Migration Script

**Test file:** `app/tests/test_upgrade_production_database.py`

**Test case: test_task18_add_stripe_settings()**
```python
def test_task18_add_stripe_settings():
    # Setup: Create test database
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    # Create Setting table
    cursor.execute("""
        CREATE TABLE setting (
            id INTEGER PRIMARY KEY,
            key VARCHAR(100) UNIQUE NOT NULL,
            value TEXT
        )
    """)

    # Action: Run task18
    from migrations.upgrade_production_database import task18_add_stripe_subscription_settings
    result = task18_add_stripe_subscription_settings(cursor)

    # Assert: Task succeeded
    assert result == True

    # Verify: All 6 settings added
    cursor.execute("SELECT COUNT(*) FROM setting WHERE key LIKE 'STRIPE_%' OR key IN ('MINIPASS_TIER', 'BILLING_FREQUENCY')")
    count = cursor.fetchone()[0]
    assert count == 6

    # Verify: All values are empty strings
    cursor.execute("SELECT value FROM setting WHERE key = 'STRIPE_CUSTOMER_ID'")
    value = cursor.fetchone()[0]
    assert value == ''

    # Verify: Idempotent - running again doesn't duplicate
    result2 = task18_add_stripe_subscription_settings(cursor)
    assert result2 == True
    cursor.execute("SELECT COUNT(*) FROM setting")
    final_count = cursor.fetchone()[0]
    assert final_count == 6  # Still 6, not 12

    conn.close()
```

### 4.4 Manual Testing Checklist

**Test 1: New Deployment (Paid Subscriber)**
- [ ] Deploy test customer with tier 1, valid Stripe data
- [ ] SSH into deployed container
- [ ] Check Setting table: `sqlite3 instance/minipass.db "SELECT * FROM setting WHERE key LIKE 'STRIPE_%' OR key IN ('MINIPASS_TIER', 'BILLING_FREQUENCY');"`
- [ ] Verify all 6 settings exist with correct values
- [ ] Check .env file: `cat .env`
- [ ] Verify NO Stripe data in .env
- [ ] Verify shared API keys ARE in .env
- [ ] Access app at `https://testcustomer.minipass.me/current-plan`
- [ ] Verify subscription info displays correctly
- [ ] Verify tier name, activity limit, billing date, amount all correct
- [ ] Create activity to test tier limit enforcement

**Test 2: Beta Tester (Existing Deployment)**
- [ ] SSH into LHGI container
- [ ] Run migration: `python migrations/upgrade_production_database.py`
- [ ] Verify output shows "TASK 18: Adding Stripe subscription settings"
- [ ] Verify output shows "6 settings added"
- [ ] Check Setting table: `sqlite3 instance/minipass.db "SELECT * FROM setting WHERE key LIKE 'STRIPE_%';"`
- [ ] Verify all values are empty strings
- [ ] Access `https://lhgi.minipass.me/current-plan`
- [ ] Verify "Thank you for being a Beta Tester!" message displays
- [ ] Verify no billing information shown
- [ ] Verify "All features unlocked - unlimited activities" message
- [ ] Try creating multiple activities (should work - no limit)

**Test 3: Upgrade Simulation (Future)**
- [ ] Deploy customer with tier 1
- [ ] Manually update Setting table to tier 2:
  ```sql
  UPDATE setting SET value = '2' WHERE key = 'MINIPASS_TIER';
  UPDATE setting SET value = 'sub_newID123' WHERE key = 'STRIPE_SUBSCRIPTION_ID';
  ```
- [ ] Refresh /current-plan page (no container restart)
- [ ] Verify tier updated to "Professional"
- [ ] Verify activity limit updated to 15
- [ ] Verify no container restart was needed

---

## Part 5: Implementation Sequence

### Step 1: Deployment Script (3-4 hours)
1. Create `set_stripe_subscription_settings_to_database()` function
2. Update `.env` generation to remove Stripe data
3. Call new function during deployment
4. Simplify docker-compose.yml generation
5. Write unit tests for deployment functions
6. Manual test: Deploy one test customer
7. Verify Setting table populated correctly

### Step 2: Migration Script (1-2 hours)
1. Add `task18_add_stripe_subscription_settings()` to upgrade script
2. Update tasks list in main()
3. Write unit test for migration task
4. Manual test: Run on LHGI beta tester
5. Verify empty settings created

### Step 3: Customer App (2-3 hours)
1. Update `get_subscription_tier()` to use `get_setting()`
2. Update `get_subscription_metadata()` to use `get_setting()`
3. Add beta tester detection logic
4. Update `get_subscription_details()` to use `get_setting()`
5. Update Current Plan template for beta tester message
6. Write unit tests for app functions
7. Manual test: Access /current-plan on both paid and beta deployments

### Step 4: Verification (1 hour)
1. Run all unit tests
2. Complete manual testing checklist
3. Verify no regressions
4. Document any issues found

---

## Part 6: Success Criteria

✅ **Deployment Script:**
- New deployments write Stripe data to Setting table only
- .env file contains only shared API keys (no customer-specific data)
- docker-compose.yml has no tier environment variables

✅ **Customer App:**
- Current Plan page reads from database (not .env)
- Paid subscribers see normal subscription info
- Beta testers see "Thank you" message with no billing info

✅ **Migration:**
- Beta tester deployments (LHGI) have empty Stripe settings
- upgrade_production_database.py adds 6 settings successfully
- Migration is idempotent (can run multiple times)

✅ **Testing:**
- All unit tests pass (deployment + app)
- Manual testing checklist 100% complete
- No regressions in existing functionality

✅ **Future-Proof:**
- Tier upgrades can be done via database UPDATE (no container restart)
- Architecture supports webhook-driven upgrades
- Clean separation: infrastructure (.env) vs customer data (database)

---

## Part 7: Rollback Strategy

**If something goes wrong:**

1. **Database rollback** (if migration fails):
   ```bash
   # Restore from backup
   cp instance/minipass.db.backup instance/minipass.db
   ```

2. **Code rollback** (if app changes break):
   - `get_setting()` already has fallback to environment variables
   - Existing .env files haven't been deleted
   - Just revert app.py changes to restore os.getenv() calls

3. **Deployment rollback** (if new deployments fail):
   - Keep both old and new deployment functions
   - Add feature flag to choose which path
   - Or: just fix the bug and redeploy

**Safety features:**
- Migration script is idempotent (safe to re-run)
- `get_setting()` has env var fallback
- All changes are backwards compatible
- Database changes are additive (won't break existing data)

---

## Part 8: Timeline & Effort Estimate

| Phase | Task | Estimated Time |
|-------|------|----------------|
| 1 | Deployment script changes | 3-4 hours |
| 2 | Migration script | 1-2 hours |
| 3 | Customer app changes | 2-3 hours |
| 4 | Verification & testing | 1 hour |
| **Total** | **Complete implementation** | **7-10 hours** |

**Note:** This assumes one developer working sequentially. Time could be reduced if deployment and app changes are done in parallel.

---

## Appendix A: Key Files Modified

**MinipassWebSite (Deployment System):**
- `utils/deploy_helpers.py` - New function, .env generation, docker-compose generation

**app (Customer Application):**
- `app.py` - Three function updates (get_subscription_tier, get_subscription_metadata, get_subscription_details)
- `templates/current_plan.html` - Beta tester message
- `migrations/upgrade_production_database.py` - New TASK 18

**Tests:**
- `MinipassWebSite/tests/test_stripe_settings_deployment.py` - New file
- `app/tests/test_subscription_settings.py` - New file
- `app/tests/test_upgrade_production_database.py` - New test case

---

## Appendix B: Database Schema Changes

**New Settings added to `setting` table:**

| Key | Value (New Deployments) | Value (Beta Testers) | Type |
|-----|------------------------|----------------------|------|
| STRIPE_CUSTOMER_ID | `cus_xxxxx` | `''` (empty) | TEXT |
| STRIPE_SUBSCRIPTION_ID | `sub_xxxxx` | `''` (empty) | TEXT |
| PAYMENT_AMOUNT | `7200` (cents) | `''` (empty) | TEXT |
| SUBSCRIPTION_RENEWAL_DATE | `2026-11-22T19:36:23` | `''` (empty) | TEXT |
| MINIPASS_TIER | `1`, `2`, or `3` | `''` (empty) | TEXT |
| BILLING_FREQUENCY | `monthly` or `annual` | `''` (empty) | TEXT |

**No schema changes needed** - Setting table already exists with `key` and `value` columns.

---

## Appendix C: References

**Existing patterns to follow:**
- Email settings: `set_email_settings_to_database()` (lines 181-276 in deploy_helpers.py)
- Organization settings: `set_organization_setting()` (lines 99-178 in deploy_helpers.py)
- Migration tasks: All tasks in upgrade_production_database.py
- `get_setting()` function: lines 363-392 in app/utils.py

**Related documentation:**
- `/home/kdresdell/Documents/DEV/minipass_env/Marketing/PRD.md` - Product requirements
- `/home/kdresdell/Documents/DEV/minipass_env/CLAUDE.md` - Project architecture
- `/home/kdresdell/Documents/DEV/minipass_env/app/CLAUDE.md` - App development guidelines

---

**END OF PLAN**

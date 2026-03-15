# Stripe Credit Card Payment Accounting Strategy

## Context

Minipass currently has two payment methods:

1. **Interac E-transfer** (existing, fully automated):
   - Payment received instantly
   - Full amount deposited (no fees)
   - Automatically matched via email parsing
   - Creates Passport + updates financial views

2. **Stripe Credit Card** (newly implemented, incomplete accounting):
   - Payment authorized instantly via Stripe Checkout
   - Webhook creates Passport and marks as paid
   - **Missing**: No Income transaction created
   - **Missing**: No fee tracking
   - **Challenge**: 7-day payout delay (funds in transit)
   - **Challenge**: Stripe takes 2.9% + $0.30 fee before deposit

### Current Implementation Gap

When Stripe webhook fires on `checkout.session.completed`:
- ✅ Creates Passport with `paid=True`, `marked_paid_by="stripe-checkout"`
- ✅ Sends customer confirmation email
- ❌ Does NOT create Income record in accounting system
- ❌ Does NOT record processing fees
- ❌ Does NOT track funds in transit

**Result**: Financial reports (SQL views) show **zero revenue** from Stripe payments because Income table is empty for credit card sales.

---

## Research Summary: Industry Best Practices

### 1. Revenue Recognition (GAAP/ASC 606 Compliant)

**When to recognize revenue:**
- **Accrual Basis** (recommended for SaaS): Recognize revenue when **earned** (at time of successful Stripe checkout), NOT when cash is deposited
- **Cash Basis**: Recognize revenue only when funds hit your bank account (7 days later)

**Industry standard for SaaS**: Use accrual accounting per ASC 606/IFRS 15 standards [Source: [SaaS Revenue Recognition 101 | Stripe](https://stripe.com/resources/more/a-guide-to-revenue-recognition-for-saas-businesses)]

### 2. Payment Processing Fees Treatment

**GAAP guidance** [Source: [How to Account for Payment Processing Costs](https://www.linkedin.com/advice/1/how-do-you-account-payment-processing-costs-cq6xe)]:
- **Record as Operating Expense** (preferred, GAAP-compliant)
- Category: "Payment Processing Fees" under SG&A or COGS
- **Do NOT use contra-revenue** (not standard practice under GAAP)

**Fee calculation for Stripe**:
- Standard rate: 2.9% + $0.30 per successful charge
- Stripe deducts fees automatically before payout
- Fees are **non-refundable** even if payment is refunded [Source: [Guide to Stripe Fees 2025](https://www.swipesum.com/insights/guide-to-stripe-fees-rates-for-2025)]

### 3. Handling Payout Delay ("Funds in Transit")

**Best practice** [Source: [Stripe Clearing Account Reconciliation | Puzzle](https://help.puzzle.io/en/articles/8422710-how-do-i-reconcile-stripe-clearing-accounts)]:
1. Create a "Stripe Clearing Account" (asset account type: Bank/Checking)
2. When payment authorized: Record full revenue + AR to Stripe Clearing
3. When payout received: Transfer from Stripe Clearing to Bank Account (minus fees)

**Journal entries example**:

**Day 0 - Customer pays $100 via Stripe:**
```
Dr. Stripe Clearing Account ........ $100.00
   Cr. Revenue (Income) ............ $100.00
```

**Day 7 - Stripe deposits $97.20 to bank ($100 - 2.9% - $0.30):**
```
Dr. Bank Account ................... $97.20
Dr. Payment Processing Fees ........ $2.80
   Cr. Stripe Clearing Account ..... $100.00
```

**Result**: Net Stripe balance is always $0 after payout, revenue is $100, expense is $2.80.

---

## Options for Minipass

### Option 1: Simple Approach - Record at Webhook Time (Accrual Basis)

**When Stripe webhook fires** (`checkout.session.completed`):
1. Create Income record:
   - `amount` = full charge amount (e.g., $100)
   - `category` = "Passport Sales" (same as Interac)
   - `date` = webhook timestamp
   - `payment_status` = "received"
   - `payment_method` = "credit_card"
   - `note` = "Stripe session: ses_xxxxx"

2. Create Expense record for fee:
   - `amount` = stripe_fee (2.9% + $0.30)
   - `category` = "Payment Processing Fees"
   - `date` = webhook timestamp
   - `payment_status` = "paid"

**Pros:**
- ✅ Simple to implement
- ✅ GAAP-compliant (accrual basis)
- ✅ Revenue appears immediately in reports
- ✅ Consistent with existing Income/Expense model

**Cons:**
- ❌ No tracking of funds in transit
- ❌ Actual bank deposit date not recorded
- ❌ Cannot reconcile bank statement timing easily

**Best for**: Small businesses, simplified accounting, when payout delay is not critical to track.

---

### Option 2: Clearing Account Approach (Industry Standard)

**Create new data model**:
```python
class StripeTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    charge_id = db.Column(db.String(100))  # Stripe charge ID
    session_id = db.Column(db.String(100))  # Checkout session ID
    gross_amount = db.Column(db.Float)  # Full charge amount
    stripe_fee = db.Column(db.Float)  # Calculated fee
    net_amount = db.Column(db.Float)  # Amount deposited to bank
    charge_date = db.Column(db.DateTime)  # When charged
    payout_date = db.Column(db.DateTime)  # When deposited (nullable)
    payout_id = db.Column(db.String(100))  # Stripe payout ID
    signup_id = db.Column(db.Integer, db.ForeignKey('signup.id'))
    passport_id = db.Column(db.Integer, db.ForeignKey('passport.id'))
    status = db.Column(db.String(20))  # "pending", "paid_out", "refunded"
```

**Workflow**:

1. **At webhook** (`checkout.session.completed`):
   - Create StripeTransaction (status="pending")
   - Create Passport (existing behavior)
   - Create Income record (amount = gross, payment_status="pending")

2. **When payout received** (use Stripe `payout.paid` webhook):
   - Update StripeTransaction (status="paid_out", payout_date, payout_id)
   - Update Income (payment_status="received", payment_date=payout_date)
   - Create Expense for stripe_fee

**Pros:**
- ✅ Full audit trail of Stripe transactions
- ✅ Track actual payout dates
- ✅ Reconcile with bank statements easily
- ✅ Support refunds/chargebacks properly
- ✅ Industry best practice

**Cons:**
- ❌ More complex implementation (new model + 2 webhooks)
- ❌ Requires Stripe payout webhook setup
- ❌ More data to manage

**Best for**: Scaling businesses, accurate cash flow tracking, professional accounting standards.

---

### Option 3: Hybrid - Simple Now, Clearing Later

**Phase 1 (Immediate)**:
- Implement Option 1 (simple approach)
- At least get revenue and fees into system

**Phase 2 (Future enhancement)**:
- When Stripe volume grows, migrate to Option 2
- Add StripeTransaction model
- Enable payout webhook tracking

**Pros:**
- ✅ Quick to implement
- ✅ Gets accounting functional now
- ✅ Can upgrade later without breaking changes

**Cons:**
- ❌ Requires future refactoring
- ❌ May have dual accounting periods (before/after upgrade)

---

## Recommended Approach for Minipass

### **Choose Option 1: Simple Accrual Accounting**

**Rationale:**
1. **Current scale**: Stripe is new feature, likely low volume initially
2. **Existing model compatibility**: Uses current Income/Expense tables
3. **User needs**: You need "clean, lean, one source of truth" - Option 1 achieves this
4. **Implementation speed**: Can be live in 30 minutes vs. 3+ hours for Option 2
5. **Upgrade path**: Can migrate to Option 2 later if Stripe becomes 50%+ of revenue

### Implementation Details

**File to modify**: `app/app.py` - Stripe webhook handler (lines 2308-2378)

**Changes required**:

1. Add Income record creation in webhook handler:
```python
# After auto_create_passport_from_signup()
income = Income(
    activity_id=signup.activity_id,
    amount=signup.requested_amount,
    category="Passport Sales",
    date=datetime.now(timezone.utc),
    payment_status="received",
    payment_date=datetime.now(timezone.utc),
    payment_method="credit_card",
    note=f"Stripe Checkout - Session: {session_id}",
    created_by="stripe-webhook"
)
db.session.add(income)
```

2. Calculate and record Stripe fee as Expense:
```python
# Calculate Stripe fee (2.9% + $0.30)
stripe_fee = round((signup.requested_amount * 0.029) + 0.30, 2)

expense = Expense(
    activity_id=signup.activity_id,
    amount=stripe_fee,
    category="Payment Processing Fees",
    date=datetime.now(timezone.utc),
    payment_status="paid",
    payment_date=datetime.now(timezone.utc),
    payment_method="stripe",
    note=f"Stripe fee for session {session_id}",
    created_by="stripe-webhook"
)
db.session.add(expense)
```

3. Add error handling and idempotency check (prevent duplicate records if webhook fires twice)

4. Update AdminActionLog for audit trail

### SQL View Impact

**No changes needed** to existing views:
- `view1_monthly_transactions_detail.sql` - Already includes Income and Expense tables
- `view2_monthly_financial_summary.sql` - Will automatically include credit card sales in revenue/expenses

**Result**: Credit card sales will appear in financial reports immediately after implementation.

---

## Future Considerations

### When to Upgrade to Option 2 (Clearing Account)

Migrate when ANY of these occur:
- Stripe revenue exceeds $10,000/month
- Monthly reconciliation becomes time-consuming
- Accountant requests detailed payout tracking
- You need to track refunds/chargebacks separately
- You integrate with accounting software (QuickBooks/Xero)

### Additional Enhancements

1. **Stripe fee as dynamic setting**: Store fee percentage in Settings table instead of hardcoding 2.9%
2. **Refund handling**: Add webhook for `charge.refunded` to reverse Income/Expense
3. **Failed payments**: Track `checkout.session.expired` for abandoned carts
4. **Multi-currency**: Handle currency conversion fees if expanding internationally

---

## Implementation Checklist

- [ ] Read current webhook handler code (`app.py:2308-2378`)
- [ ] Add Income record creation after passport creation
- [ ] Calculate and record Stripe fee as Expense
- [ ] Add idempotency check (prevent duplicate records)
- [ ] Test with Stripe test mode checkout
- [ ] Verify Income/Expense appear in financial reports
- [ ] Test refund scenario (optional for Phase 1)
- [ ] Document new behavior in `docs/CHANGELOG.md`
- [ ] Update `docs/PRODUCT.md` with fee handling details

---

## Testing Plan

1. **Test Mode Checkout**:
   - Create test signup with Stripe payment
   - Complete checkout with test card (4242 4242 4242 4242)
   - Verify webhook creates: Passport + Income + Expense

2. **Verify Financial Report**:
   - Navigate to `/reports/financial`
   - Confirm credit card sale appears in transactions list
   - Check revenue total includes Stripe amount
   - Check expenses include processing fee

3. **Verify SQL Views**:
   - Query `view1_monthly_transactions_detail` - should show Income and Expense rows
   - Query `view2_monthly_financial_summary` - cash_received should include Stripe revenue

4. **Edge Cases**:
   - Duplicate webhook delivery (should not create duplicate Income)
   - Webhook fired but Passport already exists (should handle gracefully)

---

## Sources

Research based on 2026 industry standards:

- [SaaS Revenue Recognition 101 | Stripe](https://stripe.com/resources/more/a-guide-to-revenue-recognition-for-saas-businesses)
- [SaaS Accounting 101: Methods, Strategies, and KPIs | Stripe](https://stripe.com/resources/more/saas-accounting-101)
- [Guide to Stripe Fees & Rates for 2025](https://www.swipesum.com/insights/guide-to-stripe-fees-rates-for-2025)
- [How Stripe Fees Work in 2026: A Complete Cost Breakdown](https://globalfeecalculator.com/blog/how-stripe-fees-work/)
- [Cash-based Accounting: A Guide to the Cash Basis | Stripe](https://stripe.com/resources/more/what-is-cash-based-accounting-here-is-what-businesses-need-to-know)
- [Stripe Revenue Recognition: A Complete Guide](https://www.hubifi.com/blog/accounting-for-revenue-recognition-asc-606-stripe)
- [How do I Reconcile Stripe Clearing Accounts? | Puzzle](https://help.puzzle.io/en/articles/8422710-how-do-i-reconcile-stripe-clearing-accounts)
- [Accounting for Credit Card Fees | Proformative](https://www.proformative.com/questions/accounting-for-credit-card-fees/)
- [How to Account for Payment Processing Costs](https://www.linkedin.com/advice/1/how-do-you-account-payment-processing-costs-cq6xe)
- [Best Accounting Practices for Stripe + QuickBooks](https://www.greenback.com/blog/best-accounting-practices-stripe-quickbooks/27)

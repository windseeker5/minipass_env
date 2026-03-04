# Minipass — Architecture & Data Flow

---

## The Big Picture — 3 Separate Systems

```
┌─────────────────────────────────────────────────────────────────────┐
│                           STRIPE                                    │
│                   (external payment processor)                      │
│                                                                     │
│  • Holds all subscription data (plan, price, status, dates)        │
│  • Charges customers automatically on renewal                       │
│  • Fires webhook events when anything changes                       │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ webhooks (HTTPS events)
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│               MINIPASSWEBSITE  (minipass.me)                        │
│                   MinipassWebSite/app.py                            │
│                                                                     │
│  • YOUR company's website and admin backend                         │
│  • Receives ALL Stripe webhook events                               │
│  • Owns customers.db — master list of every customer                │
│  • Deploys new customer containers                                  │
│  • Syncs plan changes down into each customer's app DB             │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ writes directly to customer app DB
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  KDC Corp    │  │    LHGI      │  │  Customer C  │
│   app/       │  │   app/       │  │   app/       │
│  port 5000   │  │  port 8001   │  │  port 8002   │
│              │  │              │  │              │
│ minipass.db  │  │ minipass.db  │  │ minipass.db  │
│  (Setting    │  │  (Setting    │  │  (Setting    │
│   table)     │  │   table)     │  │   table)     │
└──────────────┘  └──────────────┘  └──────────────┘

Each customer app is completely isolated.
Each has its own database, its own login, its own data.
```

---

## The Two Databases

```
customers.db  (lives in MinipassWebSite/)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR master record of all customers.
One row per customer.

  subdomain | plan | billing_frequency | stripe_subscription_id | payment_amount | ...
  ──────────────────────────────────────────────────────────────────────────────────
  kdc       | pro  | annual            | sub_1Siz...            | 30000          | ...
  lhgi      | basic| monthly           | sub_1Abc...            | 2000           | ...


minipass.db  (lives inside EACH customer's app/instance/)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The customer's OWN app database.
The Setting table stores their plan so the app knows what to show/allow.

  Setting table (kdc's minipass.db):
  key                    | value
  ───────────────────────────────────────────────
  MINIPASS_TIER          | 2
  BILLING_FREQUENCY      | annual
  STRIPE_SUBSCRIPTION_ID | sub_1Siz...
  PAYMENT_AMOUNT         | 30000
  ... (many other settings like org name, email config, etc.)
```

---

## Flow 1 — Customer Changes Plan

```
CUSTOMER'S BROWSER
        │
        │  clicks "Upgrade to Enterprise"
        │  POST /current-plan  action=change_plan
        ▼
CUSTOMER APP  (app/app.py on port 5000)
        │
        │  calls stripe.Subscription.modify()
        │  with the new price ID
        ▼
STRIPE API
        │
        │  ✅ subscription updated immediately
        │  (customer now on Enterprise in Stripe's system)
        │
        │  fires customer.subscription.updated  ──────────────────┐
        │                                                          │
        ▼                                                          ▼
CUSTOMER APP                                           MINIPASSWEBSITE
returns success flash                                  receives webhook
to browser                                                    │
        │                                                     │  update_customer_plan()
        │                                                     │  → writes to customers.db
        │                                                     │
        │                                                     │  set_stripe_subscription_settings_to_database()
        │                                                     │  → connects to kdc's minipass.db
        │                                                     │  → writes MINIPASS_TIER=3
        │                                                     │    BILLING_FREQUENCY=annual
        │                                                     │    PAYMENT_AMOUNT=72000
        │                                                     │
        ▼                                                     │
CUSTOMER'S BROWSER                                           ✅
page reloads
        │
        ▼
CUSTOMER APP reads MINIPASS_TIER from minipass.db
→ shows "Enterprise" on the page  ✅
```

---

## Flow 2 — Customer Cancels Auto-Renewal

```
CUSTOMER'S BROWSER
        │  clicks "Cancel Auto-Renewal"
        ▼
CUSTOMER APP  (app/app.py)
        │
        │  calls stripe.Subscription.modify(cancel_at_period_end=True)
        ▼
STRIPE API
        │  ✅ subscription flagged to cancel at period end
        │  customer keeps full access until renewal date
        │
        │  fires customer.subscription.updated
        ▼
MINIPASSWEBSITE
        │  detects cancel_at_period_end=True, price unchanged
        │  update_customer_plan(subscription_status='active')
        │  → no plan change, just status update in customers.db
        ▼
CUSTOMER APP  (next page load)
        │  get_subscription_details() calls Stripe API
        │  sees cancel_at_period_end=True
        │  shows "Cancelling" badge + end date  ✅
```

---

## Flow 3 — Subscription Expires (No Action Taken)

```
[renewal date arrives, customer did not reactivate]

STRIPE
  → does NOT charge the customer
  → sets subscription status = "canceled"
  → fires customer.subscription.updated (or customer.subscription.deleted)

MINIPASSWEBSITE  (receives webhook)
  → update_customer_plan(subscription_status='canceled')
  → updates customers.db

CUSTOMER APP  (next login)
  → get_subscription_details() → status = "canceled"
  → shows "Cancelled" badge
  → shows "Subscribe" button linking to minipass.me
  → activity creation is blocked (usage limit enforced)
```

---

## Flow 4 — New Customer Subscribes (How a Container is Born)

```
VISITOR on minipass.me
        │  clicks "Subscribe", fills form, pays with card
        ▼
STRIPE  → charges card → fires checkout.session.completed
        ▼
MINIPASSWEBSITE  (receives webhook)
        │
        ├─ creates row in customers.db
        ├─ copies app/ template to deployed/[subdomain]/
        ├─ writes .env file with Stripe keys, tier, etc.
        ├─ creates minipass.db with initial Settings
        ├─ builds Docker container
        ├─ creates subdomain (e.g. kdc.minipass.me)
        ├─ creates SSL certificate
        ├─ creates email account
        └─ sends welcome email with login credentials
```

---

## Why the Dev Environment is Tricky

In production, everything runs simultaneously in Docker and Stripe webhooks hit `minipass.me` directly.

In development on your laptop:

```
PROBLEM:
━━━━━━━
You run the customer app on port 5000  ✅
MinipassWebSite is NOT running locally ❌

stripe listen --forward-to localhost:5000 ← WRONG PORT
  (port 5000 is the customer app, it has no webhook endpoint)

stripe listen --forward-to localhost:5001 ← RIGHT PORT
  BUT MinipassWebSite is not running, so it refuses the connection

RESULT: Webhook events go nowhere → minipass.db never updates → display stays stale


SOLUTION for dev testing plan changes:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Option A — Start MinipassWebSite locally on port 5001
           AND run: stripe listen --forward-to localhost:5001/stripe-webhook

Option B — After changing plan, manually update minipass.db:
           sqlite3 app/instance/minipass.db
           UPDATE setting SET value='3' WHERE key='MINIPASS_TIER';

Option C — Verify via Stripe API that the subscription changed (what we did)
           The Stripe change is REAL even if the display doesn't update yet
```

---

## What Each System "Owns"

```
STRIPE owns:
  • The subscription (status, plan, price, dates)
  • The payment method
  • The invoice history
  • The source of truth for billing

customers.db owns:
  • The list of all Minipass customers
  • A COPY of Stripe data (plan, billing_frequency, payment_amount)
  • Deployment info (subdomain, port, email account)

minipass.db (per customer) owns:
  • That customer's activities, signups, passports, members
  • Their Settings (a COPY of MINIPASS_TIER, BILLING_FREQUENCY, etc.)
  • Their email/notification configuration
  • Their QR codes and digital passes
```

---

## One-Line Summary

> **Stripe is the bank. MinipassWebSite is the office manager. Each customer app is a tenant in the building. When Stripe says the rent changed, it tells the office manager, who updates both the master ledger (customers.db) and posts a note inside the tenant's apartment (minipass.db).**

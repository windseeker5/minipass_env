# Plan Changes and Proration — How It Works

When you change your Minipass subscription plan, billing is adjusted automatically and fairly. This guide explains exactly what happens to your money in every scenario.

---

## The Short Version

- **All plan changes take effect instantly** — no waiting until your next cycle.
- **Proration** means Stripe calculates a credit for the unused time on your old plan and charges you for the new plan, covering only the days remaining in your billing period.
- **Credits appear on your next invoice** — Stripe does not issue card refunds for prorations; instead, the credit is applied to reduce what you owe next time.
- **Switching to annual saves ~17%** compared to paying monthly.

---

## Minipass Plans at a Glance

| Plan | Monthly | Annual | Activities |
|---|---|---|---|
| **Starter** | $20 / month | $120 / year | 1 |
| **Professional** | $50 / month | $300 / year | 15 |
| **Enterprise** | $120 / month | $720 / year | 100 |

---

## Scenario 1 — Upgrade on a Monthly Plan (Same Billing Frequency)

**Example:** You are on Professional Monthly ($50/mo) and upgrade to Enterprise Monthly ($120/mo) with 15 days left in your billing period.

**What Stripe does:**
1. Credits you ~$25 for the unused 15 days of Professional ($50 × 15/30 days)
2. Charges you ~$60 for 15 days of Enterprise ($120 × 15/30 days)
3. Net charge on your next invoice: **~$35** (the difference)
4. Enterprise access (100 activities) starts **immediately**

> **Key point:** You never pay for both plans simultaneously. You only pay the difference for the remaining days.

---

## Scenario 2 — Upgrade on an Annual Plan (Same Billing Frequency)

**Example:** You are on Starter Annual ($120/yr) and upgrade to Professional Annual ($300/yr) halfway through your year (183 days remaining).

**What Stripe does:**
1. Credits you ~$60 for the unused 183 days of Starter ($120 × 183/365 days)
2. Charges you ~$150 for 183 days of Professional ($300 × 183/365 days)
3. Net charge on your next invoice: **~$90**
4. Professional access (15 activities) starts **immediately**

---

## Scenario 3 — Downgrade on a Monthly Plan

**Example:** You are on Enterprise Monthly ($120/mo) and downgrade to Starter Monthly ($20/mo) with 10 days left in your billing period.

**What Stripe does:**
1. Credits you ~$40 for the unused 10 days of Enterprise ($120 × 10/30 days)
2. Charges you ~$6.67 for 10 days of Starter ($20 × 10/30 days)
3. Net **credit of ~$33** appears on your account — reduces your next invoice
4. Starter access (1 activity) takes effect **immediately**

> **Important:** If your account has more than 1 active activity when you downgrade to Starter, your existing activities are not deleted — but you will not be able to create new ones until you are within your plan's limit.

---

## Scenario 4 — Downgrade on an Annual Plan

**Example:** You are on Enterprise Annual ($720/yr) and downgrade to Professional Annual ($300/yr) with 200 days remaining in your year.

**What Stripe does:**
1. Credits you ~$394 for the unused 200 days of Enterprise ($720 × 200/365 days)
2. Charges you ~$164 for 200 days of Professional ($300 × 200/365 days)
3. Net **credit of ~$230** on your account
4. Professional access (15 activities) takes effect **immediately**

---

## Scenario 5 — Switch from Monthly to Annual (Same Tier)

**Example:** You are on Professional Monthly ($50/mo) and switch to Professional Annual ($300/yr) with 20 days left in your current monthly period.

**What Stripe does:**
1. Credits you ~$33 for the unused 20 days of monthly Professional
2. Charges you **$300** for the full new Annual Professional plan
3. Your new annual period starts today and renews in 12 months
4. Net on next invoice: **$300 − $33 = ~$267**

> This is the most cost-effective switch — you lock in the lower annual rate immediately and get a credit for the time you already paid monthly.

---

## Scenario 6 — Switch from Annual to Monthly (Same Tier)

**Example:** You are on Professional Annual ($300/yr) and switch to Professional Monthly ($50/mo) with 200 days remaining in your year.

**What Stripe does:**
1. Credits you ~$164 for the unused 200 days of your annual plan ($300 × 200/365 days)
2. Charges you $50 for your first monthly period
3. Net on next invoice: **$50 − $164 = −$114** (full credit, nothing owed yet)
4. That credit carries forward and covers your next 2–3 monthly invoices

> **Note:** Switching annual → monthly costs more over time. You give up the annual discount and start paying the higher monthly rate.

---

## Scenario 7 — Upgrade Tier and Switch to Annual at Once

**Example:** You are on Starter Monthly ($20/mo) and switch to Enterprise Annual ($720/yr) with 10 days left in your monthly period.

**What Stripe does:**
1. Credits you ~$6.67 for the unused 10 days of Starter Monthly
2. Charges you **$720** for the full Enterprise Annual plan
3. Enterprise access (100 activities) starts **immediately**
4. Next renewal is in 12 months

---

## Scenario 8 — Downgrade Tier and Switch to Monthly at Once

**Example:** You are on Enterprise Annual ($720/yr) and switch to Starter Monthly ($20/mo) with 100 days remaining in your year.

**What Stripe does:**
1. Credits you ~$197 for the unused 100 days of Enterprise Annual ($720 × 100/365 days)
2. Charges you $20 for the first Starter Monthly period
3. Net credit of ~$177 carries forward on your account
4. Starter access (1 activity) takes effect **immediately**

---

## Scenario 9 — Cancel Auto-Renewal

You choose to **cancel auto-renewal** on your current plan. This does not cancel your access immediately.

**What happens:**
- Your plan remains fully active until the end of your current billing period (monthly or annual)
- No refund is issued — you keep everything you paid for
- On the renewal date, your subscription expires and access is removed
- The Subscription page will show a **Cancelling** badge with the exact end date

**Example:** You are on Professional Annual ($300/yr) and cancel on March 4. If your annual cycle ends on March 4 next year, you have full Professional access until then.

> You can **reactivate auto-renewal** at any time before the end date — just click "Reactivate Auto-Renewal" on your Subscription page.

---

## Scenario 10 — Reactivate After Cancelling

You cancelled auto-renewal but changed your mind before the end date.

**What happens:**
- Click **Reactivate Auto-Renewal** on your Subscription page
- Your subscription resumes its normal renewal cycle — no gaps in access
- You are charged again on the original renewal date as usual
- No proration applies — nothing changes except auto-renewal is turned back on

---

## Frequently Asked Questions

### Will I lose my data if I downgrade?

No. All your activities, signups, passports, and member data are preserved. However, if you exceed your new plan's activity limit (for example, you have 5 activities and downgrade to Starter which allows 1), you will not be able to create new activities until you are within your limit. Existing activities and their data are not deleted.

### When does the credit appear?

Proration credits appear on your **next invoice**, not immediately. Stripe applies the credit automatically — you do not need to do anything. If the credit exceeds the next invoice amount, it rolls forward to the one after that.

### Can I switch plans multiple times?

Yes. Each plan change recalculates proration from the current date. There is no penalty or limit on how often you can switch.

### Does switching from annual to monthly restart my billing date?

Yes. When you switch billing frequency, a new billing cycle starts from today. Your old annual cycle is credited and a new monthly (or annual) cycle begins immediately.

### What if my credit card is declined during a proration charge?

Stripe retries declined charges automatically. Your access remains active during the retry window. You will receive an email if a payment fails — update your payment method in your Stripe billing portal to resolve it.

### Is there a way to get a refund to my card?

Standard proration does not issue card refunds — credits stay on your Stripe account and are applied to future invoices. If you need a direct refund, contact us at support@minipass.me and we will review your case.

---

## Summary Table

| Scenario | Effect on Access | Effect on Billing |
|---|---|---|
| Upgrade (any) | Immediate | Prorated charge on next invoice |
| Downgrade (any) | Immediate | Prorated credit on next invoice |
| Monthly → Annual | Immediate, renews in 12 months | Annual charge minus monthly credit |
| Annual → Monthly | Immediate, renews monthly | Monthly charge, large credit rolls forward |
| Cancel auto-renewal | Active until end of period | No refund, no future charge |
| Reactivate auto-renewal | Continues normally | Charged again on original renewal date |
| Upgrade + frequency change | Immediate | New full cycle charge minus old plan credit |
| Downgrade + frequency change | Immediate | Large credit, may cover several future invoices |

# Understanding Your KPI Dashboard

**Who this is for:** Activity managers and business owners using Minipass who want to know what each number on the dashboard actually means.

---

## What is a KPI?

KPI stands for **Key Performance Indicator** — a number that tells you at a glance how a specific part of your business is performing right now and whether things are trending up or down.

The Minipass dashboard shows 4 KPI cards at the top. You can read them in under 10 seconds and immediately know the health of your activity.

---

## How to Read a KPI Card

Each card has three parts:

```
┌─────────────────────────────┐
│  Revenue              +12%  │  ← % badge (trend vs previous period)
│  $1,240.00                  │  ← big number (the main value)
│  ▁▂▃▄▅▆▇█                  │  ← sparkline chart (daily activity)
└─────────────────────────────┘
```

**The big number** — The main metric for the selected time period (or a live snapshot for counts like Active Passes).

**The % badge** — How this period compares to the previous period of the same length. Green = up, red = down.
- Example: "Last 7 days" selected → the badge shows how this week compares to last week.
- If there's no previous data to compare against, the badge shows `—` (no change).

**The sparkline chart** — A small bar chart showing daily activity over the selected period. It lets you spot patterns (a spike on weekends, a slow mid-week, etc.) without digging into a full report.

---

## How the Time Period Works

The dropdown at the top of the dashboard lets you choose a time window. This affects the big numbers, % badges, and sparkline charts.

| Selection | What it covers | What it compares against |
|-----------|----------------|--------------------------|
| Last 7 days | The past 7 days | The 7 days before that |
| Last 30 days | The past 30 days | The 30 days before that |
| Last 90 days | The past 90 days | The 90 days before that |
| Fiscal Year | Jan 1 to today | The same span last year |
| All time | Every day since you started | No comparison (badge shows `—`) |

**Important:** Two of the four KPIs (Active Passes and Unpaid) always show a live count regardless of the period you select. The period still affects the % badge and chart for those cards — see details below.

---

## KPI 1: Revenue

**The big number:** Total cash collected during the selected period. This is the sum of all payments recorded in Minipass within that time window.

**The % badge:** How this period's revenue compares to the previous period of the same length.
- Example: You collected $1,200 this week and $1,000 last week → badge shows **+20%**.
- If you switch to "Last 30 days", it compares this month's revenue to last month's.

**The sparkline chart:** Daily revenue — you can see which days had payments and how much.

**"All time" note:** When you select "All time", the % badge disappears (there's nothing to compare against). The big number shows your total revenue since you started.

---

## KPI 2: Active Passes

**The big number:** The number of passes that still have uses remaining right now. Think of it as your "inventory in the wild" — passes that customers are holding and haven't used up yet.

This is a **live snapshot** — it always reflects the current state, not a count from the selected period. Switching from "Last 7 days" to "Last 30 days" won't change this number.

**The % badge:** Growth in new passes created this period vs the previous period. Because Minipass doesn't store historical snapshots of active pass counts, the % badge uses new pass creation as the best available signal for growth. A positive % means you issued more passes this period than the prior one.

**The sparkline chart:** Daily new passes created during the selected period. A tall bar on a given day means you issued a lot of passes that day.

**What "active" means:** A pass is active if it has at least one use remaining. A 10-punch coffee card with 3 punches left is active. The same card with 0 punches left is not.

---

## KPI 3: Redeemed

**The big number:** The number of times a pass was scanned (redeemed) during the selected period. Each scan of a QR code counts as one redemption.

**The % badge:** How this period's redemptions compare to the previous period of the same length. A positive % means customers used their passes more this period than last.

**The sparkline chart:** Daily redemptions — useful for spotting your busiest days and slow periods.

**What a redemption is:** When a customer presents their digital pass and you scan the QR code, that's a redemption. Redemptions are how Minipass tracks attendance and usage.

---

## KPI 4: Unpaid

**The big number:** The number of passes that have been issued but not yet paid for right now. These are passes in customers' hands where payment hasn't been recorded in Minipass.

Like Active Passes, this is a **live snapshot** — it always reflects current unpaid passes, not a count from the selected period.

**The % badge:** Growth in new unpaid passes created this period vs the previous period. A rising % means you're issuing more passes without payment — a signal to follow up on outstanding balances.

**The sparkline chart:** Daily new unpaid passes issued during the selected period.

**What "unpaid" means:** When you create a pass and payment has not yet been recorded (e.g., you're waiting for an e-transfer to arrive, or the customer will pay at the door), that pass is unpaid. Once you mark it as paid in Minipass, it leaves this count.

---

## Quick Reference

| KPI | Big Number | % Badge | Sparkline |
|-----|-----------|---------|-----------|
| **Revenue** | Cash collected this period | vs prior period revenue | Daily revenue |
| **Active Passes** | Live count: passes with uses left | New passes created this period vs prior | Daily new passes created |
| **Redeemed** | Scans this period | vs prior period scans | Daily scans |
| **Unpaid** | Live count: unpaid passes right now | New unpaid passes this period vs prior | Daily new unpaid passes |

**Rule of thumb:** Revenue and Redeemed change with the time period. Active Passes and Unpaid are always live counts — the period only affects the % and chart.

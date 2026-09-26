# Fix: missing `PaymentProcessed`/`ManualProcessed` IMAP folders for new customers
### (MinipassWebSite deployer fix — separate from the MiniPass application fix)

## Context

A second, unrelated bug found while investigating the FBI customer account: the
"PaymentProcessed" folder that matched payment emails are supposed to be moved into doesn't
exist for FBI (or for `kdc`), so every matched payment email silently fails to move and gets
deleted from INBOX instead (`mail.uid("COPY", ...)` doesn't raise on a `NO` response for a
nonexistent mailbox, so the failure is swallowed, then the unconditional
`STORE +FLAGS (\Deleted)` right after it deletes the source email anyway).

Root cause, confirmed by tracing the deploy flow and diffing `utils.py` across customers:

- **The deployer never creates IMAP subfolders at all**, for any customer, automatically or
  manually. `MinipassWebSite/utils/mail_integration.py`, `setup_customer_email_complete()`
  (called from `MinipassWebSite/app.py`, `process_deployment_async` and the Stripe `/webhook`
  handler) only creates the mailbox *account* (`addmailuser` via `docker exec mailserver`) and
  sets up sieve forwarding. No `mailbox create` / IMAP `CREATE` anywhere in `MinipassWebSite/`.
- Folders have only ever existed because of a **side effect** inside the per-customer
  MiniPass application's own bot code: the original/legacy matching branch in
  `match_gmail_payments_to_passes()` (`app/utils.py`) checks `mail.list()` and calls
  `mail.create(processed_folder)` if missing, before its `COPY`. That's the only reason older
  customers like heq/lhgi ended up with `PaymentProcessed` — their first real payment match,
  years ago, happened to go through that branch and auto-created it.
- PR #51 (2026-09-09, "Shop cart/checkout") added a newer matching branch in the application
  that also lacks this folder-existence check — **that half of the bug is tracked in the
  separate MiniPass application fix document, not here.** This document only covers the
  deployer-side gap: folders should exist *before* the application's bot ever runs, so it
  never depends on any matching branch's behavior to provision them.
- **Net effect today:** every customer deployed from now on starts with zero IMAP folders,
  because the deployer (`MinipassWebSite`) never provisions them at account-creation time.

**Goal:** every newly deployed customer mailbox should have `PaymentProcessed` and
`ManualProcessed` folders created automatically as part of the deploy flow, before the
customer's application ever processes its first payment — so folder existence is never an
accident of which code path happens to run first.

## Fix approach

In `MinipassWebSite/utils/mail_integration.py`, `setup_customer_email_complete()`, right after
`create_user_programmatic()` succeeds (mailbox account confirmed created/synced), add an
explicit step that creates the standard folders on the new mailbox via:

```
docker exec mailserver doveadm mailbox create -u <email> "PaymentProcessed"
docker exec mailserver doveadm mailbox create -u <email> "ManualProcessed"
```

Make this idempotent so it's safe on redeploys (mailbox/folders may already exist): either
check `doveadm mailbox list -u <email>` first and only create what's missing, or simply ignore
a "mailbox already exists" error from `doveadm mailbox create`.

This makes folder provisioning a guaranteed part of the automatic deploy flow
(`process_deployment_async` / the Stripe `/webhook` handler) instead of an accidental
side effect of application-side bot code — which is owned by a different codebase/document.

## Files to change

- `MinipassWebSite/utils/mail_integration.py` — `setup_customer_email_complete()`: add the
  folder-provisioning step described above.
- No schema/migration changes needed. No changes to the MiniPass application (`app/`) in this
  document.

## Test validation (on local dev)

1. **Reproduce first**: run the current (unfixed) deploy flow against a brand-new test
   mailbox, confirm via `doveadm mailbox list -u <email>` that only the default folders
   (INBOX, Sent, Drafts, Trash, Junk) exist and `PaymentProcessed`/`ManualProcessed` are
   absent — matches the production symptom for FBI/kdc.
2. **Apply the fix**, re-run the deploy flow against a fresh test mailbox, confirm
   `PaymentProcessed` and `ManualProcessed` now exist immediately after deployment completes,
   before any payment has ever been received or matched.
3. **Redeploy/idempotency check**: run the deploy flow a second time against a mailbox that
   already has these folders (simulating a redeploy of an existing customer); confirm it
   doesn't error and doesn't fail the overall deployment.
4. **End-to-end check**: with a freshly provisioned mailbox, send a test payment email and
   confirm the MiniPass application's bot can now successfully move it into `PaymentProcessed`
   on the very first match (this is the point where this fix and the separate application-side
   fix meet — either one alone closes the immediate symptom, but both together are the intended
   end state).

## Rollout

- Fix the `MinipassWebSite` deployer so all *future* customer deployments provision folders
  automatically at signup/deploy time.
- This does not retroactively fix already-deployed customers (FBI, kdc) — for those, either
  run the same `doveadm mailbox create` commands manually once, or rely on the separate
  application-side fix (if/when deployed to them) to create the folder on first successful
  match.
- As with the application-side fix, actual deployment of this change to the live
  `MinipassWebSite` service happens only after local validation succeeds — a separate,
  explicit step, not part of this document.

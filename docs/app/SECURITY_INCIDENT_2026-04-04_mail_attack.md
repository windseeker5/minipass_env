# Security Incident Report — Mail Server Phishing Attack
**Date of incident:** 2026-04-03 to 2026-04-04  
**Date of discovery:** 2026-04-04  
**Date of containment:** 2026-04-04  
**Severity:** Critical  
**Status:** Contained

---

## Executive Summary

The `lhgi@minipass.me` email account was compromised and used to send mass phishing emails impersonating the French government's traffic fine agency (ANTAI — *Agence nationale de traitement automatisé des infractions*). Attackers sent emails with subject lines like *"Paiement requis : votre amende – Réf. 872258"* to hundreds of French addresses (free.fr, orange.fr, laposte.net, airfrance.fr, etc.).

The attack lasted less than 24 hours — from the evening of April 3 to the morning of April 4. The root cause was a plaintext SMTP password committed to a public GitHub repository on February 17, 2026. The attacker connected from an **external IP (`74.249.83.141`) registered to Microsoft Corporation (Azure cloud)**, authenticated via SMTP port 587, and sent 812+ phishing emails before being stopped.

---

## Timeline

| Date/Time (UTC) | Event |
|-----------------|-------|
| 2026-02-17 | `pytest/check_interac_headers.py` committed to `windseeker5/dpm` (public repo) with hardcoded SMTP credentials (`lhgi@minipass.me` / `monsterinc00`) |
| 2026-04-03 — all day | LHGI hockey game — `jf@jfgoulet.com` uses the app normally, all legitimate emails succeed with zero failures |
| **2026-04-03 20:21 UTC (4:21 PM EDT)** | **First attack connection** from `74.249.83.141` (Microsoft Azure, Virginia, US). Attacker authenticates with stolen credentials and sends a small quiet test batch to Gmail and Hotmail addresses — these deliver silently, no failures reported |
| 2026-04-03 20:22 UTC | Attacker disconnects after first batch |
| **2026-04-04 11:56 UTC (7:56 AM EDT)** | **Second wave begins** — attacker reconnects and sends 800+ emails targeting French addresses (free.fr, orange.fr, laposte.net, airfrance.fr). free.fr blocks the IP and returns 421 errors → mass queue buildup |
| 2026-04-04 12:35 UTC | Postfix queue reaches 493 deferred messages, generating thousands of retry log entries |
| 2026-04-04 ~16:00 UTC | Mail dashboard anomaly discovered (3,314 failures visible, 493 messages in queue) |
| 2026-04-04 16:16 UTC | All 493 queued phishing messages deleted (`postsuper -d ALL`) |
| 2026-04-04 16:20 UTC | SMTP password rotated for `lhgi@minipass.me`, lhgi app database updated |
| 2026-04-04 16:xx UTC | Credentials removed from git tracking, security PR created and merged |

---

## Root Cause Analysis

### How the credentials were exposed

On February 17, 2026, a test/debug script was committed to the `windseeker5/dpm` GitHub repository:

**File:** `pytest/check_interac_headers.py`  
**Commit:** `0f390f0` — *"Adding pytest folder in order to debug on my VPS and container"*

The file contained:
```python
MAIL_SERVER = "mail.minipass.me"
MAIL_USERNAME = "lhgi@minipass.me"
MAIL_PASSWORD = "monsterinc00"   # ← exposed to the public internet
```

This file was in `.gitignore` (the `pytest/` directory is gitignored) but was force-added to git tracking in a previous commit, bypassing the gitignore protection. The credentials sat exposed in the public repo for **45 days** before being exploited.

### How the attack worked

1. Attacker (or automated scanner) found the credentials in the public GitHub repo
2. Attacker rented a **Microsoft Azure cloud VM** (IP `74.249.83.141`, Boydton, Virginia, US) — a trusted cloud provider, harder to block by IP reputation alone
3. Attacker connected to `mail.minipass.me:587` from that external Azure IP using SASL authentication with the stolen credentials
4. Postfix accepted the connection — SASL auth succeeded with the valid password
5. **Phase 1 (April 3, 20:21 UTC):** Small test batch of 2 emails to Gmail/Hotmail to verify the credentials work — delivered successfully, no alarms triggered
6. **Phase 2 (April 4, 11:56 UTC):** Mass campaign of 812+ emails to French addresses — free.fr blocked the IP, causing 493 messages to pile up in the deferred queue and generating 3,314+ failure log entries
7. All emails were DKIM-signed with the `minipass.me` domain key, making them appear legitimate to mail filters

### Why DKIM didn't protect us

The emails received a valid DKIM signature (`d=minipass.me, s=mail`) because the attacker sent through our own mail server with valid credentials. DKIM proves the email came from our infrastructure — it does not prevent abuse of authenticated accounts.

### Why the Phase 2 emails failed and filled the queue

When the attacker sent 812 emails in Phase 2, the delivery process works like this:

1. The attacker's script connects to our server and submits all 812 emails rapidly via SMTP. Our server **accepts them all immediately** — this is normal behaviour. The SMTP "accepted" response only means our server received the message, not that it was delivered to the recipient.

2. Our Postfix server then tries to deliver each email to the recipient's mail server (free.fr, orange.fr, laposte.net, etc.) over port 25. At this point, the receiving server looks up our IP reputation and decides whether to accept.

3. **free.fr blocked us.** Their mail server responded with:
   ```
   421 Your IP (138.199.152.128) is temporary blacklisted by an anti-trojan rule
   ```
   A `421` response means "temporarily rejected, try again later." Postfix treats this as a **temporary failure** and moves the message to the **deferred queue** — it will keep retrying automatically every few minutes for up to 5 days.

4. With 493 messages deferred and Postfix retrying every few minutes, the mail log filled up rapidly — each retry attempt counts as a "failure" in the dashboard. That is why the dashboard showed **3,314 failures** from only 493 messages: each message was retried ~6-7 times before we intervened.

5. The reason free.fr blacklisted us so quickly: the attacker sent hundreds of emails to free.fr addresses in a very short burst. Free.fr's anti-spam system detects this volume pattern as a "trojan" (automated bulk sending) and blocks the sending IP. This is actually what **saved us from wider damage** — the French providers' rate limiting turned what could have been 800+ delivered phishing emails into 493 queued ones we could delete.

**Why Gmail and Hotmail were not blocked (Phase 1):** The test batch of 2 emails was small enough to fly under any rate-limiting threshold, and Gmail/Hotmail have higher tolerance for new senders.

---

### Correction of initial analysis

An earlier analysis incorrectly identified the attack as starting on March 22, 2026, and attributed it to internal Docker IP `172.18.0.1`. This was wrong. The March 22 and March 29 log entries showing `from=<lhgi@minipass.me>` were **legitimate lhgi application emails** sent during hockey game sessions (e.g., to `belangerjean@ymail.com`, `willi12347@live.ca`). The actual attacker IP is `74.249.83.141` (external, Microsoft Azure), and the attack window was entirely within April 3–4, 2026.

---

## Impact Assessment

### Emails sent by attacker
- **Total authenticated SMTP sessions by attacker:** 812 (`sasl_username=lhgi@minipass.me` from `74.249.83.141`)
- **Successfully passed through Amavis/queued:** 812
- **Delivered (Phase 1 test batch):** 2 confirmed delivered (`alixephilp@gmail.com`, `moranicolass@hotmail.com`)
- **Deferred/failed (Phase 2 mass campaign):** 493 in queue at time of discovery, all deleted
- **Failure log entries (retries):** 3,314+ visible in mail dashboard

### Targets
- Phase 1: Gmail and Hotmail (test batch — delivered silently)
- Phase 2: French addresses — free.fr, orange.fr, laposte.net, airfrance.fr

### Reputation damage
- **IP `138.199.152.128` blacklisted** by free.fr (anti-trojan rule, temporary — delisting request needed)
- The `lhgi` customer's brand was used as the sender identity in a phishing campaign

### Data exposure
- The `lhgi@minipass.me` SMTP password was exposed publicly for ~45 days (Feb 17 → Apr 4)
- No other credentials were found in the same file
- No evidence of access to application databases or customer data
- The attacker only exploited the SMTP account — no server intrusion detected

---

## Containment Actions Taken

1. **Mail queue flushed** — `postsuper -d ALL` deleted all 493 queued phishing messages
2. **SMTP password rotated** — New password set via `setup email update` on the mailserver container
3. **lhgi app database updated** — `MAIL_PASSWORD` setting updated in SQLite (`/app/instance/minipass.db`, key `MAIL_PASSWORD`)
4. **`lhgi-nm.conf` updated** — neomutt config updated with new password
5. **Credentials removed from git** — `pytest/` directory removed from git tracking, security PR `#11` created and merged to `windseeker5/dpm`
6. **Local file fixed** — `check_interac_headers.py` updated to load credentials from environment variables
7. **205 bounce emails deleted** — All "Undelivered Mail Returned to Sender" messages purged from `lhgi@minipass.me` inbox via `doveadm expunge`
8. **fail2ban unban** — VPS IP `138.199.152.128` was caught in collateral fail2ban bans during the incident; manually unbanned from dovecot jail
9. **free.fr blacklist** — IP ban is temporary (max 24h, auto-lifts). No action required — confirmed by free.fr postmaster page. Will resolve automatically as long as no further spam is sent.

---

## Remaining To-Do

- [ ] **Notify lhgi customer** (`jf@jfgoulet.com`) — their app's email identity was used in a phishing campaign
- [ ] **Purge git history** — The old password is still in commit `0f390f0` in git history. Password is rotated so not an emergency, but clean it with `git filter-repo` when convenient
- [ ] **Enable GitHub Push Protection** on `windseeker5/dpm` — see section below

---

## How Attackers Find Credentials in GitHub (Education)

### Your repo's popularity does not matter

This is the most important thing to understand. Attackers do not browse GitHub looking for interesting repos. They run **fully automated bots, 24/7**, that scan every single public commit on GitHub regardless of how obscure the repo is. Your 0-star repo gets the same treatment as a 50,000-star repo.

### The attack vectors

**1. GitHub's real-time Events API (firehose)**
GitHub publishes a public stream of every event happening across all public repos — every push, every commit, every new file — in real time. Attackers subscribe to this stream and scan every commit as it arrives. Your commit `0f390f0` on February 17 was almost certainly scanned **within minutes**.

**2. GitHub code search**
GitHub's search engine indexes all public code. A query like `"MAIL_PASSWORD" "minipass.me"` returns your file instantly, from any browser, no account needed. Attackers run thousands of such queries automatically via the GitHub Search API.

**3. Dedicated secret scanning tools**
Open-source tools like **GitLeaks**, **TruffleHog**, and **Gitleaks** are designed to scan repos for secrets. Security researchers use them defensively — but attackers use the exact same tools offensively. They run them in bulk against GitHub's full public repo index.

**4. Commercial breach databases**
Services like **GitGuardian** maintain a continuously updated database of every leaked credential ever found in any public repo. The same data is available to malicious actors. Your credential was likely in such a database within 24 hours of the commit — it just took 45 days for someone to act on it.

### The timeline of a typical credential leak

```
Hour 0    — You push a commit with a hardcoded password
Hour 0-1  — Automated bots index the commit and extract the credential
Day 1-7   — Credential appears in breach databases
Day 1-180 — Someone (human or bot) uses the credential
```

The 45 days between your commit and the attack is actually longer than average. Some credentials are exploited within hours.

---

## How to Prevent This in the Future

### Layer 1 — GitHub Push Protection (your first line of defense)

GitHub has a built-in feature called **Push Protection** that **blocks a push before it reaches the repo** if it detects a known secret pattern (API keys, passwords, tokens, etc.). It is **free for public repos**.

**How to enable it:**
1. Go to `https://github.com/windseeker5/dpm/settings/security_analysis`
2. Enable **"Secret scanning"**
3. Enable **"Push protection"** (sub-option under secret scanning)

Once enabled, if you try to push a file containing a credential, GitHub will **reject the push** and show you exactly which file and line contains the secret. You can bypass it if you explicitly confirm it's a false positive, but it forces you to be deliberate.

**Important limitation:** GitHub's secret scanning recognizes known patterns — AWS keys, Stripe keys, GitHub tokens, etc. A custom password like `monsterinc00` in a variable called `MAIL_PASSWORD` may or may not be caught depending on the pattern. It is not a guarantee.

### Layer 2 — Pre-commit hook with detect-secrets (your local safety net)

A pre-commit hook runs on your machine **before the commit is created** — before git even records it. This catches things that GitHub push protection might miss.

Install `detect-secrets` and set it up once:

```bash
pip install detect-secrets
# In your repo root, create a baseline of known/acceptable secrets
detect-secrets scan > .secrets.baseline
# Add the pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/sh
detect-secrets-hook --baseline .secrets.baseline
EOF
chmod +x .git/hooks/pre-commit
```

After this, any commit containing a new secret-like string will be **blocked locally** with a clear error message before it ever touches GitHub.

### Layer 3 — Fix your .gitignore discipline (the root cause here)

The `pytest/` directory was already in `.gitignore`. The problem was using `git add -f` (force) to bypass it. Two rules:

1. **Never use `git add -f` on a gitignored file** — if it is ignored, it is ignored for a reason
2. **Never put debug/test scripts with credentials in a tracked directory** — use a separate folder that is gitignored, or use environment variables from the start

### Layer 4 — Use environment variables, always

The correct pattern for any credential in any script:

```python
# WRONG — never do this
MAIL_PASSWORD = "monsterinc00"

# RIGHT — always do this
import os
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
if not MAIL_PASSWORD:
    raise ValueError("MAIL_PASSWORD environment variable not set")
```

For local testing, use a `.env` file (which must be in `.gitignore`) and load it with `python-dotenv`.

### Summary — defense in depth

| Layer | Tool | Where it stops the leak |
|-------|------|------------------------|
| 1 | GitHub Push Protection | At the remote — rejects the push |
| 2 | detect-secrets pre-commit hook | Locally — before the commit exists |
| 3 | .gitignore discipline | Process — never force-add ignored files |
| 4 | Environment variables | Code — no credential in source ever |

All four layers together make it extremely unlikely a credential ever reaches a public repo. Any single layer alone is insufficient.

---

## Lessons Learned

1. **Never hardcode credentials in test scripts**, even temporarily — use environment variables
2. **Never force-add files that are gitignored** — if a file is in `.gitignore`, it's there for a reason
3. **Public repos are indexed by automated secret scanners** within hours of a commit — treat any committed credential as immediately compromised
4. **The attacker used a legitimate cloud provider (Azure)** — IP reputation blocking alone would not have stopped this
5. **A small silent test batch preceded the main attack** — the 2 emails on April 3 evening went completely undetected; only the mass campaign triggered alerts
6. **The mail dashboard saved us** — the failure spike on April 4 was immediately visible and triggered discovery within hours
7. **Two crises, two root causes** — February 2026 was RFC 5322 non-compliance (technical). April 2026 was a credential leak (human error). Both were preventable with better process.

---

## Solo Dev Security Checklist — What To Do Going Forward

You are one person managing a production mail server, multiple customer containers, two codebases, and a public GitHub repo. This section gives you a realistic, prioritized set of measures — not a corporate security policy, but what actually makes sense for your setup.

---

### 1. Credential scanning script (already built)

A scanner has been created at `tools/scan_credentials.py`. Run it:

```bash
# Scan the entire minipass environment
python3 ~/minipass_env/tools/scan_credentials.py

# Run it before any git push — make it a habit
```

When you ran it after this incident, it already found:
- `monsterinc00` still present in the local copy of `check_interac_headers.py` (gitignored but on disk)
- A password in `scripts/fetch_dmarc_reports.py` — **review this**
- The neomutt `.conf` files (these are admin tools on the VPS itself, not in git — acceptable)
- False positives in Tabler JS library files (ignore those)

**Run this weekly, or at minimum before any `git push` to a public repo.**

---

### 2. GitHub Push Protection — enable it now (5 minutes, free)

Go to: `https://github.com/windseeker5/dpm/settings/security_analysis`

Enable:
- ✅ **Secret scanning** — alerts you after the fact if a secret is found
- ✅ **Push protection** — blocks the push before it reaches GitHub

This is your most important safety net for the git repo. It's free for public repos and requires zero maintenance.

**Limitation:** It catches known patterns (Stripe keys, AWS keys, GitHub tokens). A custom password in a variable called `MAIL_PASSWORD` may slip through — which is why the local scanner above is also needed.

---

### 3. Pre-commit hook — one-time setup per repo

Install once, protects forever:

```bash
pip install detect-secrets

# Run once in each repo root to create a baseline
cd ~/minipass_env/app
detect-secrets scan > .secrets.baseline

cd ~/minipass_env/MinipassWebSite
detect-secrets scan > .secrets.baseline

# Add the hook to each repo
echo '#!/bin/sh
detect-secrets-hook --baseline .secrets.baseline' > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

After this, any commit with a new secret-like string is **blocked before it is recorded** with a clear error showing the file and line.

---

### 4. Postfix rate limiting — limit the blast radius

Even if credentials are stolen again, rate limiting on port 587 would have capped the damage to a handful of emails instead of 812. Add to your `docker-mailserver` config:

```
# In config/postfix-main.cf (or via docker-mailserver env vars):
# Limit authenticated users to 100 emails per hour
smtpd_client_message_rate_limit = 100
smtpd_client_auth_rate_limit = 10
anvil_rate_time_unit = 3600s
```

This means even a compromised account can only send 100 emails/hour — not 812 in 10 minutes.

---

### 5. Port 587 restriction — close the external door

All your legitimate email sending happens from inside the Docker network. There is no business reason for port 587 to be accessible from the public internet. Consider restricting it to internal Docker network only:

```yaml
# In docker-compose.yml, change the mailserver port mapping:
# FROM (currently — exposed to internet):
ports:
  - "587:587"
# TO (internal only — not accessible from internet):
ports:
  - "127.0.0.1:587:587"
```

If you ever need to send from outside (e.g., local dev machine), use an SSH tunnel instead.

---

### 6. What you already have that works well

- ✅ **fail2ban** — catches brute force attempts. Did not help here because the attacker had valid credentials, but still valuable for password guessing attacks.
- ✅ **Secure password generation** — new customer containers get randomly generated mail passwords. This is the right approach.
- ✅ **Mail dashboard** — this is what caught the attack. Keep checking it daily.
- ✅ **Separate mail accounts per customer** — the compromise was isolated to `lhgi@minipass.me`. Other accounts (kdc, heq, testdelancementmf) were not affected.

---

### 7. Priority order for a solo dev

| Priority | Action | Effort | Impact |
|----------|--------|--------|--------|
| 🔴 Now | Enable GitHub Push Protection | 5 min | High |
| 🔴 Now | Review `scripts/fetch_dmarc_reports.py` for hardcoded creds | 5 min | High |
| 🟠 This week | Add pre-commit hook to both repos | 15 min | High |
| 🟠 This week | Add Postfix rate limiting | 30 min | High |
| 🟡 This month | Restrict port 587 to internal only | 1 hour | Medium |
| 🟡 This month | Purge git history of old password | 30 min | Low (already rotated) |
| 🟢 Ongoing | Run `scan_credentials.py` before every push | 0 extra time | High |

---

## References

- **Attacker IP:** `74.249.83.141` — Microsoft Azure, Boydton, Virginia, US (ASN 8075)
- **Abuse contact:** `abuse@microsoft.com`, +1-425-882-8080
- Phishing email sample: `From: "Antai.gouv.fr" <lhgi@minipass.me>`, `Subject: Paiement requis : votre amende – Réf. 872258`
- Compromised commit: `0f390f0abe35899938b18af702ebd3076d387396`
- Security fix PR: `#11` on `windseeker5/dpm`
- Postfix logs: `/var/log/mail/mail.log` (inside mailserver container)
- Our mail server IP: `138.199.152.128`

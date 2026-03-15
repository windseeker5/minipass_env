# CI/CD & Workflow Best Practices for Minipass
*Education document — no code changes, just knowledge*

---

## Context

You are a solo developer running a SaaS (Minipass) on a VPS with a multi-tenant Docker setup.

**Current workflow:** fix/commit directly to `main` → SSH to VPS → run `upgrade_customers.py` TUI manually.

**Priority:** Less friction (fewer manual steps), not safety-first. 1-5 customers deployed.

---

## 1. Branching Strategy — Why You're Risking Production Every Day

**Current risk:** Pushing broken code to `main` means customers get it immediately. If you push at 11pm with a half-tested change and go to bed, your customers hit broken code overnight.

**The fix:**

```
main          ─────────●─────────────●──────────●──▶  (always deployable)
                       ↑             ↑          ↑
feature/stripe-fix  ──●──●──●──●────┘          │
feature/qr-rework          ──●──●──●──●──●─────┘
```

Every change lives on its own branch. `main` only gets code you've decided is ready. You can have five half-finished features in flight and `main` stays clean.

**Solo dev workflow:**
```bash
# Start any change
git checkout -b fix/payment-parsing

# Work, commit, test locally
git add -p
git commit -m "fix: handle empty etransfer subject line"

# Push the branch to GitHub
git push origin fix/payment-parsing
```

Then on GitHub:
1. You'll see a **"Compare & pull request"** banner — click it
2. Click the **"Files changed"** tab — this is your code review moment, read the diff
3. Go back to **Conversation** tab → click **"Merge pull request"** → **"Confirm merge"**
4. Click **"Delete branch"** (GitHub deletes the remote branch for you)

Then back in your terminal:
```bash
# Sync your local main with the merged commit
git checkout main
git pull
# No need for git branch -d — the remote is gone, pull cleans it up
```

**Time cost:** 20 seconds per feature.
**Payoff:** `main` is always the thing you'd be comfortable deploying to customers.

### Complete workflow at a glance

| Step | Where | Command / Action |
|---|---|---|
| Start work | Terminal | `git checkout -b fix/whatever` |
| Make changes | Editor | — |
| Stage & commit | Terminal | `git add -p` then `git commit -m "..."` |
| Push branch | Terminal | `git push origin fix/whatever` |
| Open PR | GitHub | Click "Compare & pull request" banner |
| Review your diff | GitHub | Click "Files changed" tab |
| Merge | GitHub | "Merge pull request" → "Confirm merge" |
| Delete remote branch | GitHub | Click "Delete branch" button |
| Sync local main | Terminal | `git checkout main && git pull` |

### What those flags mean

| Command | Flag | What it does |
|---|---|---|
| `git checkout -b fix/whatever` | `-b` | **Create + switch** in one step. Without `-b` you'd need two commands: `git branch fix/whatever` then `git checkout fix/whatever` |
| `git add -p` | `-p` | **Patch mode** — shows each changed chunk one at a time and asks: stage it? (y/n). Lets you make 10 changes but only commit 3 of them. Great for keeping commits focused. |
| `git branch -d fix/whatever` | `-d` | **Safe delete** — deletes the branch only if it's already been merged. Use `-D` (capital) to force-delete an unmerged branch. |

### What to do if you accidentally commit directly to main (it will happen)

GitHub will reject your `git push` with "Changes must be made through a pull request."
Your commit exists locally but not on GitHub. Fix it like this:

```bash
# 1. Create a branch pointing to your commit (while still on main)
git branch fix/whatever-you-named-it

# 2. Reset local main back to match GitHub
git reset --hard origin/main

# 3. Switch to your branch
git checkout fix/whatever-you-named-it

# 4. Push the branch
git push origin fix/whatever-you-named-it
```

Then go to GitHub — you'll see a "Compare & pull request" banner — open the PR and merge it normally.

---

## 2. Pull Requests — Not Just for Teams

**The solo dev case for PRs:** When you're writing code you're in "author mode" — you see what you *meant* to write. Opening a PR and reading the diff puts you in "reviewer mode" — you see what you *actually* wrote. These are different mental states and you catch different bugs.

**GitHub's diff view catches:**
- `if x = y:` instead of `if x == y:`
- A debug `print()` statement you forgot to remove
- A route you accidentally left open
- A 400-line function you meant to break up

### Branch Protection on `main` (via Rulesets)

GitHub now uses **Rulesets** instead of the classic "Add rule" interface.

Go to: GitHub → your repo → Settings → Branches → New ruleset → New branch ruleset

1. **Ruleset Name:** `Protect main`
2. **Enforcement status:** `Active`
3. **Target branches:** Add target → Include by pattern → `main`
4. **Rules — enable these:**
   - ✅ Restrict deletions (prevents accidental deletion of `main`)
   - ✅ Require a pull request before merging
     - Set **Required approving reviews: 0** (solo dev — you just need the PR step)
     - Uncheck "Require review from code owners"
   - ✅ Block force pushes
   - ⬜ Require status checks to pass — skip for now, add in Week 2 once CI is set up
5. Click **Create**

Now `git push origin main` is rejected. You *must* go through a PR. This becomes muscle memory in a week.

**Time cost:** ~30 seconds to open a PR, 2 minutes to review your own diff.
**Payoff:** Catches bugs before they hit customers.

---

## 3. GitHub Actions CI — Automated Safety Net

You already have this test: `python -m unittest test.test_kpi_data -v`

**Add this file to your repo:**

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: ["*"]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: app

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: python -m unittest test.test_kpi_data -v
```

**What this does:**
- Every push to any branch → GitHub spins up a fresh Ubuntu VM → installs your deps → runs your tests
- Tests fail → red ✗ on the PR → cannot merge (if branch protection requires status checks)
- Tests pass → green ✓ → safe to merge

**The feedback loop:**
```
push to branch → 60-90 seconds → "Tests passed" or "Tests failed"
                                  (before it ever touches your VPS)
```

**Cost:** Free. GitHub Actions gives you 2,000 minutes/month on private repos. Each test run is ~2 minutes. That's 1,000 pushes/month free.

**Expand over time:** Add `flake8` linting, `bandit` security scanning, or DB migration smoke tests. Start with what you have.

---

## 4. Automated Deployment — Eliminating the SSH Dance

**Your current deploy process:**
1. Open terminal
2. SSH to VPS
3. Navigate to directory
4. `git pull`
5. Run `upgrade_customers.py` TUI
6. Select customers
7. Watch it run
8. Exit SSH

Steps 1-4 are pure friction. Steps 5-7 are *valuable control* — you're deciding which customers get the upgrade and in what order. Don't automate those away.

**Recommendation: automate steps 1-4, keep steps 5-7.**

### Option A: GitHub Actions SSH Deploy (recommended — easiest)

Add a second workflow that fires on push to `main`:

```yaml
# .github/workflows/deploy.yml
name: Deploy to VPS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Pull latest code on VPS
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            cd /home/kdresdell/Documents/DEV/minipass_env
            git pull origin main
            echo "Code pulled. Run upgrade_customers.py when ready."
```

Store `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY` as GitHub Secrets (encrypted, never in your repo):
- GitHub → repo → Settings → Secrets and variables → Actions → New repository secret

**Result:** Merge a PR → GitHub automatically SSHes to your VPS → pulls latest code → you SSH in *only* when you're ready to run the TUI and upgrade specific customers.

### Option B: Webhook Trigger (no GitHub Secrets needed)

Run a tiny listener on your VPS that receives a POST from GitHub on push:

```python
# deploy_hook.py — runs as a systemd service on VPS
from flask import Flask, request
import subprocess, hmac, hashlib

app = Flask(__name__)
SECRET = b"your-webhook-secret"

@app.route("/deploy", methods=["POST"])
def deploy():
    sig = request.headers.get("X-Hub-Signature-256", "")
    expected = "sha256=" + hmac.new(SECRET, request.data, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return "Forbidden", 403
    subprocess.Popen(["git", "-C", "/path/to/repo", "pull", "origin", "main"])
    return "Pulling", 200

if __name__ == "__main__":
    app.run(port=9000)
```

GitHub → repo → Settings → Webhooks → send to `https://yourVPS:9000/deploy` on push to `main`.

**Which to choose:** Option A is easier (no new service on VPS). Option B gives more control and avoids GitHub Secrets.

---

## 5. What to Keep vs. What to Change

| | Keep/Change | Reason |
|---|---|---|
| `upgrade_customers.py` TUI | ✅ Keep | Per-customer selection is exactly right for multi-tenant SaaS |
| Idempotent migration system | ✅ Keep | Already professional-grade |
| Backup-before-upgrade | ✅ Keep | Your safety net |
| healthchecks.io monitoring | ✅ Keep | Passive assurance |
| Direct push to `main` | ❌ Change | Replaced by feature branches + PRs |
| Manual SSH git pull | ❌ Change | Replaced by GitHub Action |
| No tests in CI | ❌ Change | Add the 20-line workflow file above |

---

## 6. Rollback — You Already Have It (Just Document It)

You have rollback built in. You just haven't formalized the procedure.

**The runbook:**

```bash
# On VPS — rollback to previous commit
cd /home/kdresdell/Documents/DEV/minipass_env
git log --oneline -10          # find the last known-good commit hash
git reset --hard <commit-hash>
docker-compose restart <service>

# Per-customer DB rollback
# Your backups are created by upgrade_customers.py before each upgrade
# Restore: cp backup/customerX.db app/instance/customerX.db
docker-compose restart customerX
```

**With git tags (even cleaner):**

```bash
# Before running upgrade_customers.py for customers, tag it
git tag v1.4.2
git push origin v1.4.2

# Rollback = checkout the previous tag
git checkout v1.4.1
```

Tags cost nothing and give you a named anchor for every production state. `git log --tags --oneline` shows you exactly what you shipped and when.

---

## 7. Environment Separation — Cheap Wins

**Current state:** localhost = dev, VPS = prod. Nothing in between.

**Minimum viable improvement — git tags as release markers** (described in section 6 above).

When a customer reports a bug, you know what version they're on. `git diff v1.4.1 v1.4.2` shows you exactly what changed between versions.

**Optional next level — use one customer container as staging:**

Pick your lowest-risk customer (or create a `demo` customer). Deploy to them first, verify, then deploy to everyone else via the TUI. You already have this capability — it's just a matter of habit.

---

## Recommended Adoption Order

Start here, in order. Each step is independent — stop whenever the friction-to-value ratio isn't worth it.

1. **Week 1:** Start using feature branches for every change. Just `git checkout -b fix/whatever` before you start coding. Zero tooling required.
2. **Week 2:** Add `.github/workflows/ci.yml`. Push it to `main` once. Now every future push runs your tests automatically.
3. **Week 3:** Turn on branch protection on `main`. Start doing PRs for your own merges.
4. **Week 4:** Add `.github/workflows/deploy.yml` with the SSH action. Eliminate the `git pull` step from your SSH dance.
5. **Ongoing:** Add git tags before each customer deployment wave.

---

## What NOT to Do

- **Complex GitFlow** (develop/release/hotfix branches) — overkill for a solo dev
- **Kubernetes / heavy orchestration** — unnecessary at your current scale
- **Full auto-deploy to all customers without review** — dangerous for multi-tenant SaaS
- **Expensive CI/CD platforms** — GitHub Actions free tier is sufficient

---

*Document created: 2026-03-12*
*For questions or implementation, start a new Claude Code session and reference this file.*

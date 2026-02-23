# Minipass Recovery Runbook

**Last Updated:** February 21, 2026
**Infrastructure:** Single VPS at minipass.me (138.199.152.128), SSH port 2222
**DNS registrar:** domain.com (manual update, ~5 min, propagates per TTL)

---

## Quick Reference

| Scenario | Expected Recovery | Script |
|----------|-------------------|--------|
| A — Container crash | 0–2 min (auto) | none |
| B — Data corruption (VPS alive) | 30–45 min | `restore.sh` |
| C — VPS completely gone | 45–90 min | `restore.sh` |
| D — DKIM key lost (no backup) | 60–90 min + DNS wait | manual |

**Before anything:** Check UptimeRobot alert details — it tells you which service is down and narrows the scenario.

---

## Scenario A — Container Crash (Auto-Recovered)

`restart: always` is configured on all containers. Docker restarts them automatically.

**If Docker did not auto-restart:**
```bash
ssh -p 2222 kdresdell@minipass.me
cd minipass_env
docker compose up -d
docker compose ps   # verify all containers are Up
```

**If a specific container is stuck in a crash loop:**
```bash
docker compose logs --tail=50 <service>   # e.g. mailserver, lhgi
# Fix the root cause (bad config, missing file, etc.)
docker compose restart <service>
```

**Time: 0–5 minutes.**

---

## Scenario B — VPS Running, Data Lost or Corrupted

Use this when the VPS SSH is accessible but data is wrong or containers won't start.

### Step 1: Identify what's broken
```bash
ssh -p 2222 kdresdell@minipass.me
cd minipass_env
docker compose ps
docker compose logs --tail=50 mailserver
docker compose logs --tail=50 lhgi
```

### Step 2: Push latest backup from home server to VPS
```bash
# Run on HOME system:
LATEST=$(ls ~/backups/minipass/ | grep '^20' | sort | tail -1)
echo "Restoring from: $LATEST"

rsync -avz -e "ssh -p 2222" \
  ~/backups/minipass/$LATEST/ \
  kdresdell@minipass.me:/home/kdresdell/minipass_env_restore/
```

### Step 3: Run restore script on VPS
```bash
ssh -p 2222 kdresdell@minipass.me
bash ~/minipass_env/scripts/restore.sh ~/minipass_env_restore
```

### Step 4: Verify
```bash
# On VPS:
docker compose ps
docker exec mailserver postqueue -p    # should be empty or normal queue
curl -I https://minipass.me            # should return 200
curl -I https://lhgi.minipass.me       # should return 200

# Send a test email:
echo "Test" | mail -s "Recovery test" admin@minipass.me
```

**Time: 30–45 minutes.**

---

## Scenario C — VPS Completely Gone (Nuclear Recovery)

Use when the VPS is unresponsive, provider has an outage, or the node is destroyed.

### Step 1: Get a new VPS (5 min)

Same provider (Vultr/Hetzner/DigitalOcean) or any Linux VPS with Docker support.

- Ubuntu 22.04 LTS, same specs (2 vCPU, 4GB RAM minimum)
- Note the new VPS IP address: `NEW_IP`
- Add your SSH public key during provisioning

### Step 2: Install Docker on new VPS (10 min)
```bash
ssh root@NEW_IP

# Install Docker
curl -fsSL https://get.docker.com | sh
usermod -aG docker kdresdell   # or whichever user you'll use

# Install docker-compose (if not included)
apt-get install -y docker-compose-plugin

# Create user if needed
useradd -m -s /bin/bash kdresdell
mkdir -p /home/kdresdell/.ssh
cat >> /home/kdresdell/.ssh/authorized_keys << 'EOF'
# paste your public key here
EOF
chmod 700 /home/kdresdell/.ssh
chmod 600 /home/kdresdell/.ssh/authorized_keys
chown -R kdresdell:kdresdell /home/kdresdell/.ssh
```

### Step 3: Clone the git repo (2 min)
```bash
ssh -p 22 kdresdell@NEW_IP   # new VPS uses port 22 initially
cd ~
git clone <your-repo-url> minipass_env
cd minipass_env
```

### Step 4: Push backup from home to new VPS (5–15 min)
```bash
# Run on HOME system:
LATEST=$(ls ~/backups/minipass/ | grep '^20' | sort | tail -1)
echo "Restoring from: $LATEST"

rsync -avz -e "ssh -p 22" \
  ~/backups/minipass/$LATEST/ \
  kdresdell@NEW_IP:/home/kdresdell/minipass_env_restore/
```

### Step 5: Run restore script on new VPS
```bash
ssh kdresdell@NEW_IP
bash ~/minipass_env/scripts/restore.sh ~/minipass_env_restore
```

### Step 6: Update DNS at domain.com (5 min)
1. Log in to domain.com admin panel
2. Go to DNS management for `minipass.me`
3. Update **A record**: `minipass.me` → `NEW_IP`
4. Update **A record**: `mail.minipass.me` → `NEW_IP`
5. Update **MX record** if it points to an IP (usually points to hostname, so may not need changing)
6. Save — DNS propagates based on TTL (set to 300s before maintenance, or wait up to 1 hour for 3600s TTL)

### Step 7: Wait for DNS + verify (5–30 min)
```bash
# Check DNS propagation:
dig +short minipass.me          # should return NEW_IP
dig +short mail.minipass.me     # should return NEW_IP

# Once propagated, verify:
curl -I https://minipass.me
curl -I https://lhgi.minipass.me
echo "Test" | mail -s "Recovery test" admin@minipass.me

# Check mail queue:
docker exec mailserver postqueue -p
```

**Time: 45–90 minutes total.**

---

## Scenario D — DKIM Key Loss (No Backup Available)

Use this only if `config/opendkim/` was NOT in your backup. This is why DKIM backup is the #1 priority in `backup_pull.sh`.

### Signs you need this section:
- Backup present but `mail_server/config/opendkim/` directory is empty or missing
- Mail is sending but DKIM signatures are failing (check `email_monitoring/monitoring.db`)

### Step 1: Regenerate DKIM key
```bash
ssh -p 2222 kdresdell@minipass.me
cd minipass_env

# Using docker-mailserver's setup script:
docker exec mailserver setup config dkim

# Or manually with opendkim-genkey:
mkdir -p config/opendkim/keys/minipass.me
opendkim-genkey -b 2048 -d minipass.me -D config/opendkim/keys/minipass.me/ -s mail -v
```

### Step 2: Get the new public key
```bash
cat config/opendkim/keys/minipass.me/mail.txt
# Output will look like:
# mail._domainkey IN TXT "v=DKIM1; k=rsa; p=MIIBIjANBgkqhkiG9w0B..."
```

### Step 3: Update DNS TXT record at domain.com
1. Log in to domain.com admin panel
2. DNS management for `minipass.me`
3. Update (or add) TXT record:
   - **Host:** `mail._domainkey`
   - **Value:** the full `"v=DKIM1; k=rsa; p=..."` string
4. Save — propagation takes ~1 hour

### Step 4: Restart mailserver and verify
```bash
docker compose restart mailserver

# After DNS propagates (~1 hour), test DKIM:
# Send an email and check headers — look for: dkim=pass
# Or use: https://www.mail-tester.com
```

**Note:** DMARC/DKIM checks will fail during DNS propagation. This is expected.

**Time: 60–90 minutes (mostly waiting for DNS).**

---

## Pre-Maintenance Checklist

Before any planned maintenance (VPS migration, major config change):

1. **Lower DNS TTL** on `minipass.me` A and MX records to 300 seconds — do this 1+ hour before
2. **Run a manual backup** on home system: `bash ~/minipass_env/scripts/backup_pull.sh`
3. **Verify backup** is complete: `ls ~/backups/minipass/latest/mail_server/config/opendkim/`
4. **Alert UptimeRobot**: Pause monitors temporarily to avoid false alerts during the work
5. **Document the change** in git before applying it

---

## Postfix Queue Management

```bash
# View queue
docker exec mailserver postqueue -p

# Flush queue (retry all deferred messages immediately)
docker exec mailserver postqueue -f

# Delete all queued messages (DESTRUCTIVE — use only when queue is poisoned)
docker exec mailserver postsuper -d ALL

# Check logs for delivery errors
docker exec mailserver tail -100 /var/log/mail/mail.log
```

**Remember:** Postfix is configured to queue for 10 days (`maximal_queue_lifetime`). Senders will not receive bounce errors until this timeout. A 2-hour outage loses zero emails.

---

## Contacts & Resources

| Resource | URL / Command |
|----------|---------------|
| UptimeRobot dashboard | https://uptimerobot.com |
| healthchecks.io | https://healthchecks.io |
| domain.com DNS panel | https://domain.com (login required) |
| Mail queue check | `docker exec mailserver postqueue -p` |
| Email analytics | `https://minipass.me/admin/mail-dashboard` |
| Backup location (home) | `~/backups/minipass/` |
| Latest backup | `~/backups/minipass/latest/` |
| Backup log | `~/backups/minipass/backup.log` |

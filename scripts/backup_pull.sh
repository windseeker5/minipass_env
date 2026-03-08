#!/bin/bash
# backup_pull.sh — Run on HOME SYSTEM (not VPS)
#
# Pulls critical Minipass VPS data to local backup via rsync over SSH.
# Run nightly via cron — if the ping to healthchecks.io stops firing, alert fires.
#
# HOME CRONTAB SETUP (crontab -e):
#   0 2 * * * /path/to/scripts/backup_pull.sh >> ~/backups/minipass/backup.log 2>&1
#
# FIRST-TIME SETUP:
#   1. Copy your home system's SSH public key to VPS:
#      ssh-copy-id -p 2222 kdresdell@minipass.me
#   2. Replace HEALTHCHECK_UUID below with your healthchecks.io check UUID.
#   3. Test with: bash backup_pull.sh

set -uo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
VPS="kdresdell@minipass.me"
VPS_PORT=2222
REMOTE_BASE="/home/kdresdell/minipass_env"
BACKUP_ROOT="$HOME/backups/minipass"
TODAY="$BACKUP_ROOT/$(date +%Y-%m-%d)"
HEALTHCHECK_UUID="a30a0440-d86d-41c3-b015-78a03f1f105d"   # https://healthchecks.io
RETENTION_DAYS=30
# ──────────────────────────────────────────────────────────────────────────────

SSH_OPTS=(-e "ssh -p $VPS_PORT")
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

log "Starting Minipass backup → $TODAY"
mkdir -p "$TODAY"/{mail_server/{config,maildata,mailstate},customers/deployed,minipass_env/{nginx,vhost.d,bloomcap/html,MinipassWebSite,email_monitoring/{reports,dmarc_reports},tools,scripts}}

# ── 1. DKIM keys — MOST CRITICAL (losing = emergency DNS TXT update required)
log "Backing up DKIM keys and mail config..."
rsync -avz "${SSH_OPTS[@]}" --rsync-path="sudo rsync" "$VPS:$REMOTE_BASE/config/" "$TODAY/mail_server/config/"

# ── 2. Mail data and state
log "Backing up maildata and mailstate..."
rsync -avz "${SSH_OPTS[@]}" --rsync-path="sudo rsync" "$VPS:$REMOTE_BASE/maildata/"  "$TODAY/mail_server/maildata/"
rsync -avz "${SSH_OPTS[@]}" --rsync-path="sudo rsync" "$VPS:$REMOTE_BASE/mailstate/" "$TODAY/mail_server/mailstate/"

# ── 3. SQLite databases (hot copy — acceptable for small SQLite DBs)
log "Backing up SQLite databases..."
rsync -avz "${SSH_OPTS[@]}" --rsync-path="sudo rsync" \
  "$VPS:$REMOTE_BASE/MinipassWebSite/customers.db"   "$TODAY/minipass_env/MinipassWebSite/"
rsync -avz "${SSH_OPTS[@]}" --rsync-path="sudo rsync" \
  "$VPS:$REMOTE_BASE/email_monitoring/monitoring.db" "$TODAY/minipass_env/email_monitoring/"

# ── 3a. Email monitoring reports and DMARC files
log "Backing up email monitoring reports..."
rsync -avz "${SSH_OPTS[@]}" --rsync-path="sudo rsync" \
  "$VPS:$REMOTE_BASE/email_monitoring/reports/" "$TODAY/minipass_env/email_monitoring/reports/" 2>/dev/null || true
rsync -avz "${SSH_OPTS[@]}" --rsync-path="sudo rsync" \
  "$VPS:$REMOTE_BASE/email_monitoring/dmarc_reports/" "$TODAY/minipass_env/email_monitoring/dmarc_reports/" 2>/dev/null || true

# ── 4. Deployed customer apps (databases, secrets, uploads — skip regeneratable dirs)
log "Backing up deployed customer apps (databases, secrets, uploads)..."
rsync -avz "${SSH_OPTS[@]}" --rsync-path="sudo rsync" "$VPS:$REMOTE_BASE/deployed/" "$TODAY/customers/deployed/" \
  --exclude="venv/" \
  --exclude="__pycache__/" \
  --exclude="*.pyc" \
  --exclude="migrations/" \
  --exclude="node_modules/"

# ── 5. Docker Compose + nginx config
log "Backing up docker-compose.yml and nginx config..."
rsync -avz "${SSH_OPTS[@]}" "$VPS:$REMOTE_BASE/docker-compose.yml" "$TODAY/minipass_env/"
rsync -avz "${SSH_OPTS[@]}" "$VPS:$REMOTE_BASE/nginx/"             "$TODAY/minipass_env/nginx/"
rsync -avz "${SSH_OPTS[@]}" "$VPS:$REMOTE_BASE/vhost.d/"           "$TODAY/minipass_env/vhost.d/" \
  2>/dev/null || log "Warning: vhost.d not found (skipping)"

# ── 6. .env files (SENSITIVE — stays on home server only, never pushed to cloud)
log "Backing up .env files..."
rsync -avz "${SSH_OPTS[@]}" \
  "$VPS:$REMOTE_BASE/MinipassWebSite/.env"            "$TODAY/minipass_env/MinipassWebSite/.env"            2>/dev/null || true
rsync -avz "${SSH_OPTS[@]}" \
  "$VPS:$REMOTE_BASE/MinipassWebSite/.env.production" "$TODAY/minipass_env/MinipassWebSite/.env.production" 2>/dev/null || true
rsync -avz "${SSH_OPTS[@]}" \
  "$VPS:$REMOTE_BASE/mailserver.env" "$TODAY/mail_server/mailserver.env" 2>/dev/null || true
rsync -avz "${SSH_OPTS[@]}" \
  "$VPS:$REMOTE_BASE/.env" "$TODAY/minipass_env/.env" 2>/dev/null || true

# ── 7. Bloomcap website content
log "Backing up bloomcap website..."
rsync -avz "${SSH_OPTS[@]}" \
  "$VPS:$REMOTE_BASE/bloomcap/html/" "$TODAY/minipass_env/bloomcap/html/" 2>/dev/null || true
rsync -avz "${SSH_OPTS[@]}" \
  "$VPS:$REMOTE_BASE/bloomcap/.env"  "$TODAY/minipass_env/bloomcap/.env"  2>/dev/null || true

# ── 8. Tools and scripts directories (fail2ban manager, .conf files, operational scripts)
log "Backing up tools and scripts directories..."
rsync -avz "${SSH_OPTS[@]}" \
  "$VPS:$REMOTE_BASE/tools/" "$TODAY/minipass_env/tools/" 2>/dev/null || true
rsync -avz "${SSH_OPTS[@]}" \
  "$VPS:$REMOTE_BASE/scripts/" "$TODAY/minipass_env/scripts/" 2>/dev/null || true

# ── 9. VPS crontab
log "Backing up VPS crontab..."
ssh -p "$VPS_PORT" "$VPS" "crontab -l" > "$TODAY/minipass_env/crontab.txt" 2>/dev/null \
  && log "Crontab backup: OK ($(wc -l < "$TODAY/minipass_env/crontab.txt") lines)" \
  || log "Warning: crontab backup failed or empty"

# ── 10. Update 'latest' symlink
ln -sfn "$TODAY" "$BACKUP_ROOT/latest"

# ── 11. Retention: delete backups older than RETENTION_DAYS
log "Pruning backups older than $RETENTION_DAYS days..."
find "$BACKUP_ROOT" -maxdepth 1 -type d -name "20*" -mtime +"$RETENTION_DAYS" \
  -exec rm -rf {} \; 2>/dev/null || true

# ── 12. Quick integrity check
DKIM_DIR="$TODAY/mail_server/config/opendkim"
if [ -d "$DKIM_DIR" ] && [ -n "$(ls -A "$DKIM_DIR" 2>/dev/null)" ]; then
  log "DKIM keys present: OK"
else
  log "WARNING: DKIM key directory missing or empty — check $DKIM_DIR"
fi

DB_COUNT=$(find "$TODAY/minipass_env/MinipassWebSite" -name "*.db" 2>/dev/null | wc -l)
log "Databases backed up: $DB_COUNT files"

UPLOAD_COUNT=$(find "$TODAY/customers" -path "*/static/uploads/*" -type f 2>/dev/null | wc -l)
log "User uploads backed up: $UPLOAD_COUNT files"

ENV_COUNT=$(find "$TODAY" \( -name "*.env" -o -name ".env" \) 2>/dev/null | wc -l)
log "Env files backed up: $ENV_COUNT"

CRON_LINES=$(wc -l < "$TODAY/minipass_env/crontab.txt" 2>/dev/null || echo "0")
log "Crontab lines: $CRON_LINES"

# ── 13. Ping healthchecks.io (fires alert if this line is never reached)
if [ "$HEALTHCHECK_UUID" != "REPLACE_WITH_YOUR_HEALTHCHECKS_UUID" ]; then
  curl -fsS --retry 3 "https://hc-ping.com/$HEALTHCHECK_UUID" > /dev/null 2>&1 \
    && log "Healthcheck ping: sent" \
    || log "Warning: healthcheck ping failed"
else
  log "Healthcheck ping: skipped (UUID not configured)"
fi

log "Backup complete: $TODAY"

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

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
VPS="kdresdell@minipass.me"
VPS_PORT=2222
REMOTE_BASE="/home/kdresdell/minipass_env"
BACKUP_ROOT="$HOME/backups/minipass"
TODAY="$BACKUP_ROOT/$(date +%Y-%m-%d)"
HEALTHCHECK_UUID="REPLACE_WITH_YOUR_HEALTHCHECKS_UUID"   # https://healthchecks.io
RETENTION_DAYS=30
# ──────────────────────────────────────────────────────────────────────────────

SSH_OPTS="-e ssh -p $VPS_PORT"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

log "Starting Minipass backup → $TODAY"
mkdir -p "$TODAY"/{config,maildata,mailstate,databases,deployed,nginx,env}

# ── 1. DKIM keys — MOST CRITICAL (losing = emergency DNS TXT update required)
log "Backing up DKIM keys and mail config..."
rsync -avz $SSH_OPTS "$VPS:$REMOTE_BASE/config/" "$TODAY/config/"

# ── 2. Mail data and state
log "Backing up maildata and mailstate..."
rsync -avz $SSH_OPTS "$VPS:$REMOTE_BASE/maildata/" "$TODAY/maildata/"
rsync -avz $SSH_OPTS "$VPS:$REMOTE_BASE/mailstate/" "$TODAY/mailstate/"

# ── 3. SQLite databases (hot copy — acceptable for small SQLite DBs)
log "Backing up SQLite databases..."
rsync -avz $SSH_OPTS \
  "$VPS:$REMOTE_BASE/MinipassWebSite/customers.db" \
  "$VPS:$REMOTE_BASE/app/instance/minipass.db" \
  "$VPS:$REMOTE_BASE/email_monitoring/monitoring.db" \
  "$TODAY/databases/"

# ── 4. Deployed customer databases (*.db files only, skip venv/code)
log "Backing up deployed customer databases..."
rsync -avz $SSH_OPTS "$VPS:$REMOTE_BASE/deployed/" "$TODAY/deployed/" \
  --include="*/" --include="*.db" --exclude="*"

# ── 5. Docker Compose + nginx config
log "Backing up docker-compose.yml and nginx config..."
rsync -avz $SSH_OPTS "$VPS:$REMOTE_BASE/docker-compose.yml" "$TODAY/"
rsync -avz $SSH_OPTS "$VPS:$REMOTE_BASE/nginx/" "$TODAY/nginx/"

# ── 6. .env files (SENSITIVE — stays on home server only, never pushed to cloud)
log "Backing up .env files..."
rsync -avz $SSH_OPTS \
  "$VPS:$REMOTE_BASE/MinipassWebSite/.env" \
  "$VPS:$REMOTE_BASE/MinipassWebSite/.env.production" \
  "$VPS:$REMOTE_BASE/app/.env" \
  "$VPS:$REMOTE_BASE/mailserver.env" \
  "$TODAY/env/" 2>/dev/null || log "Warning: some .env files not found (skipping)"

# ── 7. Update 'latest' symlink
ln -sfn "$TODAY" "$BACKUP_ROOT/latest"

# ── 8. Retention: delete backups older than RETENTION_DAYS
log "Pruning backups older than $RETENTION_DAYS days..."
find "$BACKUP_ROOT" -maxdepth 1 -type d -name "20*" -mtime +"$RETENTION_DAYS" \
  -exec rm -rf {} \; 2>/dev/null || true

# ── 9. Quick integrity check
DKIM_DIR="$TODAY/config/opendkim"
if [ -d "$DKIM_DIR" ] && [ -n "$(ls -A "$DKIM_DIR" 2>/dev/null)" ]; then
  log "DKIM keys present: OK"
else
  log "WARNING: DKIM key directory missing or empty — check $DKIM_DIR"
fi

DB_COUNT=$(find "$TODAY/databases" -name "*.db" 2>/dev/null | wc -l)
log "Databases backed up: $DB_COUNT files"

# ── 10. Ping healthchecks.io (fires alert if this line is never reached)
if [ "$HEALTHCHECK_UUID" != "REPLACE_WITH_YOUR_HEALTHCHECKS_UUID" ]; then
  curl -fsS --retry 3 "https://hc-ping.com/$HEALTHCHECK_UUID" > /dev/null 2>&1 \
    && log "Healthcheck ping: sent" \
    || log "Warning: healthcheck ping failed"
else
  log "Healthcheck ping: skipped (UUID not configured)"
fi

log "Backup complete: $TODAY"

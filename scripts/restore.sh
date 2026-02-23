#!/bin/bash
# restore.sh — Run on VPS (existing or new)
#
# Restores Minipass from a home server backup and starts all Docker services.
# Used for Scenario B (data corruption) or Scenario C (new VPS provisioning).
#
# USAGE:
#   On home system — push backup to VPS first:
#     rsync -avz -e "ssh -p 2222" ~/backups/minipass/latest/ \
#       kdresdell@minipass.me:/home/kdresdell/minipass_env_restore/
#
#   Then on VPS:
#     bash restore.sh [backup_dir]
#
#   backup_dir defaults to /home/kdresdell/minipass_env_restore (the rsync target above)
#
# For a NEW VPS (Scenario C):
#   1. Provision VPS, install Docker (see RECOVERY_RUNBOOK.md)
#   2. git clone <repo> /home/kdresdell/minipass_env
#   3. rsync backup from home to VPS
#   4. Run this script

set -euo pipefail

RESTORE_FROM="${1:-/home/kdresdell/minipass_env_restore}"
TARGET="/home/kdresdell/minipass_env"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

if [ ! -d "$RESTORE_FROM" ]; then
  echo "ERROR: Restore source not found: $RESTORE_FROM"
  echo "Usage: $0 [backup_dir]"
  exit 1
fi

log "Restoring from: $RESTORE_FROM"
log "Target: $TARGET"
echo ""
echo "This will overwrite data in $TARGET and restart all Docker services."
read -rp "Continue? [y/N] " confirm
[[ "$confirm" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 0; }

# ── Stop running services (graceful)
log "Stopping Docker services..."
cd "$TARGET"
docker compose down 2>/dev/null || docker-compose down 2>/dev/null || true

# ── Restore config (DKIM keys, postfix accounts, etc.)
if [ -d "$RESTORE_FROM/mail_server/config" ]; then
  log "Restoring mail config (DKIM keys, postfix accounts)..."
  rsync -av "$RESTORE_FROM/mail_server/config/" "$TARGET/config/"
else
  log "WARNING: mail_server/config/ not in backup — DKIM keys missing (see RECOVERY_RUNBOOK.md)"
fi

# ── Restore mail data
if [ -d "$RESTORE_FROM/mail_server/maildata" ]; then
  log "Restoring maildata..."
  rsync -av "$RESTORE_FROM/mail_server/maildata/" "$TARGET/maildata/"
fi

if [ -d "$RESTORE_FROM/mail_server/mailstate" ]; then
  log "Restoring mailstate..."
  rsync -av "$RESTORE_FROM/mail_server/mailstate/" "$TARGET/mailstate/"
fi

# ── Restore SQLite databases
if [ -f "$RESTORE_FROM/minipass_env/MinipassWebSite/customers.db" ]; then
  log "Restoring customers.db..."
  cp "$RESTORE_FROM/minipass_env/MinipassWebSite/customers.db" "$TARGET/MinipassWebSite/customers.db"
fi

if [ -f "$RESTORE_FROM/minipass_env/email_monitoring/monitoring.db" ]; then
  log "Restoring monitoring.db..."
  mkdir -p "$TARGET/email_monitoring"
  cp "$RESTORE_FROM/minipass_env/email_monitoring/monitoring.db" "$TARGET/email_monitoring/monitoring.db"
fi

# ── Restore deployed customer databases
if [ -d "$RESTORE_FROM/customers/deployed" ]; then
  log "Restoring deployed customer databases..."
  rsync -av "$RESTORE_FROM/customers/deployed/" "$TARGET/deployed/" \
    --include="*/" --include="*.db" --exclude="*"
fi

# ── Restore nginx config
if [ -d "$RESTORE_FROM/minipass_env/nginx" ]; then
  log "Restoring nginx config..."
  rsync -av "$RESTORE_FROM/minipass_env/nginx/" "$TARGET/nginx/"
fi

# ── Restore .env files
log "Restoring .env files..."
[ -f "$RESTORE_FROM/minipass_env/MinipassWebSite/.env" ] && \
  cp "$RESTORE_FROM/minipass_env/MinipassWebSite/.env" "$TARGET/MinipassWebSite/.env"
[ -f "$RESTORE_FROM/minipass_env/MinipassWebSite/.env.production" ] && \
  cp "$RESTORE_FROM/minipass_env/MinipassWebSite/.env.production" "$TARGET/MinipassWebSite/.env.production"
[ -f "$RESTORE_FROM/mail_server/mailserver.env" ] && \
  cp "$RESTORE_FROM/mail_server/mailserver.env" "$TARGET/mailserver.env"
[ -f "$RESTORE_FROM/minipass_env/.env" ] && \
  cp "$RESTORE_FROM/minipass_env/.env" "$TARGET/.env"

# ── Start services
log "Starting Docker services..."
cd "$TARGET"
docker compose up -d 2>/dev/null || docker-compose up -d

# ── Wait for services to come up
log "Waiting 15 seconds for services to initialize..."
sleep 15

# ── Verify
log "Service status:"
docker compose ps 2>/dev/null || docker-compose ps

log ""
log "Checking mail queue:"
docker exec mailserver postqueue -p 2>/dev/null || log "(mailserver not yet running)"

log ""
log "Restore complete. Next steps:"
log "  1. Send a test email to verify mail flow"
log "  2. Check https://minipass.me and https://lhgi.minipass.me"
log "  3. If new VPS: update DNS A record at domain.com → new VPS IP"
log "  4. If DKIM keys were missing: regenerate and update DNS TXT record"
log "     See: docs/RECOVERY_RUNBOOK.md — DKIM Key Loss section"

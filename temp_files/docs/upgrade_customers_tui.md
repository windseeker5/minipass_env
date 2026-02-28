# Upgrade Customers TUI — Reference Guide

## Overview

`upgrade_customers.py` is a terminal-based (TUI) tool for upgrading and backing up Minipass customer containers. It reads deployed customers from `customers.db`, adds LHGI as a hardcoded entry, and presents a multi-select menu for choosing which customers to process.

**Location:** `/home/kdresdell/minipass_env/upgrade_customers.py`

**Dependency:** `pip3 install simple-term-menu`

## Quick Start

```bash
# Upgrade selected customers (default mode)
python3 upgrade_customers.py

# Backup only — no upgrades, no notifications
python3 upgrade_customers.py --backup-only

# Dry run — preview what would happen without executing anything
python3 upgrade_customers.py --dry-run

# Dry-run backup — preview backup operations only
python3 upgrade_customers.py --dry-run --backup-only
```

## CLI Flags

| Flag | Description |
|------|-------------|
| `--dry-run` | Show what would be done without executing any commands or creating any files |
| `--backup-only` | Create `.tar.gz` backups without running upgrade steps. Adds **Mail Server** to the selection list. Skips email notification output |

Flags can be combined. When both are set, the tool previews backup operations without touching disk.

## How It Works

### Upgrade Mode (default)

1. Reads deployed customers from `customers.db` + hardcoded LHGI entry
2. TUI multi-select menu for choosing customers
3. For each selected customer:
   - Creates a `.tar.gz` backup archive
   - Runs upgrade steps (git fetch/reset, stop container, migrate DB, rebuild, start)
4. Prints summary with success/failure counts and email notification list

### Backup-Only Mode (`--backup-only`)

1. Same customer list as upgrade mode, **plus a Mail Server option**
2. TUI multi-select menu
3. For each selected customer: creates a `.tar.gz` backup archive only
4. Prints summary with backup paths and sizes (no email notification output)

## Backup Details

### Archive Location

```
~/customer_backups/{subdomain}/{subdomain}_backup_YYYYMMDD_HHMMSS.tar.gz
```

### What Gets Backed Up

| Customer Type | Contents |
|---------------|----------|
| **LHGI** | `instance/minipass.db`, `static/uploads`, `templates/email_templates` |
| **Deployed customers** | `instance/minipass.db`, `static/uploads`, `templates/email_templates` |
| **Mail Server** (backup-only) | `maildata`, `mailstate`, `config` |

Missing paths are skipped with a `WARNING` log message (non-fatal).

### Disk Space Check

Before creating an archive, the tool checks available disk space and requires **2x the estimated uncompressed size** as a safety margin. If space is insufficient, the backup fails with an error message.

## TUI Navigation

| Key | Action |
|-----|--------|
| Arrow keys (Up/Down) | Navigate the customer list |
| `SPACE` | Select / deselect a customer |
| `ENTER` | Confirm selection |

After confirming, you'll see a `Continue with upgrade/back up? [y/N]:` prompt.

## Inspecting Backups

```bash
# List all backup directories
ls -lh ~/customer_backups/

# List contents of a specific archive
tar -tzf ~/customer_backups/lhgi/lhgi_backup_20250601_143000.tar.gz

# Check archive size
ls -lh ~/customer_backups/lhgi/
```

## Troubleshooting

| Issue | Cause / Fix |
|-------|-------------|
| `Insufficient disk space` | Free up space — the tool requires 2x the estimated uncompressed size |
| `No data found to back up` | The customer's expected directory doesn't exist on disk |
| Missing paths logged as `WARNING` | Individual files/dirs (uploads, email templates) not found — skipped, non-fatal |
| `Command timed out after 5 minutes` | A shell command (build, migration, etc.) exceeded the 5-minute timeout |
| `simple-term-menu not installed` | Run `pip3 install simple-term-menu` |
| `Database not found` | `customers.db` not at expected path — only LHGI will be available |
| Mail server appears in upgrade mode | It doesn't — Mail Server is only shown in `--backup-only` mode |

## Syncing Backups to Local Machine

Run this from your **local dev machine** to pull all customer backups from the VPS:

```bash
rsync -avz -e "ssh -p 2222" kdresdell@minipass.me:~/customer_backups/ ~/customer_backups/
```

To sync a single customer's backups:

```bash
rsync -avz -e "ssh -p 2222" kdresdell@minipass.me:~/customer_backups/lhgi/ ~/customer_backups/lhgi/
```

# Upgrade Customers TUI Guide

A terminal-based interface for automating customer container upgrades on the Minipass VPS.

## Prerequisites

1. **SSH access** to the VPS (port 2222)
2. **Code pushed** to the `main` branch on GitHub
3. **simple-term-menu** Python package installed:
   ```bash
   pip3 install simple-term-menu
   ```

## Quick Start

```bash
ssh -p 2222 kdresdell@minipass.me
cd /home/kdresdell/minipass_env
python3 upgrade_customers.py
```

## TUI Usage

When you run the script, you'll see a multi-select menu listing all customers:

```
Select customers to upgrade (SPACE to select, ENTER to confirm):

  [LHGI] LHGI - LHGI (lhgi@jfgoulet.com)
  CUSTOMER1 - Organization Name (email@example.com)
  CUSTOMER2 - Another Org (other@example.com)
```

### Controls

| Key | Action |
|-----|--------|
| `SPACE` | Toggle selection on/off for current item |
| `UP/DOWN` | Navigate through the list |
| `ENTER` | Confirm selection and proceed |
| `q` / `Ctrl+C` | Cancel and exit |

You can select multiple customers in a single run.

## Command Line Options

```bash
# Normal execution
python3 upgrade_customers.py

# Dry-run mode (shows what would happen without executing)
python3 upgrade_customers.py --dry-run
```

Use `--dry-run` to preview all commands before actually running them.

## What the Script Does

### For LHGI (Primary Instance)

The LHGI upgrade follows this sequence:

1. **Fetch and reset** - `git fetch origin && git reset --hard origin/main`
2. **Stop container** - `docker-compose stop lhgi`
3. **Run database migration** - `python3 migrations/upgrade_production_database.py`
4. **Clear Docker cache** - `docker system prune -f && docker builder prune -f`
5. **Tag backup image** - Tags current image as `minipass_env-lhgi:backup`
6. **Build container** - `docker-compose build --no-cache --pull lhgi`
7. **Start container** - `docker-compose up -d lhgi`

### For Deployed Customers

Deployed customers use a backup-restore approach:

1. **Backup database** - Copies `minipass.db` to `~/backup_{subdomain}_{timestamp}.db`
2. **Backup uploads** - Copies uploads folder to `~/backup_{subdomain}_uploads_{timestamp}`
3. **Stop containers** - `docker-compose down`
4. **Fetch and reset** - `git fetch origin && git reset --hard origin/main && git clean -fd`
5. **Restore database** - Copies backup back to instance folder
6. **Restore uploads** - Copies uploads backup back
7. **Run database migration** - `python3 app/migrations/upgrade_production_database.py`
8. **Build container** - `docker-compose build --no-cache`
9. **Start container** - `docker-compose up -d`

## Database Migration

The script automatically calls `upgrade_production_database.py` which runs all migration tasks:

- Schema updates (new columns, tables, indexes)
- Data migrations (content transformations)
- View recreations (SQL views for reporting)
- Fiscal year fixes (AP filtering improvements)

As of January 2026, the migration script includes **21 tasks**, including:
- Task 21: AP fiscal year filtering fix (uses effective date logic for unpaid expenses)

## Customer Source

Customers are read from two sources:

1. **LHGI** - Hardcoded as the first option (always available)
2. **Deployed customers** - Read from `/home/kdresdell/minipass_env/MinipassWebSite/customers.db`
   - Only customers with `deployed = 1` are shown

## After Upgrade

The script outputs:
- A summary of successful/failed upgrades
- Email addresses of successfully upgraded customers (for notification)

### Example Output

```
============================================================
  UPGRADE SUMMARY
============================================================

Total: 2 | Success: 2 | Failed: 0

SEND NOTIFICATION TO:
  lhgi@jfgoulet.com, customer@example.com
```

## Troubleshooting

### "simple-term-menu not installed"

```bash
pip3 install simple-term-menu
```

### "Database not found"

The `customers.db` file doesn't exist at the expected path. Only LHGI will be available. This is normal if no additional customers have been deployed.

### "Customer directory not found"

The customer's deployed directory doesn't exist in `/home/kdresdell/minipass_env/deployed/{subdomain}`. Verify the customer was deployed correctly.

### Container fails to start

1. Check Docker logs:
   ```bash
   docker-compose logs lhgi
   # or for deployed customers:
   cd /home/kdresdell/minipass_env/deployed/{subdomain}
   docker-compose logs
   ```

2. If LHGI, restore the backup image:
   ```bash
   docker tag minipass_env-lhgi:backup minipass_env-lhgi:latest
   docker-compose up -d lhgi
   ```

3. For deployed customers, restore from backup:
   ```bash
   cp ~/backup_{subdomain}_{timestamp}.db /path/to/app/instance/minipass.db
   ```

### Migration fails

Check the migration script directly:
```bash
cd /home/kdresdell/minipass_env/app
python3 migrations/upgrade_production_database.py
```

Review the output for specific task failures.

### Timeout errors

Commands have a 5-minute timeout. If builds consistently timeout:
- Check disk space: `df -h`
- Check Docker resources: `docker system df`
- Clear old images: `docker image prune -a`

## Related Documentation

- [UPGRADE_AND_DEPLOY.md](UPGRADE_AND_DEPLOY.md) - Manual upgrade steps and deployment guide
- [ENV_SETUP.md](ENV_SETUP.md) - Environment setup instructions

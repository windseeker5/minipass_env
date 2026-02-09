#!/usr/bin/env python3
"""
Minipass Deployment Automation Script

A TUI-based tool for upgrading multiple customer containers.
Reads from customers.db and allows selective deployment with progress tracking.

Usage:
    python3 upgrade_customers.py

Dependencies:
    pip3 install simple-term-menu
"""

import argparse
import os
import shutil
import sqlite3
import subprocess
import sys
import tarfile
from datetime import datetime
from pathlib import Path

# Global flags
DRY_RUN = False
BACKUP_ONLY = False

try:
    from simple_term_menu import TerminalMenu
except ImportError:
    print("Error: simple-term-menu not installed.")
    print("Install with: pip3 install simple-term-menu")
    sys.exit(1)


# Configuration
CUSTOMERS_DB_PATH = "/home/kdresdell/minipass_env/MinipassWebSite/customers.db"
MINIPASS_ENV_PATH = "/home/kdresdell/minipass_env"
DEPLOYED_PATH = f"{MINIPASS_ENV_PATH}/deployed"
LHGI_APP_PATH = f"{MINIPASS_ENV_PATH}/app"
BACKUP_DIR = os.path.expanduser("~/customer_backups")

# LHGI hardcoded configuration (not in customers.db)
LHGI_CONFIG = {
    "subdomain": "lhgi",
    "organization": "LHGI",
    "email": "lhgi@jfgoulet.com",
    "is_lhgi": True,
    "is_mailserver": False
}

MAILSERVER_CONFIG = {
    "subdomain": "mailserver",
    "organization": "Mail Server",
    "email": "admin@minipass.me",
    "is_lhgi": False,
    "is_mailserver": True
}


def log(message: str, level: str = "INFO") -> None:
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def run_command(command: str, cwd: str = None) -> tuple[bool, str]:
    """Run a shell command and return success status and output."""
    global DRY_RUN

    if DRY_RUN:
        log(f"    [DRY-RUN] Would execute: {command}", "DRY")
        return True, "[DRY-RUN] Command not executed"

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        output = result.stdout + result.stderr
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "Command timed out after 5 minutes"
    except Exception as e:
        return False, str(e)


def format_size(size_bytes: int) -> str:
    """Return human-readable file size."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def estimate_backup_size(data_paths: dict) -> int:
    """Walk directories/files and sum total size in bytes."""
    total = 0
    for fs_path in data_paths.values():
        p = Path(fs_path)
        if p.is_file():
            total += p.stat().st_size
        elif p.is_dir():
            for f in p.rglob("*"):
                if f.is_file():
                    total += f.stat().st_size
    return total


def get_customer_data_paths(customer: dict) -> dict:
    """Return dict of {archive_name: filesystem_path} for backup.

    Filters out paths that don't exist on disk.
    """
    paths = {}

    if customer.get("is_mailserver"):
        base = MINIPASS_ENV_PATH
        candidates = {
            "maildata": f"{base}/maildata",
            "mailstate": f"{base}/mailstate",
            "config": f"{base}/config",
        }
    elif customer["is_lhgi"]:
        base = LHGI_APP_PATH
        candidates = {
            "instance/minipass.db": f"{base}/instance/minipass.db",
            "static/uploads": f"{base}/static/uploads",
            "templates/email_templates": f"{base}/templates/email_templates",
        }
    else:
        base = f"{DEPLOYED_PATH}/{customer['subdomain']}/app"
        candidates = {
            "instance/minipass.db": f"{base}/instance/minipass.db",
            "static/uploads": f"{base}/static/uploads",
            "templates/email_templates": f"{base}/templates/email_templates",
        }

    for name, fs_path in candidates.items():
        if Path(fs_path).exists():
            paths[name] = fs_path
        else:
            log(f"  Skipping {name} (not found: {fs_path})", "WARNING")

    return paths


def create_tar_backup(subdomain: str, data_paths: dict) -> tuple[bool, str, str]:
    """Create a .tar.gz archive of the given paths.

    Returns (success, message, archive_path).
    """
    if not data_paths:
        return False, "No data paths to back up", ""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_subdir = os.path.join(BACKUP_DIR, subdomain)
    archive_name = f"{subdomain}_backup_{timestamp}.tar.gz"
    archive_path = os.path.join(backup_subdir, archive_name)

    estimated = estimate_backup_size(data_paths)

    if DRY_RUN:
        log(f"    [DRY-RUN] Would create: {archive_path}", "DRY")
        log(f"    [DRY-RUN] Estimated size: {format_size(estimated)}", "DRY")
        for name, fs_path in data_paths.items():
            log(f"    [DRY-RUN]   {name} <- {fs_path}", "DRY")
        return True, f"Would create {archive_name} (~{format_size(estimated)})", archive_path

    # Check disk space (require 2x estimated size as safety margin)
    try:
        stat = shutil.disk_usage(BACKUP_DIR if os.path.exists(BACKUP_DIR) else os.path.expanduser("~"))
        required = estimated * 2
        if stat.free < required:
            return False, f"Insufficient disk space: {format_size(stat.free)} free, need {format_size(required)}", ""
    except OSError as e:
        return False, f"Could not check disk space: {e}", ""

    # Create backup directory
    os.makedirs(backup_subdir, exist_ok=True)

    # Create tar archive
    try:
        with tarfile.open(archive_path, "w:gz") as tar:
            for archive_name_entry, fs_path in data_paths.items():
                tar.add(fs_path, arcname=archive_name_entry)

        archive_size = os.path.getsize(archive_path)
        return True, f"Created {archive_name} ({format_size(archive_size)})", archive_path
    except Exception as e:
        # Clean up partial archive
        if os.path.exists(archive_path):
            os.remove(archive_path)
        return False, f"Failed to create archive: {e}", ""


def backup_customer(customer: dict) -> tuple[bool, str]:
    """Orchestrate backup for a customer. Returns (success, message)."""
    subdomain = customer["subdomain"]
    log(f"  Getting data paths for {subdomain}...")
    data_paths = get_customer_data_paths(customer)

    if not data_paths:
        return False, "No data found to back up"

    log(f"  Creating backup archive...")
    success, message, archive_path = create_tar_backup(subdomain, data_paths)
    return success, message


def get_customers_from_db() -> list[dict]:
    """Read deployed customers from customers.db."""
    customers = []

    db_path = Path(CUSTOMERS_DB_PATH)
    if not db_path.exists():
        log(f"Database not found: {CUSTOMERS_DB_PATH}", "WARNING")
        log("Only LHGI will be available for selection", "WARNING")
        return customers

    try:
        conn = sqlite3.connect(CUSTOMERS_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check if customers table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='customers'
        """)
        if not cursor.fetchone():
            log("Table 'customers' not found in database", "WARNING")
            conn.close()
            return customers

        # Get all deployed customers
        cursor.execute("""
            SELECT subdomain, email, organization_name
            FROM customers
            WHERE deployed = 1
        """)

        for row in cursor.fetchall():
            customers.append({
                "subdomain": row["subdomain"],
                "organization": row["organization_name"],
                "email": row["email"],
                "is_lhgi": False
            })

        conn.close()
        log(f"Found {len(customers)} deployed customers in database")
    except sqlite3.Error as e:
        log(f"Database error: {e}", "ERROR")

    return customers


def upgrade_lhgi() -> tuple[bool, str]:
    """Run upgrade steps for LHGI (git pull method)."""
    log("  Creating backup before upgrade...")
    backup_success, backup_msg = backup_customer(LHGI_CONFIG)
    if not backup_success:
        return False, f"Backup failed: {backup_msg}"
    log(f"  {backup_msg}")

    steps = [
        # Step 2: Pull latest code
        ("Fetching and resetting to origin/main",
         f"cd {LHGI_APP_PATH} && git fetch origin && git reset --hard origin/main"),

        # Step 4: Stop container
        ("Stopping LHGI container",
         f"cd {MINIPASS_ENV_PATH} && docker-compose stop lhgi"),

        # Step 5: Run database migration
        ("Running database migration",
         f"cd {LHGI_APP_PATH} && python3 migrations/upgrade_production_database.py"),

        # Step 6: Clear Docker cache
        ("Clearing Docker cache (system prune)",
         f"cd {MINIPASS_ENV_PATH} && docker system prune -f"),

        ("Clearing Docker cache (builder prune)",
         f"cd {MINIPASS_ENV_PATH} && docker builder prune -f"),

        # Step 7: Tag current image as backup
        ("Tagging current image as backup",
         "docker tag minipass_env-lhgi:latest minipass_env-lhgi:backup 2>/dev/null || true"),

        # Step 8: Build new container (no cache, pull latest base images)
        ("Building LHGI container (no cache, pull latest)",
         f"cd {MINIPASS_ENV_PATH} && docker-compose build --no-cache --pull lhgi"),

        # Step 9: Start container
        ("Starting LHGI container",
         f"cd {MINIPASS_ENV_PATH} && docker-compose up -d lhgi"),
    ]

    for step_name, command in steps:
        log(f"  {step_name}...")
        success, output = run_command(command)
        if not success:
            return False, f"Failed at: {step_name}\n{output}"

    return True, "All steps completed successfully"


def upgrade_deployed_customer(subdomain: str) -> tuple[bool, str]:
    """Run upgrade steps for a deployed customer (git reset method)."""
    customer_path = f"{DEPLOYED_PATH}/{subdomain}"
    app_path = f"{customer_path}/app"

    # Verify customer directory exists
    if not Path(customer_path).exists():
        return False, f"Customer directory not found: {customer_path}"

    # Create permanent backup archive
    customer_config = {"subdomain": subdomain, "is_lhgi": False, "is_mailserver": False}
    log("  Creating backup before upgrade...")
    backup_success, backup_msg = backup_customer(customer_config)
    if not backup_success:
        return False, f"Backup failed: {backup_msg}"
    log(f"  {backup_msg}")

    # Temporary copies for the git-reset-then-restore dance
    tmp_db = f"/tmp/upgrade_{subdomain}_minipass.db"
    tmp_uploads = f"/tmp/upgrade_{subdomain}_uploads"

    steps = [
        ("Copying database to temp",
         f"cp {app_path}/instance/minipass.db {tmp_db}"),

        ("Copying uploads to temp",
         f"cp -r {app_path}/static/uploads {tmp_uploads}"),

        ("Stopping containers",
         f"cd {customer_path} && docker-compose down"),

        ("Fetching and resetting to origin/main",
         f"cd {app_path} && git fetch origin && git reset --hard origin/main && git clean -fd"),

        ("Restoring database from temp",
         f"cp {tmp_db} {app_path}/instance/minipass.db"),

        ("Restoring uploads from temp",
         f"cp -r {tmp_uploads}/. {app_path}/static/uploads/"),

        ("Running database migration",
         f"cd {customer_path} && python3 app/migrations/upgrade_production_database.py"),

        ("Building container (no cache)",
         f"cd {customer_path} && docker-compose build --no-cache"),

        ("Starting container",
         f"cd {customer_path} && docker-compose up -d"),

        ("Cleaning up temp files",
         f"rm -f {tmp_db} && rm -rf {tmp_uploads}"),
    ]

    for step_name, command in steps:
        log(f"  {step_name}...")
        success, output = run_command(command)
        if not success:
            return False, f"Failed at: {step_name}\n{output}"

    return True, "All steps completed successfully"


def upgrade_customer(customer: dict) -> tuple[bool, str]:
    """Upgrade a single customer based on their type."""
    if customer.get("is_mailserver"):
        return False, "Mail server cannot be upgraded, use --backup-only mode"
    if customer["is_lhgi"]:
        return upgrade_lhgi()
    else:
        return upgrade_deployed_customer(customer["subdomain"])


def main():
    global DRY_RUN, BACKUP_ONLY

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Minipass Deployment Automation - Upgrade customer containers"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing any commands"
    )
    parser.add_argument(
        "--backup-only",
        action="store_true",
        help="Create backups without upgrading"
    )
    args = parser.parse_args()

    DRY_RUN = args.dry_run
    BACKUP_ONLY = args.backup_only

    mode_label = "Minipass Deployment Automation"
    mode_tags = []
    if DRY_RUN:
        mode_tags.append("DRY-RUN MODE")
    if BACKUP_ONLY:
        mode_tags.append("BACKUP-ONLY MODE")

    print("\n" + "=" * 60)
    if mode_tags:
        print(f"  {mode_label} [{' | '.join(mode_tags)}]")
        if DRY_RUN:
            print("  (No commands will be executed)")
    else:
        print(f"  {mode_label}")
    print("=" * 60 + "\n")

    action = "back up" if BACKUP_ONLY else "upgrade"

    # Step 1: Get customers from database
    log("Reading customers from database...")
    customers = get_customers_from_db()

    # Add is_mailserver key to db customers for consistency
    for c in customers:
        c.setdefault("is_mailserver", False)

    # Step 2: Build customer list
    all_customers = [LHGI_CONFIG] + customers
    if BACKUP_ONLY:
        all_customers.append(MAILSERVER_CONFIG)

    if not all_customers:
        log("No customers found!", "ERROR")
        sys.exit(1)

    log(f"Found {len(all_customers)} customers (including LHGI)")

    # Step 3: Build menu options
    menu_options = []
    for c in all_customers:
        label = f"{c['subdomain'].upper()} - {c['organization']} ({c['email']})"
        if c["is_lhgi"]:
            label = f"[LHGI] {label}"
        elif c.get("is_mailserver"):
            label = f"[MAIL SERVER] {label}"
        menu_options.append(label)

    # Step 4: Show TUI for selection
    print(f"\nSelect customers to {action} (SPACE to select, ENTER to confirm):\n")

    terminal_menu = TerminalMenu(
        menu_options,
        multi_select=True,
        show_multi_select_hint=True,
        multi_select_select_on_accept=False,
        multi_select_empty_ok=False,
    )

    selected_indices = terminal_menu.show()

    if selected_indices is None or len(selected_indices) == 0:
        log("No customers selected. Exiting.")
        sys.exit(0)

    # Step 5: Confirm selection
    selected_customers = [all_customers[i] for i in selected_indices]
    selected_names = [c["subdomain"].upper() for c in selected_customers]

    print(f"\nYou selected: {', '.join(selected_names)}")
    confirm = input(f"Continue with {action}? [y/N]: ").strip().lower()

    if confirm != "y":
        log(f"{action.title()} cancelled.")
        sys.exit(0)

    # Step 6: Run operations
    print("\n" + "-" * 60)
    results = []

    for customer in selected_customers:
        subdomain = customer["subdomain"].upper()

        if BACKUP_ONLY:
            log(f"Backing up {subdomain}...")
            success, message = backup_customer(customer)
        else:
            log(f"Upgrading {subdomain}...")
            success, message = upgrade_customer(customer)

        results.append({
            "customer": customer,
            "success": success,
            "message": message
        })

        if success:
            log(f"{subdomain}: SUCCESS", "SUCCESS")
        else:
            log(f"{subdomain}: FAILED - {message}", "ERROR")

        print("-" * 60)

    # Step 7: Summary
    summary_title = "BACKUP SUMMARY" if BACKUP_ONLY else "UPGRADE SUMMARY"
    print("\n" + "=" * 60)
    print(f"  {summary_title}")
    print("=" * 60 + "\n")

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    print(f"Total: {len(results)} | Success: {len(successful)} | Failed: {len(failed)}\n")

    if successful and BACKUP_ONLY:
        print("BACKUP DETAILS:")
        for r in successful:
            print(f"  - {r['customer']['subdomain'].upper()}: {r['message']}")
        print()

    if failed:
        fail_label = "FAILED BACKUPS:" if BACKUP_ONLY else "FAILED UPGRADES:"
        print(fail_label)
        for r in failed:
            print(f"  - {r['customer']['subdomain'].upper()}: {r['message'][:100]}")
        print(f"\nCheck logs for details on failures.\n")

    # Step 8: Output emails for notification (skip in backup-only mode)
    if successful and not BACKUP_ONLY:
        emails = [r["customer"]["email"] for r in successful]
        print("SEND NOTIFICATION TO:")
        print(f"  {', '.join(emails)}")
        print()

    # Exit code based on results
    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()

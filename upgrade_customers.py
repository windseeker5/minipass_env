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
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Global dry-run flag
DRY_RUN = False

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

# LHGI hardcoded configuration (not in customers.db)
LHGI_CONFIG = {
    "subdomain": "lhgi",
    "organization": "LHGI",
    "email": "lhgi@jfgoulet.com",
    "is_lhgi": True
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
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_db = f"~/backup_{subdomain}_{timestamp}.db"
    backup_uploads = f"~/backup_{subdomain}_uploads_{timestamp}"

    # Verify customer directory exists
    if not Path(customer_path).exists():
        return False, f"Customer directory not found: {customer_path}"

    steps = [
        ("Backing up database",
         f"cp {app_path}/instance/minipass.db {backup_db}"),

        ("Backing up uploads",
         f"cp -r {app_path}/static/uploads {backup_uploads}"),

        ("Stopping containers",
         f"cd {customer_path} && docker-compose down"),

        ("Fetching and resetting to origin/main",
         f"cd {app_path} && git fetch origin && git reset --hard origin/main && git clean -fd"),

        ("Restoring database backup",
         f"cp {backup_db} {app_path}/instance/minipass.db"),

        ("Restoring uploads backup",
         f"cp -r {backup_uploads}/. {app_path}/static/uploads/"),

        ("Running database migration",
         f"cd {customer_path} && python3 app/migrations/upgrade_production_database.py"),

        ("Building container (no cache)",
         f"cd {customer_path} && docker-compose build --no-cache"),

        ("Starting container",
         f"cd {customer_path} && docker-compose up -d"),
    ]

    for step_name, command in steps:
        log(f"  {step_name}...")
        success, output = run_command(command)
        if not success:
            return False, f"Failed at: {step_name}\n{output}"

    return True, "All steps completed successfully"


def upgrade_customer(customer: dict) -> tuple[bool, str]:
    """Upgrade a single customer based on their type."""
    if customer["is_lhgi"]:
        return upgrade_lhgi()
    else:
        return upgrade_deployed_customer(customer["subdomain"])


def main():
    global DRY_RUN

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Minipass Deployment Automation - Upgrade customer containers"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing any commands"
    )
    args = parser.parse_args()

    DRY_RUN = args.dry_run

    print("\n" + "=" * 60)
    if DRY_RUN:
        print("  Minipass Deployment Automation [DRY-RUN MODE]")
        print("  (No commands will be executed)")
    else:
        print("  Minipass Deployment Automation")
    print("=" * 60 + "\n")

    # Step 1: Get customers from database
    log("Reading customers from database...")
    customers = get_customers_from_db()

    # Step 2: Add LHGI as first entry
    all_customers = [LHGI_CONFIG] + customers

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
        menu_options.append(label)

    # Step 4: Show TUI for selection
    print("\nSelect customers to upgrade (SPACE to select, ENTER to confirm):\n")

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
    confirm = input("Continue with upgrade? [y/N]: ").strip().lower()

    if confirm != "y":
        log("Upgrade cancelled.")
        sys.exit(0)

    # Step 6: Run upgrades
    print("\n" + "-" * 60)
    results = []

    for customer in selected_customers:
        subdomain = customer["subdomain"].upper()
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
    print("\n" + "=" * 60)
    print("  UPGRADE SUMMARY")
    print("=" * 60 + "\n")

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    print(f"Total: {len(results)} | Success: {len(successful)} | Failed: {len(failed)}\n")

    if failed:
        print("FAILED UPGRADES:")
        for r in failed:
            print(f"  - {r['customer']['subdomain'].upper()}: {r['message'][:100]}")
        print("\nCheck logs for details on failed upgrades.\n")

    # Step 8: Output emails for notification
    if successful:
        emails = [r["customer"]["email"] for r in successful]
        print("SEND NOTIFICATION TO:")
        print(f"  {', '.join(emails)}")
        print()

    # Exit code based on results
    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Database Migration: Add Stripe Customer and Subscription IDs

This migration adds Stripe relationship fields to enable recurring subscription management.

New fields:
- stripe_customer_id: Stripe Customer ID (cus_xxx)
- stripe_subscription_id: Stripe Subscription ID (sub_xxx)

Usage:
    python migrations/add_stripe_ids.py
"""

import sqlite3
import shutil
from datetime import datetime
import os

CUSTOMERS_DB = "customers.db"
BACKUP_DB = f"customers_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

def backup_database():
    """Create a backup of the database before migration."""
    if os.path.exists(CUSTOMERS_DB):
        shutil.copy2(CUSTOMERS_DB, BACKUP_DB)
        print(f"✅ Database backed up to: {BACKUP_DB}")
        return True
    else:
        print(f"⚠️  Database {CUSTOMERS_DB} not found. Will be created fresh.")
        return False

def check_column_exists(cursor, table_name, column_name):
    """Check if a column already exists in a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

def add_stripe_id_fields(conn):
    """Add Stripe ID fields to customers table."""
    cur = conn.cursor()

    # Define new columns to add
    new_columns = [
        ("stripe_customer_id", "TEXT"),
        ("stripe_subscription_id", "TEXT"),
    ]

    print("\n📊 Adding Stripe ID columns to customers table...")

    for column_name, column_def in new_columns:
        if not check_column_exists(cur, 'customers', column_name):
            try:
                cur.execute(f"ALTER TABLE customers ADD COLUMN {column_name} {column_def}")
                print(f"   ✅ Added column: {column_name}")
            except sqlite3.OperationalError as e:
                print(f"   ❌ Failed to add {column_name}: {e}")
        else:
            print(f"   ⏭️  Column already exists: {column_name}")

    conn.commit()

def verify_migration(conn):
    """Verify the migration was successful."""
    cur = conn.cursor()

    print("\n🔍 Verifying migration...")

    # Check all new columns exist
    cur.execute("PRAGMA table_info(customers)")
    columns = [row[1] for row in cur.fetchall()]

    required_columns = [
        'stripe_customer_id',
        'stripe_subscription_id'
    ]

    all_present = True
    for col in required_columns:
        if col in columns:
            print(f"   ✅ Column exists: {col}")
        else:
            print(f"   ❌ Column missing: {col}")
            all_present = False

    if all_present:
        print("\n✅ Migration completed successfully!")

        # Show summary
        cur.execute("SELECT COUNT(*) FROM customers")
        total_customers = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM customers WHERE stripe_subscription_id IS NOT NULL")
        with_subscriptions = cur.fetchone()[0]

        print(f"\n📊 Database Summary:")
        print(f"   Total customers: {total_customers}")
        print(f"   Customers with Stripe subscription IDs: {with_subscriptions}")

        return True
    else:
        print("\n❌ Migration failed - some columns are missing")
        return False

def rollback(backup_file):
    """Rollback the migration by restoring from backup."""
    if os.path.exists(backup_file):
        shutil.copy2(backup_file, CUSTOMERS_DB)
        print(f"✅ Database rolled back from: {backup_file}")
        return True
    else:
        print(f"❌ Backup file not found: {backup_file}")
        return False

def main():
    """Main migration function."""
    print("="*60)
    print("  MiniPass Database Migration: Add Stripe IDs")
    print("="*60)

    # Step 1: Backup
    backup_exists = backup_database()

    try:
        # Step 2: Connect to database
        conn = sqlite3.connect(CUSTOMERS_DB)

        # Step 3: Add new columns
        add_stripe_id_fields(conn)

        # Step 4: Verify migration
        success = verify_migration(conn)

        conn.close()

        if success:
            print("\n" + "="*60)
            print("  ✅ Migration Complete!")
            print("="*60)
            if backup_exists:
                print(f"\n💡 Backup saved at: {BACKUP_DB}")
                print(f"   To rollback: mv {BACKUP_DB} {CUSTOMERS_DB}")
            return 0
        else:
            print("\n" + "="*60)
            print("  ❌ Migration Failed")
            print("="*60)
            return 1

    except Exception as e:
        print(f"\n❌ Migration error: {e}")
        print("\nAttempting rollback...")
        if backup_exists:
            rollback(BACKUP_DB)
        return 1

if __name__ == "__main__":
    exit(main())

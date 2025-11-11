#!/usr/bin/env python3
"""
Database Migration: Add Subscription Tracking Fields

This migration adds subscription and billing tracking fields to the customers table.

New fields:
- billing_frequency: 'monthly' or 'annual'
- subscription_start_date: When subscription started
- subscription_end_date: When subscription expires
- stripe_price_id: Stripe Price ID used
- stripe_checkout_session_id: Stripe Checkout Session ID
- payment_amount: Amount paid in cents
- currency: Currency code (default 'cad')
- subscription_status: 'active', 'expired', 'cancelled'

Usage:
    python migrations/add_subscription_tracking.py
"""

import sqlite3
import shutil
from datetime import datetime, timedelta
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

def add_subscription_fields(conn):
    """Add subscription tracking fields to customers table."""
    cur = conn.cursor()

    # Define new columns to add
    new_columns = [
        ("billing_frequency", "TEXT DEFAULT 'monthly'"),
        ("subscription_start_date", "TEXT"),
        ("subscription_end_date", "TEXT"),
        ("stripe_price_id", "TEXT"),
        ("stripe_checkout_session_id", "TEXT"),
        ("payment_amount", "INTEGER"),
        ("currency", "TEXT DEFAULT 'cad'"),
        ("subscription_status", "TEXT DEFAULT 'active'"),
    ]

    print("\n📊 Adding new columns to customers table...")

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

def populate_default_values(conn):
    """Populate default values for existing customers."""
    cur = conn.cursor()

    print("\n📝 Populating default values for existing customers...")

    # Get all existing customers without subscription data
    cur.execute("""
        SELECT id, subdomain, created_at
        FROM customers
        WHERE subscription_start_date IS NULL
    """)

    existing_customers = cur.fetchall()

    if not existing_customers:
        print("   ℹ️  No existing customers to update")
        return

    print(f"   Found {len(existing_customers)} existing customers")

    for customer_id, subdomain, created_at in existing_customers:
        # Calculate default subscription dates
        if created_at:
            start_date = created_at
        else:
            start_date = datetime.now().isoformat()

        # Default to monthly subscription, ending 30 days after creation
        try:
            start_dt = datetime.fromisoformat(start_date)
        except:
            start_dt = datetime.now()

        end_dt = start_dt + timedelta(days=30)
        end_date = end_dt.isoformat()

        # Update customer with default values
        cur.execute("""
            UPDATE customers
            SET billing_frequency = 'monthly',
                subscription_start_date = ?,
                subscription_end_date = ?,
                subscription_status = 'active',
                currency = 'cad'
            WHERE id = ?
        """, (start_date, end_date, customer_id))

        print(f"   ✅ Updated customer: {subdomain}")

    conn.commit()
    print(f"   ✅ Updated {len(existing_customers)} customers with default values")

def verify_migration(conn):
    """Verify the migration was successful."""
    cur = conn.cursor()

    print("\n🔍 Verifying migration...")

    # Check all new columns exist
    cur.execute("PRAGMA table_info(customers)")
    columns = [row[1] for row in cur.fetchall()]

    required_columns = [
        'billing_frequency',
        'subscription_start_date',
        'subscription_end_date',
        'stripe_price_id',
        'stripe_checkout_session_id',
        'payment_amount',
        'currency',
        'subscription_status'
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

        cur.execute("SELECT COUNT(*) FROM customers WHERE subscription_status = 'active'")
        active_customers = cur.fetchone()[0]

        print(f"\n📊 Database Summary:")
        print(f"   Total customers: {total_customers}")
        print(f"   Active subscriptions: {active_customers}")

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
    print("  MiniPass Database Migration: Add Subscription Tracking")
    print("="*60)

    # Step 1: Backup
    backup_exists = backup_database()

    try:
        # Step 2: Connect to database
        conn = sqlite3.connect(CUSTOMERS_DB)

        # Step 3: Add new columns
        add_subscription_fields(conn)

        # Step 4: Populate defaults for existing customers
        populate_default_values(conn)

        # Step 5: Verify migration
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

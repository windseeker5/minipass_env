#!/usr/bin/env python3

import sqlite3
import os
import sys
from datetime import datetime

# Add parent directory to path so we can import customer_helpers
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CUSTOMERS_DB = "customers.db"

def add_organization_name_field():
    """
    Adds organization_name field to the existing customers table.
    """
    print("🔧 Adding organization_name field to customers database...")
    
    with sqlite3.connect(CUSTOMERS_DB) as conn:
        cur = conn.cursor()
        
        # Check if column already exists
        cur.execute("PRAGMA table_info(customers)")
        columns = [column[1] for column in cur.fetchall()]
        
        if "organization_name" not in columns:
            try:
                cur.execute("ALTER TABLE customers ADD COLUMN organization_name TEXT")
                print("✅ Added column: organization_name")
            except sqlite3.OperationalError as e:
                print(f"❌ Failed to add column organization_name: {e}")
        else:
            print("ℹ️  Column organization_name already exists")
        
        conn.commit()
        print("✅ Database migration completed")

def verify_schema():
    """
    Verifies the updated database schema.
    """
    print("\n📊 Verifying database schema...")
    
    with sqlite3.connect(CUSTOMERS_DB) as conn:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(customers)")
        columns = cur.fetchall()
        
        print("\nCurrent table schema:")
        for column in columns:
            cid, name, data_type, not_null, default_val, pk = column
            print(f"  {name}: {data_type}" + 
                  (f" (NOT NULL)" if not_null else "") + 
                  (f" DEFAULT {default_val}" if default_val else "") +
                  (f" PRIMARY KEY" if pk else ""))

if __name__ == "__main__":
    print("🚀 Starting database migration for organization_name field...")
    
    # Check if database exists
    if not os.path.exists(CUSTOMERS_DB):
        print(f"❌ Database {CUSTOMERS_DB} not found. Please run from MinipassWebSite directory.")
        sys.exit(1)
    
    try:
        add_organization_name_field()
        verify_schema()
        print("\n✅ Migration completed successfully!")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
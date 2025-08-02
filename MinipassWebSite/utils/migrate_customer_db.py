#!/usr/bin/env python3
"""
Database migration script to add email-related columns to the customers table.
This fixes the missing email_address column issue.
"""

import sqlite3
import os
from datetime import datetime

CUSTOMERS_DB = "../customers.db"

def get_table_columns(cursor, table_name):
    """Get list of columns in a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]

def migrate_customers_table():
    """Add missing email-related columns to customers table"""
    
    print("🔍 Checking customers table schema...")
    
    # Check if database exists
    if not os.path.exists(CUSTOMERS_DB):
        print(f"❌ Database {CUSTOMERS_DB} not found")
        return False
    
    with sqlite3.connect(CUSTOMERS_DB) as conn:
        cur = conn.cursor()
        
        # Get current columns
        columns = get_table_columns(cur, 'customers')
        print(f"📋 Current columns: {', '.join(columns)}")
        
        # Define the new columns we need
        new_columns = [
            ('email_address', 'TEXT'),
            ('email_password', 'TEXT'),
            ('forwarding_email', 'TEXT'),
            ('email_created', 'TEXT'),
            ('email_status', 'TEXT DEFAULT "pending"'),
            ('organization_name', 'TEXT')
        ]
        
        # Add missing columns
        for column_name, column_type in new_columns:
            if column_name not in columns:
                try:
                    alter_sql = f"ALTER TABLE customers ADD COLUMN {column_name} {column_type}"
                    print(f"➕ Adding column: {column_name}")
                    cur.execute(alter_sql)
                    print(f"✅ Successfully added column: {column_name}")
                except sqlite3.Error as e:
                    print(f"❌ Error adding column {column_name}: {e}")
                    return False
            else:
                print(f"✓ Column {column_name} already exists")
        
        # Verify final schema
        final_columns = get_table_columns(cur, 'customers')
        print(f"📋 Final columns: {', '.join(final_columns)}")
        
        conn.commit()
        print("✅ Database migration completed successfully!")
        return True

def show_table_info():
    """Display current table structure"""
    print("\n" + "="*60)
    print("CUSTOMERS TABLE STRUCTURE")
    print("="*60)
    
    if not os.path.exists(CUSTOMERS_DB):
        print(f"❌ Database {CUSTOMERS_DB} not found")
        return
    
    with sqlite3.connect(CUSTOMERS_DB) as conn:
        cur = conn.cursor()
        
        # Get table info
        cur.execute("PRAGMA table_info(customers)")
        columns = cur.fetchall()
        
        print(f"{'Column':<20} {'Type':<15} {'Null':<8} {'Default':<15}")
        print("-" * 60)
        
        for col in columns:
            col_id, name, col_type, not_null, default_val, pk = col
            null_str = "NO" if not_null else "YES"
            default_str = str(default_val) if default_val is not None else ""
            print(f"{name:<20} {col_type:<15} {null_str:<8} {default_str:<15}")
        
        # Count records
        cur.execute("SELECT COUNT(*) FROM customers")
        count = cur.fetchone()[0]
        print(f"\nTotal records: {count}")

if __name__ == "__main__":
    print("🚀 Starting customers database migration...")
    
    # Show current structure
    show_table_info()
    
    # Perform migration
    success = migrate_customers_table()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        # Show updated structure
        show_table_info()
    else:
        print("\n💥 Migration failed!")
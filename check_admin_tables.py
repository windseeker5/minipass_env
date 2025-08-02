#!/usr/bin/env python3

import sqlite3
import bcrypt

def check_admin_tables():
    db_path = "/home/kdresdell/minipass_env/deployed/kiteguru/app/instance/minipass.db"
    email = "kdresdell@gmail.com"
    password = "ci_wp6drHtsa1G5T"
    
    print("🔍 Checking both Admin and admin tables")
    print("=" * 50)
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Check uppercase Admin table
    print("📋 Checking 'Admin' table (uppercase):")
    try:
        cur.execute("SELECT id, email, password_hash FROM Admin")
        admin_records = cur.fetchall()
        print(f"   Found {len(admin_records)} records in Admin table:")
        for record in admin_records:
            admin_id, admin_email, password_hash = record
            print(f"   ID: {admin_id}, Email: {admin_email}")
            
            # Test password against uppercase Admin table
            if bcrypt.checkpw(password.encode(), password_hash):
                print("   ✅ Password matches in Admin table!")
            else:
                print("   ❌ Password does not match in Admin table")
    except Exception as e:
        print(f"   ❌ Error with Admin table: {e}")
    
    print()
    
    # Check lowercase admin table  
    print("📋 Checking 'admin' table (lowercase):")
    try:
        cur.execute("SELECT id, email, password_hash FROM admin")
        admin_records = cur.fetchall()
        print(f"   Found {len(admin_records)} records in admin table:")
        for record in admin_records:
            admin_id, admin_email, password_hash = record
            print(f"   ID: {admin_id}, Email: {admin_email}")
            
            # Test password against lowercase admin table
            if isinstance(password_hash, str):
                # If it's a string, we need to check if it's a bcrypt hash or plain text
                if password_hash.startswith('$2b$') or password_hash.startswith('$2a$'):
                    # It's a bcrypt hash
                    if bcrypt.checkpw(password.encode(), password_hash.encode()):
                        print("   ✅ Password matches in admin table (bcrypt)!")
                    else:
                        print("   ❌ Password does not match in admin table (bcrypt)")
                else:
                    # It might be plain text
                    if password_hash == password:
                        print("   ✅ Password matches in admin table (plain text)!")
                    else:
                        print("   ❌ Password does not match in admin table (plain text)")
            else:
                # It's bytes (binary)
                if bcrypt.checkpw(password.encode(), password_hash):
                    print("   ✅ Password matches in admin table (binary bcrypt)!")
                else:
                    print("   ❌ Password does not match in admin table (binary bcrypt)")
                    
    except Exception as e:
        print(f"   ❌ Error with admin table: {e}")
    
    conn.close()
    
    print()
    print("🔧 SOLUTION:")
    print("The deployment script creates 'Admin' table (uppercase)")
    print("But the app uses 'admin' table (lowercase)")
    print("We need to copy the admin user from 'Admin' to 'admin' table")

if __name__ == "__main__":
    check_admin_tables()
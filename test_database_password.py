#!/usr/bin/env python3

import sqlite3
import bcrypt
import sys
import os

def test_database_password(db_path, email, password):
    """
    Test if the password matches what's stored in the database
    
    Args:
        db_path (str): Path to the database file
        email (str): Admin email to check
        password (str): Password to verify
    """
    print(f"🔍 Testing database: {db_path}")
    print(f"📧 Email: {email}")
    print(f"🔐 Password: {password}")
    print("=" * 60)
    
    # Check if database file exists
    if not os.path.exists(db_path):
        print(f"❌ Database file does not exist: {db_path}")
        return False
    
    print(f"✅ Database file exists: {db_path}")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # Check if Admin table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Admin';")
        admin_table = cur.fetchone()
        
        if not admin_table:
            print("❌ Admin table does not exist in database")
            conn.close()
            return False
        
        print("✅ Admin table exists")
        
        # Get all admin users
        cur.execute("SELECT id, email, password_hash FROM Admin")
        admins = cur.fetchall()
        
        print(f"📊 Found {len(admins)} admin user(s) in database:")
        for admin_id, admin_email, password_hash in admins:
            print(f"   ID: {admin_id}, Email: {admin_email}")
        
        # Find the specific admin user
        cur.execute("SELECT password_hash FROM Admin WHERE email = ?", (email,))
        result = cur.fetchone()
        
        if not result:
            print(f"❌ Admin user '{email}' not found in database")
            conn.close()
            return False
        
        print(f"✅ Admin user '{email}' found in database")
        
        # Get the stored password hash
        stored_hash = result[0]
        print(f"🔑 Stored password hash: {stored_hash[:50]}... (truncated)")
        
        # Test the password
        if bcrypt.checkpw(password.encode(), stored_hash):
            print("✅ PASSWORD MATCHES! The password is correct.")
            conn.close()
            return True
        else:
            print("❌ PASSWORD MISMATCH! The password does not match.")
            
            # Let's also test what hash the current password would generate
            print("\n🧪 Testing password hashing:")
            test_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
            print(f"🔐 New hash would be: {test_hash[:50]}... (truncated)")
            
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Error testing database: {str(e)}")
        return False

def inspect_database_structure(db_path):
    """
    Inspect the database structure and contents
    """
    print(f"\n🔬 Inspecting database structure: {db_path}")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # Get all tables
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cur.fetchall()
        
        print(f"📋 Tables in database: {len(tables)}")
        for table in tables:
            table_name = table[0]
            print(f"   📄 Table: {table_name}")
            
            # Get table schema
            cur.execute(f"PRAGMA table_info({table_name});")
            columns = cur.fetchall()
            
            for col in columns:
                col_id, col_name, col_type, not_null, default, pk = col
                print(f"      🔸 {col_name} ({col_type})")
            
            # Get row count
            cur.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cur.fetchone()[0]
            print(f"      📊 Rows: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error inspecting database: {str(e)}")

if __name__ == "__main__":
    # Test the kiteguru database
    db_path = "/home/kdresdell/minipass_env/deployed/kiteguru/app/instance/minipass.db"
    email = "kdresdell@gmail.com"
    password = "ci_wp6drHtsa1G5T"
    
    print("🧪 MiniPass Database Password Tester")
    print("=" * 60)
    
    # Inspect database structure first
    inspect_database_structure(db_path)
    
    # Test the password
    print()
    success = test_database_password(db_path, email, password)
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 RESULT: Database password verification PASSED")
        print("💡 The issue is likely NOT with the database password.")
        print("🔍 Check container logs or application configuration.")
    else:
        print("❌ RESULT: Database password verification FAILED")
        print("💡 The issue might be with password storage or hashing.")
        print("🔧 Consider regenerating the admin user.")
    
    print("\n📚 Additional debugging commands:")
    print(f"   docker logs minipass_kiteguru")
    print(f"   docker exec -it minipass_kiteguru /bin/bash")
    print(f"   docker ps --filter name=minipass_kiteguru")
#!/usr/bin/env python3
"""
Migration Script: Pass to Passport System
Migrates users with remaining games from old pass system to new passport system
Author: MiniPass Migration Tool
Date: 2025-01-24
"""

import sqlite3
import sys
import csv
from datetime import datetime
import random
import string
from pathlib import Path


class PassToPassportMigrator:
    """Handles migration from old pass system to new passport system"""
    
    def __init__(self, old_db_path, new_db_path, activity_id, passport_type_id, dry_run=False):
        """
        Initialize migrator with database paths and target IDs
        
        Args:
            old_db_path: Path to old database with pass table
            new_db_path: Path to new database with passport system
            activity_id: ID of pre-created activity in new system
            passport_type_id: ID of pre-created passport type
            dry_run: If True, don't commit changes (preview only)
        """
        self.old_db_path = old_db_path
        self.new_db_path = new_db_path
        self.activity_id = activity_id
        self.passport_type_id = passport_type_id
        self.dry_run = dry_run
        
        # Track migration results
        self.migration_log = []
        self.error_log = []
        self.user_mapping = {}  # old_email -> new_user_id
        
    def connect_databases(self):
        """Establish connections to both databases"""
        try:
            self.old_conn = sqlite3.connect(self.old_db_path)
            self.old_conn.row_factory = sqlite3.Row
            self.new_conn = sqlite3.connect(self.new_db_path)
            self.new_conn.row_factory = sqlite3.Row
            print(f"✓ Connected to databases")
            return True
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            return False
    
    def close_databases(self):
        """Close database connections"""
        if hasattr(self, 'old_conn'):
            self.old_conn.close()
        if hasattr(self, 'new_conn'):
            self.new_conn.close()
    
    def generate_pass_code(self):
        """Generate a unique pass code for new passport"""
        # Format: MP-XXXX-XXXX (MP for MiniPass)
        chars = string.ascii_uppercase + string.digits
        code = f"MP-{''.join(random.choices(chars, k=4))}-{''.join(random.choices(chars, k=4))}"
        return code
    
    def get_passes_to_migrate(self):
        """Fetch all passes with remaining games from old database"""
        cursor = self.old_conn.cursor()
        query = """
            SELECT 
                id,
                pass_code,
                user_name,
                user_email,
                phone_number,
                games_remaining,
                sold_amt,
                paid_ind,
                paid_date,
                activity,
                notes
            FROM pass
            WHERE games_remaining > 0
            ORDER BY games_remaining DESC, user_name
        """
        cursor.execute(query)
        passes = cursor.fetchall()
        print(f"✓ Found {len(passes)} passes with remaining games")
        return passes
    
    def create_user(self, pass_data):
        """Create a new user in the new database"""
        cursor = self.new_conn.cursor()
        
        # Normalize email to lowercase
        email = pass_data['user_email'].lower() if pass_data['user_email'] else None
        
        insert_query = """
            INSERT INTO user (name, email, phone_number)
            VALUES (?, ?, ?)
        """
        
        if self.dry_run:
            print(f"  [DRY RUN] Would create user: {pass_data['user_name']}")
            return None
        
        try:
            cursor.execute(insert_query, (
                pass_data['user_name'],
                email,
                pass_data['phone_number']
            ))
            user_id = cursor.lastrowid
            self.user_mapping[email] = user_id
            return user_id
        except Exception as e:
            self.error_log.append(f"Failed to create user {pass_data['user_name']}: {e}")
            return None
    
    def create_passport(self, pass_data, user_id):
        """Create a new passport in the new database"""
        cursor = self.new_conn.cursor()
        
        # Generate new pass code
        new_pass_code = self.generate_pass_code()
        
        # Create migration note
        migration_note = f"Migrated from 2024-2025 season. Had {pass_data['games_remaining']} uses remaining."
        if pass_data['notes']:
            migration_note += f" Original notes: {pass_data['notes']}"
        
        insert_query = """
            INSERT INTO passport (
                pass_code,
                user_id,
                activity_id,
                passport_type_id,
                passport_type_name,
                uses_remaining,
                sold_amt,
                paid,
                paid_date,
                created_dt,
                notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        if self.dry_run:
            print(f"  [DRY RUN] Would create passport: {new_pass_code} with {pass_data['games_remaining']} uses")
            return new_pass_code
        
        try:
            cursor.execute(insert_query, (
                new_pass_code,
                user_id,
                self.activity_id,
                self.passport_type_id,
                "Remplacant",  # Hardcoded as specified
                pass_data['games_remaining'],
                pass_data['sold_amt'] or 0.0,
                bool(pass_data['paid_ind']),
                pass_data['paid_date'],
                datetime.now(),
                migration_note
            ))
            return new_pass_code
        except Exception as e:
            self.error_log.append(f"Failed to create passport for user_id {user_id}: {e}")
            return None
    
    def migrate(self):
        """Execute the migration process"""
        print("\n" + "="*60)
        print("STARTING MIGRATION PROCESS")
        print("="*60)
        
        if self.dry_run:
            print("🔍 DRY RUN MODE - No changes will be saved")
        else:
            print("⚡ LIVE MODE - Changes will be committed")
        
        # Connect to databases
        if not self.connect_databases():
            return False
        
        # Get passes to migrate
        passes = self.get_passes_to_migrate()
        
        if not passes:
            print("No passes to migrate!")
            return True
        
        # Summary statistics
        total_games = sum(p['games_remaining'] for p in passes)
        print(f"Total games to preserve: {total_games}")
        print("-" * 60)
        
        # Migrate each pass
        success_count = 0
        for i, pass_data in enumerate(passes, 1):
            print(f"\n[{i}/{len(passes)}] Processing: {pass_data['user_name']}")
            
            # Create user
            user_id = self.create_user(pass_data)
            if not user_id and not self.dry_run:
                print(f"  ✗ Failed to create user")
                continue
            
            # Create passport
            new_pass_code = self.create_passport(pass_data, user_id)
            if not new_pass_code and not self.dry_run:
                print(f"  ✗ Failed to create passport")
                continue
            
            # Log successful migration
            self.migration_log.append({
                'old_pass_code': pass_data['pass_code'],
                'new_pass_code': new_pass_code,
                'user_name': pass_data['user_name'],
                'user_email': pass_data['user_email'],
                'games_remaining': pass_data['games_remaining'],
                'amount_paid': pass_data['sold_amt']
            })
            
            success_count += 1
            print(f"  ✓ Migrated: {pass_data['games_remaining']} uses remaining")
        
        # Commit or rollback
        if not self.dry_run:
            if success_count == len(passes):
                self.new_conn.commit()
                print(f"\n✓ MIGRATION SUCCESSFUL: {success_count}/{len(passes)} passes migrated")
            else:
                self.new_conn.rollback()
                print(f"\n✗ MIGRATION FAILED: Only {success_count}/{len(passes)} successful, rolled back")
                return False
        else:
            print(f"\n✓ DRY RUN COMPLETE: Would migrate {success_count}/{len(passes)} passes")
        
        # Close connections
        self.close_databases()
        
        return True
    
    def validate_migration(self):
        """Run validation queries to verify migration success"""
        if self.dry_run:
            print("\nSkipping validation in dry run mode")
            return
        
        print("\n" + "="*60)
        print("VALIDATION RESULTS")
        print("="*60)
        
        conn = sqlite3.connect(self.new_db_path)
        cursor = conn.cursor()
        
        # Check counts
        cursor.execute("SELECT COUNT(*) FROM user")
        user_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM passport")
        passport_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(uses_remaining) FROM passport")
        total_uses = cursor.fetchone()[0] or 0
        
        print(f"Users created: {user_count}")
        print(f"Passports created: {passport_count}")
        print(f"Total uses remaining: {total_uses}")
        
        # List all migrated users
        cursor.execute("""
            SELECT u.name, u.email, p.uses_remaining, p.pass_code
            FROM user u
            JOIN passport p ON u.id = p.user_id
            ORDER BY p.uses_remaining DESC
        """)
        
        print("\nMigrated Users:")
        print("-" * 60)
        for row in cursor.fetchall():
            print(f"{row[0]:30} | {row[2]} uses | {row[3]}")
        
        conn.close()
    
    def save_migration_report(self, output_path="migration_report.csv"):
        """Save migration report to CSV file"""
        if not self.migration_log:
            print("No migration data to save")
            return
        
        output_file = Path(output_path)
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['old_pass_code', 'new_pass_code', 'user_name', 
                         'user_email', 'games_remaining', 'amount_paid']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.migration_log)
        
        print(f"\n✓ Migration report saved to: {output_file.absolute()}")
        
        # Save error log if any
        if self.error_log:
            error_file = output_file.parent / "migration_errors.txt"
            with open(error_file, 'w') as f:
                f.write('\n'.join(self.error_log))
            print(f"✗ Errors logged to: {error_file.absolute()}")


def main():
    """Main execution function"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║     MiniPass Migration Tool: Pass → Passport System     ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Configuration
    OLD_DB = "lhgi_prod_database_backup_20250824_021538.db"
    NEW_DB = "instance/minipass.db"
    
    # Check if databases exist
    if not Path(OLD_DB).exists():
        print(f"✗ Old database not found: {OLD_DB}")
        sys.exit(1)
    
    if not Path(NEW_DB).exists():
        print(f"✗ New database not found: {NEW_DB}")
        sys.exit(1)
    
    # Get configuration from user
    print("Please ensure you have:")
    print("1. Flushed/cleared the new database")
    print("2. Created the activity: 'Hockey du midi LHGI - 2025 / 2026'")
    print("3. Created the passport type: 'Remplacant'")
    print()
    
    try:
        activity_id = int(input("Enter the Activity ID (probably 1): ") or "1")
        passport_type_id = int(input("Enter the Passport Type ID (probably 1): ") or "1")
        
        # Ask for dry run
        dry_run_input = input("\nDo a dry run first? (recommended) [Y/n]: ").lower()
        dry_run = dry_run_input != 'n'
        
    except ValueError:
        print("✗ Invalid input. Please enter numeric IDs.")
        sys.exit(1)
    
    # Create migrator and run
    migrator = PassToPassportMigrator(
        OLD_DB, 
        NEW_DB, 
        activity_id, 
        passport_type_id,
        dry_run=dry_run
    )
    
    # Execute migration
    success = migrator.migrate()
    
    if success:
        # Run validation
        migrator.validate_migration()
        
        # Save report
        if not dry_run:
            migrator.save_migration_report("test/migration_report.csv")
        
        # If it was a dry run, offer to run for real
        if dry_run:
            print("\n" + "="*60)
            real_run = input("Dry run complete. Run the actual migration now? [y/N]: ").lower()
            if real_run == 'y':
                print("\nExecuting REAL migration...")
                migrator_real = PassToPassportMigrator(
                    OLD_DB, 
                    NEW_DB, 
                    activity_id, 
                    passport_type_id,
                    dry_run=False
                )
                if migrator_real.migrate():
                    migrator_real.validate_migration()
                    migrator_real.save_migration_report("test/migration_report.csv")
    else:
        print("\n✗ Migration failed. Check error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3

import os
import subprocess
import pyfiglet

# Configuration
MAILSERVER = "mailserver"
DOMAIN = "minipass.me"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
FORWARD_DIR = os.path.join(PARENT_DIR, "config", "user-patches")

def get_active_accounts():
    """Get all active email accounts from mail server"""
    try:
        output = subprocess.check_output([
            "docker", "exec", MAILSERVER,
            "bash", "-c",
            "grep -vE '^#|^$' /tmp/docker-mailserver/postfix-accounts.cf"
        ]).decode().strip()
        return sorted(set(line.split("|")[0] for line in output.splitlines()))
    except Exception as e:
        print(f"❌ Error getting active accounts: {e}")
        return []

def get_mailbox_directories():
    """Get all mailbox directories that exist on disk"""
    try:
        result = subprocess.run([
            "docker", "exec", MAILSERVER,
            "ls", "-1", f"/var/mail/{DOMAIN}/"
        ], capture_output=True, text=True, check=False)

        if result.returncode == 0:
            return sorted([f"{name}@{DOMAIN}" for name in result.stdout.strip().split('\n') if name.strip()])
        return []
    except Exception as e:
        print(f"❌ Error getting mailbox directories: {e}")
        return []

def list_all_mailboxes():
    """Show comprehensive mailbox status - both accounts and directories"""
    print("\n📬 Complete Mailbox Analysis\n")

    active_accounts = get_active_accounts()
    mailbox_dirs = get_mailbox_directories()

    # Find different categories
    active_with_dirs = [acc for acc in active_accounts if acc in mailbox_dirs]
    orphaned_dirs = [dir for dir in mailbox_dirs if dir not in active_accounts]
    accounts_without_dirs = [acc for acc in active_accounts if acc not in mailbox_dirs]

    print(f"{'Status':<12} {'Email':<35} {'Type':<15}")
    print("=" * 65)

    # Active accounts with directories (healthy)
    for email in active_with_dirs:
        app_type = "🐳 MiniPass App" if "_app@" in email else "👤 Regular User"
        print(f"{'✅ Active':<12} {email:<35} {app_type:<15}")

    # Orphaned directories (problematic)
    for email in orphaned_dirs:
        app_type = "🐳 MiniPass App" if "_app@" in email else "👤 Regular User"
        print(f"{'⚠️  Orphaned':<12} {email:<35} {app_type:<15}")

    # Accounts without directories (unusual)
    for email in accounts_without_dirs:
        app_type = "🐳 MiniPass App" if "_app@" in email else "👤 Regular User"
        print(f"{'🔍 No Dir':<12} {email:<35} {app_type:<15}")

    print(f"\n📊 Summary:")
    print(f"   ✅ Active accounts with directories: {len(active_with_dirs)}")
    print(f"   ⚠️  Orphaned directories: {len(orphaned_dirs)}")
    print(f"   🔍 Accounts without directories: {len(accounts_without_dirs)}")

    if orphaned_dirs:
        print(f"\n💡 Orphaned directories are leftover from incomplete deletions")

    return {
        'active_accounts': active_accounts,
        'mailbox_dirs': mailbox_dirs,
        'orphaned_dirs': orphaned_dirs
    }

def delete_mailbox_completely(email):
    """Completely delete a mailbox (account + directory + forward config)"""
    print(f"\n🗑️ Completely deleting mailbox: {email}")

    success = True

    # 1. Delete email account from mail server
    try:
        print("   📧 Deleting email account...")
        result = subprocess.run([
            "docker", "exec", MAILSERVER,
            "setup", "email", "del", "-y", email
        ], capture_output=True, text=True, check=False)

        if result.returncode == 0:
            print("   ✅ Email account deleted")
        else:
            print(f"   ⚠️ Email account warning: {result.stderr.strip() or 'Already deleted'}")
    except Exception as e:
        print(f"   ❌ Error deleting email account: {e}")
        success = False

    # 2. Delete mailbox directory
    try:
        local_part = email.split("@")[0]
        inbox_path = f"/var/mail/{DOMAIN}/{local_part}"
        print("   📁 Deleting mailbox directory...")

        result = subprocess.run([
            "docker", "exec", MAILSERVER,
            "rm", "-rf", inbox_path
        ], capture_output=True, text=True, check=False)

        if result.returncode == 0:
            print("   ✅ Mailbox directory deleted")
        else:
            print(f"   ⚠️ Mailbox directory warning: {result.stderr.strip() or 'Already gone'}")
    except Exception as e:
        print(f"   ❌ Error deleting mailbox directory: {e}")
        success = False

    # 3. Delete forward configuration
    try:
        local_forward_dir = os.path.join(FORWARD_DIR, email)
        if os.path.exists(local_forward_dir):
            print("   🔧 Deleting forward configuration...")
            import shutil
            shutil.rmtree(local_forward_dir)
            print("   ✅ Forward configuration deleted")
        else:
            print("   ℹ️ No forward configuration found")
    except Exception as e:
        print(f"   ❌ Error deleting forward config: {e}")
        success = False

    # 4. Validate complete deletion
    print("   🔍 Validating deletion...")

    # Check if account still exists
    try:
        result = subprocess.run([
            "docker", "exec", MAILSERVER,
            "grep", "-i", email,
            "/tmp/docker-mailserver/postfix-accounts.cf"
        ], capture_output=True, text=True, check=False)

        if result.stdout.strip():
            print(f"   ❌ Account still in postfix-accounts.cf")
            success = False
        else:
            print("   ✅ Account removed from mail server")
    except:
        pass

    # Check if directory still exists
    try:
        local_part = email.split("@")[0]
        result = subprocess.run([
            "docker", "exec", MAILSERVER,
            "ls", f"/var/mail/{DOMAIN}/{local_part}"
        ], capture_output=True, text=True, check=False)

        if "No such file" in result.stderr or result.returncode != 0:
            print("   ✅ Mailbox directory confirmed gone")
        else:
            print(f"   ❌ Mailbox directory still exists")
            success = False
    except:
        pass

    if success:
        print(f"\n✅ {email} completely deleted!")
    else:
        print(f"\n⚠️ {email} deletion completed with warnings")

    return success

def cleanup_orphaned_directories():
    """Clean up all orphaned mailbox directories"""
    print("\n🧹 Cleaning up orphaned mailbox directories...")

    data = list_all_mailboxes()
    orphaned = data['orphaned_dirs']

    if not orphaned:
        print("\n✅ No orphaned directories found!")
        return

    print(f"\n⚠️ Found {len(orphaned)} orphaned directories:")
    for i, email in enumerate(orphaned, 1):
        app_type = "🐳" if "_app@" in email else "👤"
        print(f"  {i}. {app_type} {email}")

    confirm = input(f"\n❗ Delete ALL {len(orphaned)} orphaned directories? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Aborted.")
        return

    success_count = 0
    for email in orphaned:
        print(f"\n🗑️ Deleting orphaned directory: {email}")
        if delete_mailbox_completely(email):
            success_count += 1

    print(f"\n📊 Cleanup completed: {success_count}/{len(orphaned)} successfully deleted")

def delete_specific_mailbox():
    """Delete a specific mailbox chosen by user"""
    data = list_all_mailboxes()
    all_mailboxes = sorted(set(data['active_accounts'] + data['mailbox_dirs']))

    if not all_mailboxes:
        print("\n ℹ️ No mailboxes found!")
        return

    print(f"\n🎯 Select mailbox to delete:")
    for i, email in enumerate(all_mailboxes, 1):
        status = "✅ Active" if email in data['active_accounts'] else "⚠️ Orphaned"
        app_type = "🐳" if "_app@" in email else "👤"
        print(f"  {i:2d}. {status} {app_type} {email}")

    try:
        choice = int(input(f"\nEnter number (1-{len(all_mailboxes)}): "))
        if 1 <= choice <= len(all_mailboxes):
            selected_email = all_mailboxes[choice - 1]

            print(f"\n⚠️ You are about to COMPLETELY DELETE:")
            print(f"   📧 {selected_email}")
            print(f"   📁 All mailbox data")
            print(f"   🔧 Forward configuration")

            confirm = input(f"\n❗ Type 'DELETE {selected_email.split('@')[0]}' to confirm: ")
            expected = f"DELETE {selected_email.split('@')[0]}"

            if confirm == expected:
                delete_mailbox_completely(selected_email)
            else:
                print("❌ Aborted.")
        else:
            print("❌ Invalid choice.")
    except ValueError:
        print("❌ Invalid number.")

def show_menu():
    """Display the simplified menu"""
    title = pyfiglet.figlet_format("simple mail", font="small")
    print(title)
    print("  1. 📋 List all mailboxes (active + orphaned)")
    print("  2. 🗑️  Delete specific mailbox completely")
    print("  3. 🧹 Clean up ALL orphaned directories")
    print("  4. ❌ Exit")
    print()

def main():
    """Main program loop"""
    while True:
        show_menu()

        try:
            choice = input("Choose option (1-4): ").strip()

            if choice == '1':
                list_all_mailboxes()

            elif choice == '2':
                delete_specific_mailbox()

            elif choice == '3':
                cleanup_orphaned_directories()

            elif choice == '4':
                print("👋 Goodbye!")
                break

            else:
                print("❌ Invalid choice. Please enter 1-4.")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
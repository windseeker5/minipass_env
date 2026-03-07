#!/usr/bin/env python3

import os
import subprocess
import getpass
import shutil
import pyfiglet

# Get the parent directory (minipass_env) from the current script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)

MAILSERVER = "mailserver"
DOMAIN = "minipass.me"
USER_BASE_DIR = f"/var/mail/{DOMAIN}"
LOCAL_SIEVE_BASE = os.path.join(PARENT_DIR, "config", "user-patches")
FORWARD_DIR = os.path.join(PARENT_DIR, "config", "user-patches")

def is_minipass_app_email(email):
    """Check if email is a minipass app email and return appropriate prefix"""
    return "🐳 " if "_app@minipass.me" in email else ""

def list_mail_users():
    print("\n📬 Mail Users:\n")
    output = subprocess.check_output([
        "docker", "exec", MAILSERVER,
        "bash", "-c",
        "grep -vE '^#|^$' /tmp/docker-mailserver/postfix-accounts.cf"
    ]).decode().strip()
    users = sorted(set(line.split("|")[0] for line in output.splitlines()))
    for user in users:
        prefix = is_minipass_app_email(user)
        print(f" - {prefix}{user}")

def old_list_forwards():
    print("\n📤 Users with Forwarding Enabled:\n")
    for user_folder in os.listdir(LOCAL_SIEVE_BASE):
        sieve_path = os.path.join(LOCAL_SIEVE_BASE, user_folder, "sieve", "forward.sieve")
        if os.path.exists(sieve_path):
            with open(sieve_path) as f:
                content = f.read()
                if "redirect" in content:
                    parts = content.split('"')
                    if len(parts) >= 2:
                        target = parts[1]
                        print(f" - {user_folder} ➡️ {target}")



def list_forwards():
    print("\n📤 Users with Forwarding Enabled:\n")
    for user_folder in os.listdir(LOCAL_SIEVE_BASE):
        sieve_path = os.path.join(LOCAL_SIEVE_BASE, user_folder, "sieve", "forward.sieve")
        if os.path.exists(sieve_path):
            with open(sieve_path) as f:
                for line in f:
                    if "redirect" in line and '"' in line:
                        target = line.split('"')[1]
                        prefix = is_minipass_app_email(user_folder)
                        print(f" - {prefix}{user_folder} ➡️ {target}")
                        break


 


def create_user():
    email = input("Enter new email (e.g. user@minipass.me): ").strip()
    password = getpass.getpass("Enter password: ")
    subprocess.run([
        "docker", "exec", MAILSERVER,
        "addmailuser", email, password
    ], check=True)
    
    choice = input("Add a forwarding address? (y/n): ").strip().lower()
    if choice == "y":
        forward_to = input("Forward to which email?: ").strip()
        write_forward_sieve(email, forward_to)
        activate_forward_in_container(email)  # This will restart the mailserver
    else:
        # Even without forwarding, restart mailserver to ensure new user is properly loaded
        restart_mailserver()
    
    print("✅ User creation complete.\n")



def add_forward_to_existing_user():
    email = input("Enter existing email to add forward to: ").strip()
    forward_to = input("Forward to which email?: ").strip()
    write_forward_sieve(email, forward_to)
    activate_forward_in_container(email)
    print("✅ Forwarding rule added.\n")




def delete_forward():
    email = input("Enter email to remove forward from: ").strip()
    sieve_path = os.path.join(LOCAL_SIEVE_BASE, email, "sieve", "forward.sieve")
    if os.path.exists(sieve_path):
        os.remove(sieve_path)
        print("🗑️ Local forward.sieve deleted.")
        subprocess.run([
            "docker", "exec", MAILSERVER,
            "rm", f"/var/mail/{DOMAIN}/{email.split('@')[0]}/home/sieve/forward.sieve"
        ], stderr=subprocess.DEVNULL)
    subprocess.run([
        "docker", "exec", MAILSERVER,
        "rm", f"/var/mail/{DOMAIN}/{email.split('@')[0]}/home/.dovecot.sieve"
    ], stderr=subprocess.DEVNULL)
    print("❌ Forward removed.\n")



def delete_user():
    email = input("Enter full email to delete: ").strip()
    subprocess.run([
        "docker", "exec", MAILSERVER,
        "delmailuser", email
    ], check=True)
    print("❌ Mail user deleted.\n")



def delete_user_inbox():
    email = input("Enter email to purge inbox: ").strip()
    local_part = email.split("@")[0]
    maildir = f"{USER_BASE_DIR}/{local_part}/Maildir"
    subprocess.run([
        "docker", "exec", MAILSERVER,
        "rm", "-rf", f"{maildir}/cur", f"{maildir}/new"
    ])
    print("🧹 Inbox purged.\n")



def hard_delete_user():
    email = input("Enter the email of the user to hard delete: ").strip()
    confirm = input(f"⚠️ Are you sure you want to permanently delete {email}? This will remove the user, inbox, and forward config. (y/n): ").lower()
    if confirm != 'y':
        print("❌ Cancelled.")
        return

    try:
        print("🗑️ Deleting user...")
        subprocess.run([
            "docker", "exec", MAILSERVER,
            "setup", "email", "del", "-y", email
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to delete user: {e}")

    try:
        local_forward_dir = os.path.join(FORWARD_DIR, email)
        if os.path.exists(local_forward_dir):
            shutil.rmtree(local_forward_dir)
            print("🧹 Forward config deleted.")
        else:
            print("ℹ️ No forward config found.")
    except Exception as e:
        print(f"❌ Failed to delete forward config: {e}")

    try:
        inbox_path = f"/var/mail/{DOMAIN}/{email.split('@')[0]}"
        result = subprocess.run([
            "docker", "exec", MAILSERVER,
            "rm", "-rf", inbox_path
        ], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Failed to delete inbox path: {inbox_path}")
            print(result.stderr)
        else:
            print("📭 Mail inbox data deleted.")
    except Exception as e:
        print(f"❌ Error deleting inbox: {e}")

    validate_user_deletion(email)



def validate_user_deletion(email):
    print("\n🔍 Validating deletion...")

    # Check user
    result = subprocess.run([
        "docker", "exec", MAILSERVER,
        "grep", "-i", email,
        "/tmp/docker-mailserver/postfix-accounts.cf"
    ], capture_output=True, text=True)
    if result.stdout.strip():
        print(f"❌ User still exists in postfix-accounts.cf: {result.stdout.strip()}")
    else:
        print("✅ User is removed from postfix-accounts.cf")

    # Check mailbox folder
    local_part = email.split("@")[0]
    result = subprocess.run([
        "docker", "exec", MAILSERVER,
        "ls", f"/var/mail/{DOMAIN}/{local_part}"
    ], capture_output=True, text=True)
    if "No such file" in result.stderr:
        print("✅ Mailbox directory is gone.")
    else:
        print(f"❌ Mailbox directory still exists: {result.stdout.strip()}")

    # Check sieve and forward rules
    result = subprocess.run([
        "docker", "exec", MAILSERVER,
        "find", f"/var/mail/{DOMAIN}/", "-name", "forward.sieve"
    ], capture_output=True, text=True)
    if email.split("@")[0] in result.stdout:
        print("❌ forward.sieve still present.")
    else:
        print("✅ forward.sieve is removed.")

    result = subprocess.run([
        "docker", "exec", MAILSERVER,
        "find", f"/var/mail/{DOMAIN}/", "-name", ".dovecot.sieve"
    ], capture_output=True, text=True)
    if email.split("@")[0] in result.stdout:
        print("❌ .dovecot.sieve still present.")
    else:
        print("✅ .dovecot.sieve is removed.")



def write_forward_sieve(email, forward_to):
    path = os.path.join(LOCAL_SIEVE_BASE, email, "sieve")
    os.makedirs(path, exist_ok=True)
    forward_script = 'require ["fileinto", "copy"];\nredirect :copy "{}";\n'.format(forward_to)
    with open(os.path.join(path, "forward.sieve"), "w") as f:
        f.write(forward_script)
    print(f"📁 Forward config written to: {os.path.join(path, 'forward.sieve')}")



def restart_mailserver():
    """Restart the mailserver container to reload configuration"""
    print("🔄 Restarting mailserver to reload configuration...")
    try:
        subprocess.run(["docker", "restart", MAILSERVER], check=True)
        print("✅ Mailserver restarted successfully.")
        print("⏳ Waiting 10 seconds for mailserver to fully start...")
        import time
        time.sleep(10)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to restart mailserver: {e}")
        raise

def activate_forward_in_container(email):
    local_part = email.split("@")[0]
    local_path = os.path.join(LOCAL_SIEVE_BASE, email, "sieve", "forward.sieve")
    container_home = f"/var/mail/{DOMAIN}/{local_part}/home"
    container_sieve_dir = f"{container_home}/sieve"
    print("🔄 Activating forward inside container...")
    subprocess.run(["docker", "exec", MAILSERVER, "mkdir", "-p", container_sieve_dir], check=True)
    subprocess.run(["docker", "cp", local_path, f"{MAILSERVER}:{container_sieve_dir}/forward.sieve"], check=True)
    subprocess.run(["docker", "exec", MAILSERVER, "chown", "-R", "docker:docker", container_home], check=True)
    subprocess.run([
        "docker", "exec", MAILSERVER,
        "doveadm", "sieve", "put", "-u", email, "forward", f"{container_sieve_dir}/forward.sieve"
    ], check=True)
    subprocess.run([
        "docker", "exec", MAILSERVER,
        "doveadm", "sieve", "activate", "-u", email, "forward"
    ], check=True)
    print("✅ Forwarding activated.")
    
    # Restart mailserver to ensure configuration is fully loaded
    restart_mailserver()



def diagnose_mail_forwards():
    """Diagnose forward status for all users"""
    print("\n🔍 Diagnosing Forward Status:\n")
    
    # Get all users
    output = subprocess.check_output([
        "docker", "exec", MAILSERVER,
        "bash", "-c",
        "grep -vE '^#|^$' /tmp/docker-mailserver/postfix-accounts.cf"
    ]).decode().strip()
    users = sorted(set(line.split("|")[0] for line in output.splitlines()))
    
    print(f"{'Email':<25} {'Local Config':<12} {'Container Active':<16} {'Forward To':<30}")
    print("=" * 85)
    
    for user in users:
        # Check local config
        local_sieve_path = os.path.join(LOCAL_SIEVE_BASE, user, "sieve", "forward.sieve")
        local_config = "✅ Yes" if os.path.exists(local_sieve_path) else "❌ No"
        
        # Check container active status
        try:
            result = subprocess.run([
                "docker", "exec", MAILSERVER,
                "doveadm", "sieve", "list", "-u", user
            ], capture_output=True, text=True, check=False)
            
            container_active = "✅ Yes" if result.returncode == 0 and "forward" in result.stdout else "❌ No"
        except:
            container_active = "❌ Error"
        
        # Get forward destination - prioritize container over local config
        forward_to = "-"
        
        # First try to get forward destination from container (most accurate)
        if container_active == "✅ Yes":
            try:
                local_part = user.split("@")[0]
                container_sieve_file = f"/var/mail/{DOMAIN}/{local_part}/home/sieve/forward.sieve"
                
                content_result = subprocess.run([
                    "docker", "exec", MAILSERVER,
                    "cat", container_sieve_file
                ], capture_output=True, text=True, check=False)
                
                if content_result.returncode == 0:
                    for line in content_result.stdout.splitlines():
                        if 'redirect' in line and '"' in line:
                            forward_to = line.split('"')[1]
                            break
            except:
                pass
        
        # Fallback to local config if container check failed
        if forward_to == "-" and os.path.exists(local_sieve_path):
            try:
                with open(local_sieve_path, 'r') as f:
                    for line in f:
                        if 'redirect' in line and '"' in line:
                            # Extract email from redirect line: redirect :copy "email@domain.com";
                            forward_to = line.split('"')[1]
                            break
            except:
                forward_to = "Error reading"
        
        prefix = is_minipass_app_email(user)
        user_with_prefix = f"{prefix}{user}"
        user_display = user_with_prefix[:23] + ".." if len(user_with_prefix) > 25 else user_with_prefix
        forward_display = forward_to[:28] + ".." if len(forward_to) > 30 else forward_to
        
        print(f"{user_display:<25} {local_config:<12} {container_active:<16} {forward_display:<30}")


def recover_lost_forwards():
    """Help recover lost forward configurations"""
    print("\n🔧 Forward Recovery Tool\n")
    
    diagnose_mail_forwards()
    
    print("\n" + "="*50)
    print("Forward Recovery Options:")
    print("1. Check container for existing forward rules")
    print("2. Recreate forward for specific user")
    print("3. Recover ALL missing local configs from container")
    print("4. Return to main menu")
    
    choice = input("\nChoose recovery option (1-4): ").strip()
    
    if choice == "1":
        check_container_forwards()
    elif choice == "2":
        recreate_specific_forward()
    elif choice == "3":
        recover_all_local_configs()
    elif choice == "4":
        return
    else:
        print("❌ Invalid choice.")



def check_container_forwards():
    """Check what forward rules exist in the mail container"""
    print("\n🔍 Checking container forward rules...\n")
    
    # Get all users
    output = subprocess.check_output([
        "docker", "exec", MAILSERVER,
        "bash", "-c",
        "grep -vE '^#|^$' /tmp/docker-mailserver/postfix-accounts.cf"
    ]).decode().strip()
    users = sorted(set(line.split("|")[0] for line in output.splitlines()))
    
    for user in users:
        prefix = is_minipass_app_email(user)
        print(f"\n📧 Checking {prefix}{user}:")
        
        # Check if forward rule exists in container
        try:
            result = subprocess.run([
                "docker", "exec", MAILSERVER,
                "doveadm", "sieve", "list", "-u", user
            ], capture_output=True, text=True, check=False)
            
            if result.returncode == 0 and result.stdout.strip():
                print(f"   🔍 Sieve rules: {result.stdout.strip()}")
                
                # If forward rule exists, try to read the content
                if "forward" in result.stdout:
                    local_part = user.split("@")[0]
                    container_sieve_file = f"/var/mail/{DOMAIN}/{local_part}/home/sieve/forward.sieve"
                    
                    content_result = subprocess.run([
                        "docker", "exec", MAILSERVER,
                        "cat", container_sieve_file
                    ], capture_output=True, text=True, check=False)
                    
                    if content_result.returncode == 0:
                        print(f"   📄 Forward content: {content_result.stdout.strip()}")
                        
                        # Extract forward destination
                        for line in content_result.stdout.splitlines():
                            if 'redirect' in line and '"' in line:
                                forward_to = line.split('"')[1]
                                print(f"   ➡️  Forwards to: {forward_to}")
                                break
                    else:
                        print(f"   ❌ Could not read forward file")
            else:
                print("   ❌ No active sieve rules")
                
        except Exception as e:
            print(f"   ❌ Error checking: {e}")



def recreate_specific_forward():
    """Recreate forward for a specific user"""
    email = input("\nEnter email to recreate forward for: ").strip()
    forward_to = input("Enter destination email address: ").strip()
    
    print(f"\n🔧 Recreating forward: {email} ➡️ {forward_to}")
    
    try:
        # Create local sieve config
        write_forward_sieve(email, forward_to)
        
        # Activate in container
        activate_forward_in_container(email)
        
        print("✅ Forward recreated successfully!")
        
    except Exception as e:
        print(f"❌ Error recreating forward: {e}")



def recover_all_local_configs():
    """Recover all missing local forward configs from the container"""
    print("\n🔧 Recovering ALL missing local configs from container...\n")
    
    # Get all users
    output = subprocess.check_output([
        "docker", "exec", MAILSERVER,
        "bash", "-c",
        "grep -vE '^#|^$' /tmp/docker-mailserver/postfix-accounts.cf"
    ]).decode().strip()
    users = sorted(set(line.split("|")[0] for line in output.splitlines()))
    
    recovered_count = 0
    skipped_count = 0
    
    for user in users:
        # Check if local config is missing
        local_sieve_path = os.path.join(LOCAL_SIEVE_BASE, user, "sieve", "forward.sieve")
        
        if os.path.exists(local_sieve_path):
            prefix = is_minipass_app_email(user)
            print(f"⏭️  Skipping {prefix}{user} - local config already exists")
            skipped_count += 1
            continue
        
        # Check if forward exists in container
        try:
            result = subprocess.run([
                "docker", "exec", MAILSERVER,
                "doveadm", "sieve", "list", "-u", user
            ], capture_output=True, text=True, check=False)
            
            if result.returncode == 0 and "forward" in result.stdout:
                # Forward exists in container, get the content
                local_part = user.split("@")[0]
                container_sieve_file = f"/var/mail/{DOMAIN}/{local_part}/home/sieve/forward.sieve"
                
                content_result = subprocess.run([
                    "docker", "exec", MAILSERVER,
                    "cat", container_sieve_file
                ], capture_output=True, text=True, check=False)
                
                if content_result.returncode == 0:
                    # Extract forward destination
                    forward_to = None
                    for line in content_result.stdout.splitlines():
                        if 'redirect' in line and '"' in line:
                            forward_to = line.split('"')[1]
                            break
                    
                    if forward_to:
                        prefix = is_minipass_app_email(user)
                        print(f"🔄 Recovering {prefix}{user} ➡️ {forward_to}")
                        try:
                            # Create local sieve config
                            write_forward_sieve(user, forward_to)
                            recovered_count += 1
                            print(f"   ✅ Local config recovered for {prefix}{user}")
                        except Exception as e:
                            print(f"   ❌ Failed to create local config: {e}")
                    else:
                        print(f"   ⚠️  Could not extract forward destination for {user}")
                else:
                    print(f"   ❌ Could not read container sieve file for {user}")
            else:
                prefix = is_minipass_app_email(user)
                print(f"⏭️  Skipping {prefix}{user} - no active forward in container")
                skipped_count += 1
                
        except Exception as e:
            print(f"   ❌ Error checking {user}: {e}")
    
    print(f"\n📊 Recovery Summary:")
    print(f"   ✅ Recovered: {recovered_count} local configs")
    print(f"   ⏭️  Skipped: {skipped_count} users")
    
    if recovered_count > 0:
        print(f"\n🎉 Success! Try running option 2 (List users with forwarding) now to see all forwards.")



def deep_mail_server_diagnostics():
    """Comprehensive mail server diagnostics to check for issues"""
    print("\n🔬 Deep Mail Server Diagnostics\n")
    print("=" * 70)
    
    # Get all users
    try:
        output = subprocess.check_output([
            "docker", "exec", MAILSERVER,
            "bash", "-c",
            "grep -vE '^#|^$' /tmp/docker-mailserver/postfix-accounts.cf"
        ]).decode().strip()
        users = sorted(set(line.split("|")[0] for line in output.splitlines()))
        print(f"📊 Found {len(users)} total mail users")
    except Exception as e:
        print(f"❌ Failed to get user list: {e}")
        return
    
    # Check 1: Duplicate sieve rules
    print("\n1️⃣ Checking for duplicate sieve rules...")
    duplicates_found = False
    
    for user in users:
        try:
            result = subprocess.run([
                "docker", "exec", MAILSERVER,
                "doveadm", "sieve", "list", "-u", user
            ], capture_output=True, text=True, check=False)
            
            if result.returncode == 0 and result.stdout.strip():
                rules = result.stdout.strip().split('\n')
                rule_names = [rule.split()[0] for rule in rules if rule.strip()]
                
                # Check for duplicates
                if len(rule_names) != len(set(rule_names)):
                    duplicates_found = True
                    prefix = is_minipass_app_email(user)
                    print(f"   ⚠️  {prefix}{user}: Duplicate rules detected: {rule_names}")
                elif len(rule_names) > 1:
                    prefix = is_minipass_app_email(user)
                    print(f"   ℹ️  {prefix}{user}: Multiple rules: {rule_names}")
                    
        except Exception as e:
            print(f"   ❌ Error checking {user}: {e}")
    
    if not duplicates_found:
        print("   ✅ No duplicate sieve rules found")
    
    # Check 2: Orphaned sieve files
    print("\n2️⃣ Checking for orphaned sieve files...")
    orphaned_files = []
    
    try:
        result = subprocess.run([
            "docker", "exec", MAILSERVER,
            "find", f"/var/mail/{DOMAIN}/", "-name", "*.sieve", "-type", "f"
        ], capture_output=True, text=True, check=False)
        
        if result.returncode == 0:
            sieve_files = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            for sieve_file in sieve_files:
                if sieve_file:
                    # Extract username from path
                    path_parts = sieve_file.split('/')
                    if len(path_parts) >= 4:
                        username_part = path_parts[3]  # /var/mail/domain/username/...
                        full_email = f"{username_part}@{DOMAIN}"
                        
                        if full_email not in users:
                            orphaned_files.append(sieve_file)
                            print(f"   ⚠️  Orphaned sieve file: {sieve_file}")
        
        if not orphaned_files:
            print("   ✅ No orphaned sieve files found")
            
    except Exception as e:
        print(f"   ❌ Error checking orphaned files: {e}")
    
    # Check 3: Forward destination analysis
    print("\n3️⃣ Analyzing forward destinations...")
    forward_destinations = {}
    invalid_forwards = []
    
    for user in users:
        try:
            result = subprocess.run([
                "docker", "exec", MAILSERVER,
                "doveadm", "sieve", "list", "-u", user
            ], capture_output=True, text=True, check=False)
            
            if result.returncode == 0 and "forward" in result.stdout:
                # Get forward content
                local_part = user.split("@")[0]
                container_sieve_file = f"/var/mail/{DOMAIN}/{local_part}/home/sieve/forward.sieve"
                
                content_result = subprocess.run([
                    "docker", "exec", MAILSERVER,
                    "cat", container_sieve_file
                ], capture_output=True, text=True, check=False)
                
                if content_result.returncode == 0:
                    forward_to = None
                    for line in content_result.stdout.splitlines():
                        if 'redirect' in line and '"' in line:
                            forward_to = line.split('"')[1]
                            break
                    
                    if forward_to:
                        if forward_to not in forward_destinations:
                            forward_destinations[forward_to] = []
                        forward_destinations[forward_to].append(user)
                        
                        # Check for potential issues
                        if not '@' in forward_to or not '.' in forward_to:
                            invalid_forwards.append(f"{user} -> {forward_to}")
                    else:
                        invalid_forwards.append(f"{user} -> [could not parse destination]")
                        
        except Exception as e:
            print(f"   ❌ Error analyzing {user}: {e}")
    
    # Report forward destination analysis
    print(f"   📊 Active forwards: {sum(len(users) for users in forward_destinations.values())}")
    
    # Check for multiple users forwarding to same destination
    for destination, forwarding_users in forward_destinations.items():
        if len(forwarding_users) > 1:
            # Add prefixes to user display in the list
            users_with_prefixes = [f"{is_minipass_app_email(user)}{user}" for user in forwarding_users]
            print(f"   ℹ️  Multiple users forward to {destination}: {', '.join(users_with_prefixes)}")
    
    if invalid_forwards:
        print("   ⚠️  Invalid forward destinations:")
        for invalid in invalid_forwards:
            print(f"      {invalid}")
    else:
        print("   ✅ All forward destinations appear valid")
    
    # Check 4: Mail directory consistency
    print("\n4️⃣ Checking mail directory consistency...")
    
    try:
        result = subprocess.run([
            "docker", "exec", MAILSERVER,
            "ls", "-la", f"/var/mail/{DOMAIN}/"
        ], capture_output=True, text=True, check=False)
        
        if result.returncode == 0:
            mail_dirs = []
            for line in result.stdout.split('\n'):
                if line.strip() and not line.startswith('total') and not line.startswith('d'):
                    continue
                elif line.strip() and line.startswith('d') and not line.endswith(('.', '..')):
                    parts = line.split()
                    if len(parts) >= 9:
                        dir_name = parts[-1]
                        mail_dirs.append(f"{dir_name}@{DOMAIN}")
            
            # Check for directories without corresponding users
            orphaned_dirs = [d for d in mail_dirs if d not in users]
            if orphaned_dirs:
                print("   ⚠️  Orphaned mail directories:")
                for orphaned_dir in orphaned_dirs:
                    prefix = is_minipass_app_email(orphaned_dir)
                    print(f"      {prefix}{orphaned_dir}")
            else:
                print("   ✅ All mail directories have corresponding users")
                
            # Check for users without directories
            missing_dirs = [u for u in users if u not in mail_dirs]
            if missing_dirs:
                print("   ⚠️  Users missing mail directories:")
                for missing_dir in missing_dirs:
                    prefix = is_minipass_app_email(missing_dir)
                    print(f"      {prefix}{missing_dir}")
            else:
                print("   ✅ All users have mail directories")
                
    except Exception as e:
        print(f"   ❌ Error checking mail directories: {e}")
    
    # Check 5: Postfix virtual aliases
    print("\n5️⃣ Checking postfix virtual aliases...")
    
    try:
        result = subprocess.run([
            "docker", "exec", MAILSERVER,
            "bash", "-c",
            "test -f /tmp/docker-mailserver/postfix-virtual.cf && cat /tmp/docker-mailserver/postfix-virtual.cf || echo 'No virtual aliases file'"
        ], capture_output=True, text=True, check=False)
        
        if result.returncode == 0:
            if "No virtual aliases file" in result.stdout:
                print("   ℹ️  No postfix virtual aliases configured")
            else:
                aliases = result.stdout.strip().split('\n') if result.stdout.strip() else []
                print(f"   📊 Found {len(aliases)} postfix virtual aliases")
                for alias in aliases[:5]:  # Show first 5
                    if alias.strip():
                        print(f"      {alias}")
                if len(aliases) > 5:
                    print(f"      ... and {len(aliases) - 5} more")
                    
    except Exception as e:
        print(f"   ❌ Error checking virtual aliases: {e}")
    
    # Summary
    print(f"\n📋 Diagnostic Summary:")
    print(f"   👥 Total users: {len(users)}")
    print(f"   📤 Active forwards: {sum(len(users) for users in forward_destinations.values())}")
    print(f"   🎯 Unique destinations: {len(forward_destinations)}")
    
    issues_found = len(orphaned_files) + len(invalid_forwards)
    if issues_found == 0:
        print(f"   ✅ No issues detected - mail server looks healthy!")
    else:
        print(f"   ⚠️  {issues_found} potential issues found - review above")
    
    print("\n" + "=" * 70)



def main_menu():
    while True:
        #print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        #print("   MINIPASS MAIL MANGER  TOOL")
        #print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

        title = pyfiglet.figlet_format("minipass", font = "big" ) 
        print(title)

        print("  1.  List mail users")
        print("  2.  List users with forwarding")
        print("  3.  Create new user")
        print("  4.  Delete a forward")
        print("  5.  Delete a mail user")
        print("  6.  Delete user inbox emails")
        print("  7.  Hard Delete Mail User (user + forward + inbox)")
        print("  8.  Add a forward to an existing user")
        print("  9.  Diagnose forward status")
        print("  10. Recover lost forwards")
        print("  11. Deep mail server diagnostics")
        print("  12. Restart mailserver")
        print("")
        print("  x.  Exit")

        choice = input("\nChoose an option:> ").strip()
        if choice == "1":
            list_mail_users()
        elif choice == "2":
            list_forwards()
        elif choice == "3":
            create_user()
        elif choice == "4":
            delete_forward()
        elif choice == "5":
            delete_user()
        elif choice == "6":
            delete_user_inbox()
        elif choice == '7':
            hard_delete_user()
        elif choice == '8':
            add_forward_to_existing_user()
        elif choice == '9':
            diagnose_mail_forwards()
        elif choice == '10':
            recover_lost_forwards()
        elif choice == '11':
            deep_mail_server_diagnostics()
        elif choice == '12':
            restart_mailserver()
        elif choice == "x":
            break
        else:
            print("❌ Invalid choice. Try again.")

if __name__ == "__main__":
    main_menu()

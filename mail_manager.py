#!/usr/bin/env python3

import os
import subprocess
import getpass
import shutil

MAILSERVER = "mailserver"
DOMAIN = "minipass.me"
USER_BASE_DIR = f"/var/mail/{DOMAIN}"
LOCAL_SIEVE_BASE = "./config/user-patches"
FORWARD_DIR = "./config/user-patches"

def list_mail_users():
    print("\n📬 Mail Users:\n")
    output = subprocess.check_output([
        "docker", "exec", MAILSERVER,
        "bash", "-c",
        "grep -vE '^#|^$' /tmp/docker-mailserver/postfix-accounts.cf"
    ]).decode().strip()
    users = sorted(set(line.split("|")[0] for line in output.splitlines()))
    for user in users:
        print(f" - {user}")

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
                        print(f" - {user_folder} ➡️ {target}")
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
        activate_forward_in_container(email)
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
            "setup", "email", "del", email
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
    print("✅ Forwarding activated.\n")

def main_menu():
    while True:
        print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print("   MINIPASS MAIL MANGER  TOOL")
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print("1. List mail users")
        print("2. List users with forwarding")
        print("3. Create new user")
        print("4. Delete a forward")
        print("5. Delete a mail user")
        print("6. Delete user inbox emails")
        print("7. Hard Delete Mail User (user + forward + inbox)")
        print("8. Add a forward to an existing user")
        print("x. Exit")

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
        elif choice == "x":
            break
        else:
            print("❌ Invalid choice. Try again.")

if __name__ == "__main__":
    main_menu()

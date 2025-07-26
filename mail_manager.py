#!/usr/bin/env python3
import os
import subprocess
import getpass






MAILSERVER = "mailserver"
DOMAIN = "minipass.me"
USER_BASE_DIR = f"/var/mail/{DOMAIN}"
LOCAL_SIEVE_BASE = "./config/user-patches"
FORWARD_DIR = "./config/user-patches"


import os
import shutil
import subprocess



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
        inbox_path = f"/var/mail/minipass.me/{email.split('@')[0]}"
        subprocess.run([
            "docker", "exec", MAILSERVER,
            "rm", "-rf", inbox_path
        ], check=True)
        print("📭 Mail inbox data deleted.")
    except subprocess.CalledProcessError:
        print("❌ Failed to delete inbox data.")





def old2_hard_delete_user():
    email = input("Enter the email of the user to hard delete: ").strip()
    confirm = input(f"⚠️ Are you sure you want to permanently delete {email}? This will remove the user, inbox, and forward config. (y/n): ").lower()
    if confirm != 'y':
        print("❌ Cancelled.")
        return

    # Delete user
    try:
        print("🗑️ Deleting user...")
        subprocess.run([
            "docker", "exec", MAILSERVER,
            "setup", "email", "del", email
        ], check=True)
    except subprocess.CalledProcessError:
        print("❌ Failed to delete user.")

    # Delete forward config
    try:
        local_forward_dir = os.path.join(FORWARD_DIR, email)
        if os.path.exists(local_forward_dir):
            shutil.rmtree(local_forward_dir)
            print("🧹 Forward config deleted.")
    except Exception as e:
        print(f"❌ Failed to delete forward config: {e}")

    # Delete inbox files
    try:
        inbox_path = f"/var/mail/minipass.me/{email.split('@')[0]}"
        subprocess.run([
            "docker", "exec", MAILSERVER,
            "rm", "-rf", inbox_path
        ], check=True)
        print("📭 Mail inbox data deleted.")
    except subprocess.CalledProcessError:
        print("❌ Failed to delete inbox data.")







def OLD_hard_delete_user():
    email = input("Enter the email of the user to hard delete: ").strip()

    confirm = input(f"⚠️ Are you sure you want to permanently delete {email}? This will remove the user, inbox, and forward config. (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Cancelled.")
        return

    # Step 1: Delete user
    print("🗑️ Deleting user...")
    subprocess.run(["docker", "exec", MAILSERVER, "./delmailuser.sh", email])

    # Step 2: Delete forward config
    local_forward_dir = os.path.join(FORWARD_DIR, email)
    if os.path.isdir(local_forward_dir):
        shutil.rmtree(local_forward_dir)
        print(f"🧹 Forward config deleted from {local_forward_dir}")
    else:
        print("ℹ️ No forward config found.")

    # Step 3: Delete mail data inside container
    print("🧹 Deleting mail data from container...")
    subprocess.run([
        "docker", "exec", MAILSERVER, "rm", "-rf", f"/var/mail/minipass.me/{email.split('@')[0]}"
    ])

    print(f"✅ Hard delete complete for: {email}")






def list_mail_users():
    print("\n📬 Mail Users:")
    output = subprocess.check_output([
        "docker", "exec", MAILSERVER,
        "bash", "-c",
        "grep -vE '^#|^$' /tmp/docker-mailserver/postfix-accounts.cf"
    ]).decode().strip()
    users = sorted(set(line.split("|")[0] for line in output.splitlines()))
    for user in users:
        print(f" - {user}")

def OLD_list_forwards():
    print("\n📤 Users with Forwarding Enabled:")
    for root, dirs, files in os.walk(LOCAL_SIEVE_BASE):
        if "forward.sieve" in files:
            email = os.path.basename(root)
            with open(os.path.join(root, "forward.sieve")) as f:
                for line in f:
                    if "redirect" in line:
                        forward_to = line.split('"')[1]
                        print(f" - {email} ➡️ {forward_to}")



def list_forwards():
    print("\n📤 Users with Forwarding Enabled:")
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





def create_user():
    email = input("Enter new email (e.g. user@minipass.me): ").strip()
    password = getpass.getpass("Enter password: ")

    subprocess.run([
        "docker", "exec", MAILSERVER,
        "addmailuser", email, password
    ])

    choice = input("Add a forwarding address? (y/n): ").strip().lower()
    if choice == "y":
        forward_to = input("Forward to which email?: ").strip()
        write_forward_sieve(email, forward_to)
        activate_forward_in_container(email)
    print("✅ User creation complete.\n")


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
    ])
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


def write_forward_sieve(email, forward_to):
    path = os.path.join(LOCAL_SIEVE_BASE, email, "sieve")
    os.makedirs(path, exist_ok=True)
    forward_script = f'redirect "{forward_to}";\n'
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
        print("\n 📪 Mail Manager")
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print("1. List mail users")
        print("2. List users with forwarding")
        print("3. Create new user")
        print("4. Delete a forward")
        print("5. Delete a mail user")
        print("6. Delete user inbox emails")
        print("7. Hard Delete Mail User (user + forward + inbox)")
        print("")
        print("x. Exit")

        choice = input("Choose an option: ").strip()
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

        elif choice == "x":
            break
        else:
            print("❌ Invalid choice. Try again.")

if __name__ == "__main__":
    main_menu()

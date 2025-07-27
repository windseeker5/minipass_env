#!/usr/bin/env python3

import os
import subprocess
import shutil
import logging

MAILSERVER = "mailserver"
DOMAIN = "minipass.me"
USER_BASE_DIR = f"/var/mail/{DOMAIN}"
LOCAL_SIEVE_BASE = "./config/user-patches"
FORWARD_DIR = "./config/user-patches"

def create_user_programmatic(email, password):
    """
    Creates a mail user programmatically without interactive prompts.
    
    Args:
        email (str): Full email address (e.g., user@minipass.me)
        password (str): Password for the email account
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logging.info(f"📧 Creating mail user: {email}")
        subprocess.run([
            "docker", "exec", MAILSERVER,
            "addmailuser", email, password
        ], check=True)
        logging.info(f"✅ Successfully created mail user: {email}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Failed to create mail user {email}: {e}")
        return False
    except Exception as e:
        logging.error(f"❌ Exception creating mail user {email}: {e}")
        return False

def add_forward_programmatic(email, forward_to):
    """
    Adds email forwarding programmatically without interactive prompts.
    
    Args:
        email (str): Source email address
        forward_to (str): Destination email address
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logging.info(f"📤 Adding forward rule: {email} -> {forward_to}")
        write_forward_sieve(email, forward_to)
        activate_forward_in_container(email)
        logging.info(f"✅ Successfully added forward rule: {email} -> {forward_to}")
        return True
    except Exception as e:
        logging.error(f"❌ Failed to add forward rule {email} -> {forward_to}: {e}")
        return False

def write_forward_sieve(email, forward_to):
    """
    Writes the sieve forwarding script locally.
    
    Args:
        email (str): Source email address
        forward_to (str): Destination email address
    """
    path = os.path.join(LOCAL_SIEVE_BASE, email, "sieve")
    os.makedirs(path, exist_ok=True)
    forward_script = 'require ["fileinto", "copy"];\nredirect :copy "{}";\n'.format(forward_to)
    with open(os.path.join(path, "forward.sieve"), "w") as f:
        f.write(forward_script)
    logging.info(f"📁 Forward config written to: {os.path.join(path, 'forward.sieve')}")

def activate_forward_in_container(email):
    """
    Activates the forwarding rule inside the mail container.
    
    Args:
        email (str): Email address to activate forwarding for
    """
    local_part = email.split("@")[0]
    local_path = os.path.join(LOCAL_SIEVE_BASE, email, "sieve", "forward.sieve")
    container_home = f"/var/mail/{DOMAIN}/{local_part}/home"
    container_sieve_dir = f"{container_home}/sieve"
    
    logging.info("🔄 Activating forward inside container...")
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
    logging.info("✅ Forwarding activated.")

def setup_customer_email_complete(subdomain, password, forward_to_email):
    """
    Complete email setup for a new customer including user creation and forwarding.
    
    Args:
        subdomain (str): Customer's subdomain/app_name
        password (str): Password for the email account (same as app password)
        forward_to_email (str): Customer's external email for forwarding
        
    Returns:
        tuple: (success: bool, email_address: str, error_message: str)
    """
    email_address = f"{subdomain}_app@{DOMAIN}"
    
    try:
        logging.info(f"🔧 Setting up complete email for subdomain: {subdomain}")
        logging.info(f"📧 Creating email: {email_address}")
        logging.info(f"➡️  Forwarding to: {forward_to_email}")
        
        # Step 1: Create mail user
        if not create_user_programmatic(email_address, password):
            return False, email_address, "Failed to create mail user"
        
        # Step 2: Set up forwarding if forward_to_email is provided
        if forward_to_email and forward_to_email.strip():
            if not add_forward_programmatic(email_address, forward_to_email):
                logging.warning(f"⚠️ Email created but forwarding failed for {email_address}")
                return True, email_address, "Email created but forwarding setup failed"
        
        logging.info(f"✅ Complete email setup successful for {email_address}")
        return True, email_address, ""
        
    except Exception as e:
        error_msg = f"Email setup failed: {e}"
        logging.error(f"❌ {error_msg}")
        return False, email_address, error_msg

def delete_user_programmatic(email):
    """
    Deletes a mail user programmatically without interactive prompts.
    
    Args:
        email (str): Email address to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logging.info(f"🗑️ Deleting mail user: {email}")
        subprocess.run([
            "docker", "exec", MAILSERVER,
            "delmailuser", email
        ], check=True)
        
        # Also remove forward config if it exists
        local_forward_dir = os.path.join(FORWARD_DIR, email)
        if os.path.exists(local_forward_dir):
            shutil.rmtree(local_forward_dir)
            logging.info("🧹 Forward config deleted.")
        
        logging.info(f"✅ Successfully deleted mail user: {email}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Failed to delete mail user {email}: {e}")
        return False
    except Exception as e:
        logging.error(f"❌ Exception deleting mail user {email}: {e}")
        return False
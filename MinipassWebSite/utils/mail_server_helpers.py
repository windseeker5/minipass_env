# utils/mail_server_helpers.py

import subprocess
import logging
import os

def create_mailserver_user(username, app_name):
    """
    Creates a new email user in the mailserver container
    Args:
        username: The username part of the email (e.g., 'admin', 'newuser')
        app_name: The app name (subdomain) for the email domain
    Returns:
        bool: True if successful, False otherwise
    """
    email_address = f"{username}@{app_name}.minipass.me"
    
    try:
        # Execute docker command to add email user
        cmd = [
            "docker", "exec", "-it", "mailserver", 
            "setup", "email", "add", email_address
        ]
        
        logging.info(f"Creating mailserver user: {email_address}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            logging.info(f"✅ Successfully created email user: {email_address}")
            return True
        else:
            logging.error(f"❌ Failed to create email user: {email_address}")
            logging.error(f"Error output: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logging.error(f"❌ Timeout creating email user: {email_address}")
        return False
    except Exception as e:
        logging.error(f"❌ Exception creating email user {email_address}: {e}")
        return False


def add_email_forwarding(user_email, forward_to_email):
    """
    Adds email forwarding rule to postfix-virtual.cf
    Args:
        user_email: The source email address (e.g., 'admin@appname.minipass.me')
        forward_to_email: The destination email address (e.g., 'customer@gmail.com')
    Returns:
        bool: True if successful, False otherwise
    """
    virtual_config_path = "/maildata/config/postfix-virtual.cf"
    forwarding_rule = f"{user_email}  {forward_to_email}\n"
    
    try:
        # Check if file exists
        if not os.path.exists(virtual_config_path):
            logging.error(f"❌ Postfix virtual config file not found: {virtual_config_path}")
            return False
        
        # Append forwarding rule to the file
        with open(virtual_config_path, 'a') as f:
            f.write(forwarding_rule)
        
        logging.info(f"✅ Added forwarding rule: {user_email} -> {forward_to_email}")
        return True
        
    except Exception as e:
        logging.error(f"❌ Failed to add forwarding rule: {e}")
        return False


def restart_postfix():
    """
    Restarts the postfix service using supervisorctl
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        cmd = ["supervisorctl", "restart", "postfix"]
        
        logging.info("Restarting postfix service...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            logging.info("✅ Successfully restarted postfix service")
            return True
        else:
            logging.error(f"❌ Failed to restart postfix service")
            logging.error(f"Error output: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logging.error("❌ Timeout restarting postfix service")
        return False
    except Exception as e:
        logging.error(f"❌ Exception restarting postfix: {e}")
        return False


def setup_customer_email(app_name, admin_email, forwarding_email, username="admin"):
    """
    Complete email setup for a new customer including user creation, forwarding, and postfix restart
    Args:
        app_name: The app name (subdomain)
        admin_email: The admin email address (for logging purposes)
        forwarding_email: Where emails should be forwarded to
        username: Username for the email (defaults to 'admin')
    Returns:
        tuple: (success: bool, email_address: str)
    """
    email_address = f"{username}@{app_name}.minipass.me"
    
    logging.info(f"🔧 Setting up email for customer: {admin_email}")
    logging.info(f"📧 Creating email: {email_address}")
    logging.info(f"➡️  Forwarding to: {forwarding_email}")
    
    # Step 1: Create mailserver user
    if not create_mailserver_user(username, app_name):
        return False, email_address
    
    # Step 2: Add forwarding rule
    if not add_email_forwarding(email_address, forwarding_email):
        return False, email_address
    
    # Step 3: Restart postfix
    if not restart_postfix():
        return False, email_address
    
    logging.info(f"✅ Email setup completed successfully for {email_address}")
    return True, email_address
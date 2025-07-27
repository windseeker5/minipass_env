#!/usr/bin/env python3

import os
import subprocess
import shutil
import logging
from .logging_config import (
    setup_subscription_logger, log_subprocess_call, log_subprocess_result,
    log_operation_start, log_operation_end, log_file_operation, log_validation_check
)

# Initialize subscription logger
logger = setup_subscription_logger()

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
    log_operation_start(logger, "Create Mail User", email=email, domain=DOMAIN)
    
    try:
        # Execute addmailuser command
        command = ["docker", "exec", MAILSERVER, "addmailuser", email, password]
        log_subprocess_call(logger, command, f"Creating mail user {email}")
        
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        log_subprocess_result(logger, result, f"Mail user {email} created successfully")
        
        # Verify user was created by checking postfix-accounts.cf
        verify_command = ["docker", "exec", MAILSERVER, "grep", email, "/tmp/docker-mailserver/postfix-accounts.cf"]
        log_subprocess_call(logger, verify_command, f"Verifying user {email} exists in postfix accounts")
        
        verify_result = subprocess.run(verify_command, capture_output=True, text=True)
        log_subprocess_result(logger, verify_result, f"User verification completed for {email}")
        
        if verify_result.returncode == 0 and email in verify_result.stdout:
            log_validation_check(logger, f"User {email} exists in mail server", True, "User found in postfix-accounts.cf")
            log_operation_end(logger, "Create Mail User", success=True)
            return True
        else:
            log_validation_check(logger, f"User {email} exists in mail server", False, "User not found in postfix-accounts.cf")
            log_operation_end(logger, "Create Mail User", success=False, error_msg="User verification failed")
            return False
            
    except subprocess.CalledProcessError as e:
        error_msg = f"Command failed with exit code {e.returncode}: {e.stderr if e.stderr else str(e)}"
        logger.error(f"❌ Failed to create mail user {email}: {error_msg}")
        log_operation_end(logger, "Create Mail User", success=False, error_msg=error_msg)
        return False
    except Exception as e:
        error_msg = f"Unexpected exception: {str(e)}"
        logger.error(f"❌ Exception creating mail user {email}: {error_msg}")
        log_operation_end(logger, "Create Mail User", success=False, error_msg=error_msg)
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
    log_operation_start(logger, "Add Email Forward", source_email=email, destination_email=forward_to)
    
    try:
        # Step 1: Write sieve forwarding script
        logger.info(f"📝 Step 1: Writing sieve forward script for {email}")
        write_forward_sieve(email, forward_to)
        
        # Step 2: Activate forwarding in container
        logger.info(f"🔄 Step 2: Activating forward rule in mail container for {email}")
        activate_forward_in_container(email)
        
        # Step 3: Verify forwarding is active
        logger.info(f"🔍 Step 3: Verifying forward rule activation for {email}")
        if verify_forward_active(email, forward_to):
            log_operation_end(logger, "Add Email Forward", success=True)
            return True
        else:
            log_operation_end(logger, "Add Email Forward", success=False, error_msg="Forward verification failed")
            return False
            
    except Exception as e:
        error_msg = f"Exception in forward setup: {str(e)}"
        logger.error(f"❌ Failed to add forward rule {email} -> {forward_to}: {error_msg}")
        log_operation_end(logger, "Add Email Forward", success=False, error_msg=error_msg)
        return False

def write_forward_sieve(email, forward_to):
    """
    Writes the sieve forwarding script locally.
    
    Args:
        email (str): Source email address
        forward_to (str): Destination email address
    """
    sieve_dir = os.path.join(LOCAL_SIEVE_BASE, email, "sieve")
    sieve_file = os.path.join(sieve_dir, "forward.sieve")
    
    log_file_operation(logger, "Creating sieve directory", sieve_dir)
    os.makedirs(sieve_dir, exist_ok=True)
    
    forward_script = 'require ["fileinto", "copy"];\nredirect :copy "{}";\n'.format(forward_to)
    
    log_file_operation(logger, "Writing forward sieve script", sieve_file, f"Content: {forward_script.strip()}")
    with open(sieve_file, "w") as f:
        f.write(forward_script)
    
    # Verify file was written correctly
    if os.path.exists(sieve_file):
        with open(sieve_file, "r") as f:
            content = f.read()
        log_validation_check(logger, f"Sieve file written correctly", True, f"File exists and contains: {content.strip()}")
    else:
        log_validation_check(logger, f"Sieve file written correctly", False, "File does not exist after write operation")

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
    
    logger.info(f"🔄 Activating forward inside container for {email}")
    logger.info(f"   📂 Local sieve file: {local_path}")
    logger.info(f"   📂 Container home: {container_home}")
    logger.info(f"   📂 Container sieve dir: {container_sieve_dir}")
    
    # Step 1: Create sieve directory in container
    command1 = ["docker", "exec", MAILSERVER, "mkdir", "-p", container_sieve_dir]
    log_subprocess_call(logger, command1, "Creating sieve directory in container")
    result1 = subprocess.run(command1, capture_output=True, text=True, check=True)
    log_subprocess_result(logger, result1, "Sieve directory created successfully")
    
    # Step 2: Copy sieve file to container
    command2 = ["docker", "cp", local_path, f"{MAILSERVER}:{container_sieve_dir}/forward.sieve"]
    log_subprocess_call(logger, command2, "Copying sieve file to container")
    result2 = subprocess.run(command2, capture_output=True, text=True, check=True)
    log_subprocess_result(logger, result2, "Sieve file copied successfully")
    
    # Step 3: Set proper ownership
    command3 = ["docker", "exec", MAILSERVER, "chown", "-R", "docker:docker", container_home]
    log_subprocess_call(logger, command3, "Setting ownership on container home directory")
    result3 = subprocess.run(command3, capture_output=True, text=True, check=True)
    log_subprocess_result(logger, result3, "Ownership set successfully")
    
    # Step 4: Put sieve rule using doveadm
    command4 = [
        "docker", "exec", MAILSERVER,
        "doveadm", "sieve", "put", "-u", email, "forward", f"{container_sieve_dir}/forward.sieve"
    ]
    log_subprocess_call(logger, command4, f"Installing sieve rule for {email}")
    result4 = subprocess.run(command4, capture_output=True, text=True, check=True)
    log_subprocess_result(logger, result4, f"Sieve rule installed for {email}")
    
    # Step 5: Activate sieve rule using doveadm
    command5 = [
        "docker", "exec", MAILSERVER,
        "doveadm", "sieve", "activate", "-u", email, "forward"
    ]
    log_subprocess_call(logger, command5, f"Activating sieve rule for {email}")
    result5 = subprocess.run(command5, capture_output=True, text=True, check=True)
    log_subprocess_result(logger, result5, f"Sieve rule activated for {email}")
    
    logger.info("✅ Forward activation completed")

def verify_forward_active(email, expected_forward_to):
    """
    Verifies that the forward rule is active and working for the given email.
    
    Args:
        email (str): Email address to check
        expected_forward_to (str): Expected forwarding destination
        
    Returns:
        bool: True if forward is active and correct, False otherwise
    """
    logger.info(f"🔍 Verifying forward rule for {email}")
    
    try:
        # Check if sieve rule exists and is active using doveadm
        command = [
            "docker", "exec", MAILSERVER,
            "doveadm", "sieve", "list", "-u", email
        ]
        log_subprocess_call(logger, command, f"Listing active sieve rules for {email}")
        result = subprocess.run(command, capture_output=True, text=True)
        log_subprocess_result(logger, result, f"Sieve rules retrieved for {email}")
        
        if result.returncode == 0:
            if "forward" in result.stdout:
                log_validation_check(logger, f"Forward rule exists for {email}", True, "Forward rule found in sieve list")
                
                # Additional check: verify the sieve file content in container
                local_part = email.split("@")[0]
                container_sieve_file = f"/var/mail/{DOMAIN}/{local_part}/home/sieve/forward.sieve"
                
                check_command = ["docker", "exec", MAILSERVER, "cat", container_sieve_file]
                log_subprocess_call(logger, check_command, f"Reading sieve file content for {email}")
                check_result = subprocess.run(check_command, capture_output=True, text=True)
                log_subprocess_result(logger, check_result, f"Sieve file content retrieved for {email}")
                
                if check_result.returncode == 0 and expected_forward_to in check_result.stdout:
                    log_validation_check(logger, f"Forward destination correct for {email}", True, f"Found {expected_forward_to} in sieve file")
                    return True
                else:
                    log_validation_check(logger, f"Forward destination correct for {email}", False, f"Expected {expected_forward_to} not found in sieve file")
                    return False
            else:
                log_validation_check(logger, f"Forward rule exists for {email}", False, "Forward rule not found in sieve list")
                return False
        else:
            log_validation_check(logger, f"Forward rule check for {email}", False, f"Failed to list sieve rules: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error verifying forward for {email}: {e}")
        log_validation_check(logger, f"Forward verification for {email}", False, f"Exception: {str(e)}")
        return False

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
    
    log_operation_start(logger, "Complete Customer Email Setup", 
                       subdomain=subdomain, 
                       email_address=email_address, 
                       forward_to_email=forward_to_email)
    
    # First, verify mail server status
    logger.info("🔍 Verifying mail server status before setup")
    mail_status = verify_mail_server_status()
    if not all([mail_status['mail_container_running'], mail_status['postfix_config_accessible'], mail_status['dovecot_accessible']]):
        error_msg = f"Mail server not ready: {', '.join(mail_status['error_messages'])}"
        log_operation_end(logger, "Complete Customer Email Setup", success=False, error_msg=error_msg)
        return False, email_address, error_msg
    
    try:
        # Step 1: Create mail user
        logger.info(f"📧 Step 1: Creating mail user {email_address}")
        if not create_user_programmatic(email_address, password):
            error_msg = "Failed to create mail user"
            log_operation_end(logger, "Complete Customer Email Setup", success=False, error_msg=error_msg)
            return False, email_address, error_msg
        
        # Step 2: Set up forwarding if forward_to_email is provided
        if forward_to_email and forward_to_email.strip():
            logger.info(f"📤 Step 2: Setting up forwarding {email_address} -> {forward_to_email}")
            if not add_forward_programmatic(email_address, forward_to_email):
                error_msg = "Email created but forwarding setup failed"
                logger.warning(f"⚠️ {error_msg} for {email_address}")
                log_operation_end(logger, "Complete Customer Email Setup", success=False, error_msg=error_msg)
                return True, email_address, error_msg
        else:
            logger.info(f"📭 Step 2: Skipping forwarding setup (no forward_to_email provided)")
        
        log_operation_end(logger, "Complete Customer Email Setup", success=True)
        return True, email_address, ""
        
    except Exception as e:
        error_msg = f"Email setup failed: {e}"
        logger.error(f"❌ {error_msg}")
        log_operation_end(logger, "Complete Customer Email Setup", success=False, error_msg=error_msg)
        return False, email_address, error_msg

def delete_user_programmatic(email):
    """
    Deletes a mail user programmatically without interactive prompts.
    
    Args:
        email (str): Email address to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    log_operation_start(logger, "Delete Mail User", email=email)
    
    try:
        # Step 1: Delete mail user from mail server
        command = ["docker", "exec", MAILSERVER, "delmailuser", email]
        log_subprocess_call(logger, command, f"Deleting mail user {email}")
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        log_subprocess_result(logger, result, f"Mail user {email} deleted successfully")
        
        # Step 2: Remove local forward config if it exists
        local_forward_dir = os.path.join(FORWARD_DIR, email)
        if os.path.exists(local_forward_dir):
            log_file_operation(logger, "Removing local forward config", local_forward_dir)
            shutil.rmtree(local_forward_dir)
            log_validation_check(logger, f"Local forward config removed for {email}", True, "Directory removed successfully")
        else:
            log_validation_check(logger, f"Local forward config for {email}", True, "No local config found to remove")
        
        log_operation_end(logger, "Delete Mail User", success=True)
        return True
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Command failed with exit code {e.returncode}: {e.stderr if e.stderr else str(e)}"
        logger.error(f"❌ Failed to delete mail user {email}: {error_msg}")
        log_operation_end(logger, "Delete Mail User", success=False, error_msg=error_msg)
        return False
    except Exception as e:
        error_msg = f"Unexpected exception: {str(e)}"
        logger.error(f"❌ Exception deleting mail user {email}: {error_msg}")
        log_operation_end(logger, "Delete Mail User", success=False, error_msg=error_msg)
        return False

def verify_mail_server_status():
    """
    Performs comprehensive checks on the mail server status and configuration.
    
    Returns:
        dict: Status information about various mail server components
    """
    log_operation_start(logger, "Mail Server Status Check")
    
    status = {
        'mail_container_running': False,
        'postfix_config_accessible': False,
        'dovecot_accessible': False,
        'user_patches_directory': False,
        'error_messages': []
    }
    
    try:
        # Check 1: Mail container is running
        container_check = ["docker", "ps", "--filter", f"name={MAILSERVER}", "--format", "{{.Names}}\t{{.Status}}"]
        log_subprocess_call(logger, container_check, "Checking mail container status")
        result = subprocess.run(container_check, capture_output=True, text=True)
        log_subprocess_result(logger, result, "Mail container status check")
        
        if result.returncode == 0 and MAILSERVER in result.stdout:
            status['mail_container_running'] = True
            log_validation_check(logger, "Mail container running", True, f"Container {MAILSERVER} is running")
        else:
            status['error_messages'].append(f"Mail container {MAILSERVER} is not running")
            log_validation_check(logger, "Mail container running", False, f"Container {MAILSERVER} not found")
        
        # Check 2: Postfix configuration is accessible
        if status['mail_container_running']:
            postfix_check = ["docker", "exec", MAILSERVER, "ls", "/tmp/docker-mailserver/postfix-accounts.cf"]
            log_subprocess_call(logger, postfix_check, "Checking postfix configuration file")
            result = subprocess.run(postfix_check, capture_output=True, text=True)
            log_subprocess_result(logger, result, "Postfix config check")
            
            if result.returncode == 0:
                status['postfix_config_accessible'] = True
                log_validation_check(logger, "Postfix config accessible", True, "postfix-accounts.cf is accessible")
            else:
                status['error_messages'].append("Postfix configuration file not accessible")
                log_validation_check(logger, "Postfix config accessible", False, "postfix-accounts.cf not found")
        
        # Check 3: Dovecot commands are working
        if status['mail_container_running']:
            dovecot_check = ["docker", "exec", MAILSERVER, "doveadm", "help"]
            log_subprocess_call(logger, dovecot_check, "Checking dovecot availability")
            result = subprocess.run(dovecot_check, capture_output=True, text=True)
            log_subprocess_result(logger, result, "Dovecot availability check")
            
            if result.returncode == 0:
                status['dovecot_accessible'] = True
                log_validation_check(logger, "Dovecot accessible", True, "doveadm commands are working")
            else:
                status['error_messages'].append("Dovecot commands not working")
                log_validation_check(logger, "Dovecot accessible", False, "doveadm commands failed")
        
        # Check 4: User patches directory exists and is writable
        if os.path.exists(LOCAL_SIEVE_BASE):
            status['user_patches_directory'] = True
            log_validation_check(logger, "User patches directory", True, f"Directory exists: {LOCAL_SIEVE_BASE}")
        else:
            status['error_messages'].append(f"User patches directory not found: {LOCAL_SIEVE_BASE}")
            log_validation_check(logger, "User patches directory", False, f"Directory missing: {LOCAL_SIEVE_BASE}")
        
        # Summary
        all_checks_passed = all([
            status['mail_container_running'],
            status['postfix_config_accessible'],
            status['dovecot_accessible'],
            status['user_patches_directory']
        ])
        
        if all_checks_passed:
            log_operation_end(logger, "Mail Server Status Check", success=True)
        else:
            error_summary = "; ".join(status['error_messages'])
            log_operation_end(logger, "Mail Server Status Check", success=False, error_msg=error_summary)
        
        return status
        
    except Exception as e:
        error_msg = f"Error during mail server status check: {str(e)}"
        logger.error(f"❌ {error_msg}")
        status['error_messages'].append(error_msg)
        log_operation_end(logger, "Mail Server Status Check", success=False, error_msg=error_msg)
        return status

def list_all_mail_users():
    """
    Lists all mail users currently configured in the mail server.
    
    Returns:
        list: List of email addresses configured in the mail server
    """
    logger.info("📋 Listing all mail users")
    
    try:
        command = ["docker", "exec", MAILSERVER, "grep", "-vE", "^#|^$", "/tmp/docker-mailserver/postfix-accounts.cf"]
        log_subprocess_call(logger, command, "Reading postfix accounts configuration")
        result = subprocess.run(command, capture_output=True, text=True)
        log_subprocess_result(logger, result, "Postfix accounts retrieved")
        
        if result.returncode == 0:
            users = []
            for line in result.stdout.strip().splitlines():
                if '|' in line:
                    email = line.split('|')[0]
                    users.append(email)
            
            logger.info(f"📊 Found {len(users)} mail users:")
            for user in users:
                logger.info(f"   📧 {user}")
            
            return users
        else:
            logger.error("❌ Failed to retrieve mail users list")
            return []
            
    except Exception as e:
        logger.error(f"❌ Error listing mail users: {e}")
        return []

def diagnose_email_setup_issue(email_address, expected_forward_to=None):
    """
    Comprehensive diagnostic function for email setup issues.
    
    Args:
        email_address (str): Email address to diagnose
        expected_forward_to (str): Expected forwarding destination (optional)
    
    Returns:
        dict: Diagnostic results
    """
    log_operation_start(logger, "Email Setup Diagnosis", email=email_address, expected_forward=expected_forward_to)
    
    diagnosis = {
        'email_exists': False,
        'sieve_file_exists': False,
        'forward_active': False,
        'forward_destination_correct': False,
        'issues_found': [],
        'recommendations': []
    }
    
    try:
        # Check 1: Email exists in mail server
        all_users = list_all_mail_users()
        if email_address in all_users:
            diagnosis['email_exists'] = True
            log_validation_check(logger, f"Email {email_address} exists", True, "Found in mail server")
        else:
            diagnosis['email_exists'] = False
            diagnosis['issues_found'].append(f"Email {email_address} not found in mail server")
            diagnosis['recommendations'].append("Create the email account using mail_integration.create_user_programmatic()")
            log_validation_check(logger, f"Email {email_address} exists", False, "Not found in mail server")
        
        # Check 2: Local sieve file exists
        local_part = email_address.split("@")[0] if "@" in email_address else email_address
        local_sieve_file = os.path.join(LOCAL_SIEVE_BASE, email_address, "sieve", "forward.sieve")
        
        if os.path.exists(local_sieve_file):
            diagnosis['sieve_file_exists'] = True
            log_validation_check(logger, f"Local sieve file for {email_address}", True, f"Found: {local_sieve_file}")
            
            # Read sieve file content
            with open(local_sieve_file, 'r') as f:
                sieve_content = f.read()
            logger.info(f"📄 Sieve file content: {sieve_content.strip()}")
            
        else:
            diagnosis['sieve_file_exists'] = False
            diagnosis['issues_found'].append(f"Local sieve file missing: {local_sieve_file}")
            diagnosis['recommendations'].append("Run write_forward_sieve() to create the local sieve configuration")
            log_validation_check(logger, f"Local sieve file for {email_address}", False, f"Missing: {local_sieve_file}")
        
        # Check 3: Container sieve file and activation
        if diagnosis['email_exists']:
            container_sieve_file = f"/var/mail/{DOMAIN}/{local_part}/home/sieve/forward.sieve"
            
            check_command = ["docker", "exec", MAILSERVER, "ls", "-la", container_sieve_file]
            log_subprocess_call(logger, check_command, f"Checking container sieve file for {email_address}")
            result = subprocess.run(check_command, capture_output=True, text=True)
            log_subprocess_result(logger, result, f"Container sieve file check for {email_address}")
            
            if result.returncode == 0:
                log_validation_check(logger, f"Container sieve file for {email_address}", True, "File exists in container")
                
                # Check if forward is active
                if expected_forward_to:
                    if verify_forward_active(email_address, expected_forward_to):
                        diagnosis['forward_active'] = True
                        diagnosis['forward_destination_correct'] = True
                        log_validation_check(logger, f"Forward active for {email_address}", True, f"Forwarding to {expected_forward_to}")
                    else:
                        diagnosis['forward_active'] = False
                        diagnosis['issues_found'].append(f"Forward not active or incorrect destination for {email_address}")
                        diagnosis['recommendations'].append("Run activate_forward_in_container() to activate forwarding")
                        log_validation_check(logger, f"Forward active for {email_address}", False, "Forward not working correctly")
            else:
                diagnosis['issues_found'].append(f"Container sieve file missing: {container_sieve_file}")
                diagnosis['recommendations'].append("Run activate_forward_in_container() to copy and activate sieve file")
                log_validation_check(logger, f"Container sieve file for {email_address}", False, "File missing in container")
        
        # Summary
        issues_count = len(diagnosis['issues_found'])
        if issues_count == 0:
            log_operation_end(logger, "Email Setup Diagnosis", success=True)
        else:
            error_msg = f"Found {issues_count} issues"
            log_operation_end(logger, "Email Setup Diagnosis", success=False, error_msg=error_msg)
        
        return diagnosis
        
    except Exception as e:
        error_msg = f"Error during email diagnosis: {str(e)}"
        logger.error(f"❌ {error_msg}")
        diagnosis['issues_found'].append(error_msg)
        log_operation_end(logger, "Email Setup Diagnosis", success=False, error_msg=error_msg)
        return diagnosis
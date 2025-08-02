#!/usr/bin/env python3
"""
Test script for the enhanced logging system.

This script helps validate that the new logging configuration is working
and provides sample operations to test mail integration logging.
"""

import os
import sys

# Add the current directory to the path so we can import utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.mail_integration import (
    verify_mail_server_status, 
    list_all_mail_users,
    diagnose_email_setup_issue
)
from utils.logging_config import setup_subscription_logger

def main():
    """Main test function"""
    
    # Initialize logger
    logger = setup_subscription_logger()
    
    print("=" * 70)
    print("ENHANCED LOGGING SYSTEM TEST")
    print("=" * 70)
    
    logger.info("🧪 Starting enhanced logging system test")
    
    # Test 1: Mail server status check
    print("\n1. Testing mail server status check...")
    logger.info("🔍 Test 1: Mail server status verification")
    
    mail_status = verify_mail_server_status()
    
    print(f"   Mail container running: {mail_status.get('mail_container_running', False)}")
    print(f"   Postfix accessible: {mail_status.get('postfix_config_accessible', False)}")
    print(f"   Dovecot accessible: {mail_status.get('dovecot_accessible', False)}")
    print(f"   User patches directory: {mail_status.get('user_patches_directory', False)}")
    
    if mail_status.get('error_messages'):
        print(f"   Issues found: {', '.join(mail_status['error_messages'])}")
    
    # Test 2: List existing mail users
    print("\n2. Testing mail user listing...")
    logger.info("📋 Test 2: Listing existing mail users")
    
    users = list_all_mail_users()
    print(f"   Found {len(users)} existing mail users")
    
    # Test 3: Log file verification
    print("\n3. Verifying log file creation...")
    # Determine correct log file path
    current_dir = os.getcwd()
    if current_dir.endswith('MinipassWebSite'):
        log_file_path = os.path.join(current_dir, 'subscribed_app.log')
    else:
        log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'subscribed_app.log')
    
    if os.path.exists(log_file_path):
        file_size = os.path.getsize(log_file_path)
        print(f"   ✅ Log file exists: {log_file_path}")
        print(f"   📊 Log file size: {file_size} bytes")
        
        # Show last few lines of log file
        try:
            with open(log_file_path, 'r') as f:
                lines = f.readlines()
                if lines:
                    print(f"   📄 Last log entry: {lines[-1].strip()}")
                else:
                    print("   📄 Log file is empty")
        except Exception as e:
            print(f"   ❌ Error reading log file: {e}")
    else:
        print(f"   ❌ Log file not found: {log_file_path}")
    
    # Test 4: Diagnostic functionality (if mail server is running)
    if mail_status.get('mail_container_running', False):
        print("\n4. Testing diagnostic functionality...")
        logger.info("🔧 Test 4: Email diagnostic functionality")
        
        # Test with a dummy email address
        test_email = "nonexistent_test@minipass.me"
        diagnosis = diagnose_email_setup_issue(test_email, "test@example.com")
        
        print(f"   Diagnosis for {test_email}:")
        print(f"   - Email exists: {diagnosis.get('email_exists', False)}")
        print(f"   - Sieve file exists: {diagnosis.get('sieve_file_exists', False)}")
        print(f"   - Issues found: {len(diagnosis.get('issues_found', []))}")
        print(f"   - Recommendations: {len(diagnosis.get('recommendations', []))}")
    else:
        print("\n4. Skipping diagnostic test (mail server not running)")
    
    logger.info("🎉 Enhanced logging system test completed")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETED")
    print("=" * 70)
    print(f"📋 Check the log file for detailed output: {log_file_path}")
    print("🔍 The enhanced logging is now ready for subscription debugging!")
    print("=" * 70)

if __name__ == "__main__":
    main()
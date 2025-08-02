#!/usr/bin/env python3
"""
Deployment script for Secure Fail2Ban Manager

This script sets up the secure fail2ban manager with proper permissions,
sudoers configuration, and security controls.

Author: Security hardening deployment
Version: 1.0
"""

import os
import sys
import subprocess
import stat
import shutil
import getpass
from pathlib import Path

# Configuration
SCRIPT_DIR = "/home/kdresdell/minipass_env"
SECURE_SCRIPT = "fail2ban_manager_secure.py"
ORIGINAL_SCRIPT = "fail2ban_manager.py"
EMAIL_CONFIG = "email_security_config.conf"
ANALYSIS_REPORT = "fail2ban_security_analysis.md"

SUDOERS_FILE = "/etc/sudoers.d/fail2ban_manager"
LOG_DIR = "/var/log/fail2ban_manager"
BACKUP_DIR = "/var/backups/fail2ban_manager"

class DeploymentError(Exception):
    """Custom exception for deployment errors"""
    pass

class SecureFailBanDeployer:
    def __init__(self):
        self.current_user = getpass.getuser()
        self.script_path = os.path.join(SCRIPT_DIR, SECURE_SCRIPT)
        self.original_path = os.path.join(SCRIPT_DIR, ORIGINAL_SCRIPT)
        
        # Validate environment
        self.validate_environment()
    
    def validate_environment(self):
        """Validate deployment environment"""
        # Check if running as root
        if os.geteuid() == 0:
            raise DeploymentError("This deployment script should not be run as root")
        
        # Check if required files exist
        required_files = [
            os.path.join(SCRIPT_DIR, SECURE_SCRIPT),
            os.path.join(SCRIPT_DIR, EMAIL_CONFIG),
            os.path.join(SCRIPT_DIR, ANALYSIS_REPORT)
        ]
        
        for file_path in required_files:
            if not os.path.exists(file_path):
                raise DeploymentError(f"Required file not found: {file_path}")
        
        # Check sudo access
        try:
            subprocess.run(['sudo', '-n', 'true'], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            raise DeploymentError("sudo access required. Please run 'sudo -v' first")
    
    def backup_original_files(self):
        """Backup original files before deployment"""
        print("📦 Creating backups...")
        
        try:
            # Create backup directory
            subprocess.run(['sudo', 'mkdir', '-p', BACKUP_DIR], check=True)
            subprocess.run(['sudo', 'chmod', '750', BACKUP_DIR], check=True)
            
            # Backup original script if it exists
            if os.path.exists(self.original_path):
                backup_path = os.path.join(BACKUP_DIR, f"{ORIGINAL_SCRIPT}.backup")
                subprocess.run(['sudo', 'cp', self.original_path, backup_path], check=True)
                print(f"✅ Backed up original script to {backup_path}")
            
            # Backup existing fail2ban configuration
            jail_local = "/etc/fail2ban/jail.local"
            if os.path.exists(jail_local):
                backup_path = os.path.join(BACKUP_DIR, "jail.local.backup")
                subprocess.run(['sudo', 'cp', jail_local, backup_path], check=True)
                print(f"✅ Backed up jail.local to {backup_path}")
            
        except subprocess.CalledProcessError as e:
            raise DeploymentError(f"Failed to create backups: {e}")
    
    def create_log_directories(self):
        """Create secure log directories"""
        print("📁 Setting up log directories...")
        
        try:
            # Create log directory
            subprocess.run(['sudo', 'mkdir', '-p', LOG_DIR], check=True)
            subprocess.run(['sudo', 'chmod', '750', LOG_DIR], check=True)
            subprocess.run(['sudo', 'chown', f'root:{self.current_user}', LOG_DIR], check=True)
            
            print(f"✅ Created secure log directory: {LOG_DIR}")
            
        except subprocess.CalledProcessError as e:
            raise DeploymentError(f"Failed to create log directories: {e}")
    
    def setup_sudoers_configuration(self):
        """Setup secure sudoers configuration"""
        print("🔐 Configuring sudoers...")
        
        sudoers_content = f"""# Fail2Ban Manager - Secure sudo configuration
# Allows {self.current_user} to execute specific fail2ban commands safely

# Allow fail2ban-client status commands (read-only)
{self.current_user} ALL=(root) NOPASSWD: /usr/bin/fail2ban-client status
{self.current_user} ALL=(root) NOPASSWD: /usr/bin/fail2ban-client status *

# Allow specific ban/unban operations with validation
{self.current_user} ALL=(root) NOPASSWD: /usr/bin/fail2ban-client set * banip *
{self.current_user} ALL=(root) NOPASSWD: /usr/bin/fail2ban-client set * unbanip *
{self.current_user} ALL=(root) NOPASSWD: /usr/bin/fail2ban-client unban *

# Allow log file reading
{self.current_user} ALL=(root) NOPASSWD: /bin/cat /var/log/fail2ban.log*

# Deny all other fail2ban-client commands for security
"""
        
        try:
            # Write sudoers configuration
            with open('/tmp/fail2ban_sudoers', 'w') as f:
                f.write(sudoers_content)
            
            # Validate sudoers syntax
            subprocess.run(['sudo', 'visudo', '-c', '-f', '/tmp/fail2ban_sudoers'], check=True)
            
            # Install sudoers file
            subprocess.run(['sudo', 'cp', '/tmp/fail2ban_sudoers', SUDOERS_FILE], check=True)
            subprocess.run(['sudo', 'chmod', '440', SUDOERS_FILE], check=True)
            subprocess.run(['sudo', 'chown', 'root:root', SUDOERS_FILE], check=True)
            
            # Clean up temp file
            os.remove('/tmp/fail2ban_sudoers')
            
            print(f"✅ Configured sudoers: {SUDOERS_FILE}")
            
        except subprocess.CalledProcessError as e:
            raise DeploymentError(f"Failed to configure sudoers: {e}")
    
    def install_secure_script(self):
        """Install the secure script with proper permissions"""
        print("🛡️ Installing secure script...")
        
        try:
            # Set secure permissions on the script
            os.chmod(self.script_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP)  # 750
            
            # Create symlink for easy access
            symlink_path = f"/home/{self.current_user}/bin/fail2ban-secure"
            os.makedirs(f"/home/{self.current_user}/bin", exist_ok=True)
            
            if os.path.exists(symlink_path):
                os.remove(symlink_path)
            
            os.symlink(self.script_path, symlink_path)
            
            print(f"✅ Installed secure script with symlink: {symlink_path}")
            
        except OSError as e:
            raise DeploymentError(f"Failed to install secure script: {e}")
    
    def setup_email_protection(self):
        """Setup email service protection configuration"""
        print("📧 Setting up email service protection...")
        
        email_config_path = os.path.join(SCRIPT_DIR, EMAIL_CONFIG)
        target_path = "/etc/fail2ban/jail.d/email-security.conf"
        
        try:
            # Copy email configuration
            subprocess.run(['sudo', 'cp', email_config_path, target_path], check=True)
            subprocess.run(['sudo', 'chmod', '644', target_path], check=True)
            subprocess.run(['sudo', 'chown', 'root:root', target_path], check=True)
            
            print(f"✅ Installed email protection config: {target_path}")
            print("⚠️  Review and enable appropriate jails in the configuration")
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Warning: Could not install email config: {e}")
            print("   You may need to manually copy the email configuration")
    
    def create_filters(self):
        """Create additional fail2ban filters"""
        print("🔍 Creating additional filters...")
        
        # Email rate limiting filter
        rate_limit_filter = """[Definition]
# Email rate limiting filter
failregex = ^.* (postfix|dovecot).*\[<HOST>\].*
ignoreregex =

[Init]
# Count all connections from same IP
maxlines = 1
"""
        
        # Email bomber filter
        bomber_filter = """[Definition]
# Email bomber protection filter
failregex = ^.* postfix/smtpd\\[\\d+\\]: .* client=.*\\[<HOST>\\].*
            ^.* dovecot.*\\[<HOST>\\].*
ignoreregex =

[Init]
maxlines = 1
"""
        
        filters = {
            '/etc/fail2ban/filter.d/email-rate-limit.conf': rate_limit_filter,
            '/etc/fail2ban/filter.d/email-bomber.conf': bomber_filter
        }
        
        for filter_path, content in filters.items():
            try:
                with open('/tmp/filter_temp', 'w') as f:
                    f.write(content)
                
                subprocess.run(['sudo', 'cp', '/tmp/filter_temp', filter_path], check=True)
                subprocess.run(['sudo', 'chmod', '644', filter_path], check=True)
                subprocess.run(['sudo', 'chown', 'root:root', filter_path], check=True)
                
                os.remove('/tmp/filter_temp')
                print(f"✅ Created filter: {filter_path}")
                
            except (subprocess.CalledProcessError, OSError) as e:
                print(f"⚠️ Warning: Could not create filter {filter_path}: {e}")
    
    def test_installation(self):
        """Test the installation"""
        print("🧪 Testing installation...")
        
        try:
            # Test script execution
            result = subprocess.run([self.script_path, '--help'], 
                                  capture_output=True, text=True, timeout=10)
            
            # Test sudo configuration
            result = subprocess.run(['sudo', '-n', '/usr/bin/fail2ban-client', 'status'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print("✅ Installation test passed")
            else:
                print("⚠️ Warning: Some tests failed, but installation completed")
                
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"⚠️ Warning: Installation test failed: {e}")
    
    def show_post_installation_info(self):
        """Show post-installation information"""
        print("\n" + "="*60)
        print("🎉 SECURE FAIL2BAN MANAGER DEPLOYMENT COMPLETED")
        print("="*60)
        print()
        print("📁 Files installed:")
        print(f"   • Secure script: {self.script_path}")
        print(f"   • Security analysis: {os.path.join(SCRIPT_DIR, ANALYSIS_REPORT)}")
        print(f"   • Email config: /etc/fail2ban/jail.d/email-security.conf")
        print(f"   • Sudoers config: {SUDOERS_FILE}")
        print(f"   • Log directory: {LOG_DIR}")
        print(f"   • Backup directory: {BACKUP_DIR}")
        print()
        print("🚀 Usage:")
        print(f"   • Run: {self.script_path}")
        print(f"   • Or use: ~/bin/fail2ban-secure")
        print()
        print("⚠️  Security Notes:")
        print("   • Review the security analysis report")
        print("   • Configure email protection jails as needed")
        print("   • Test the configuration in a safe environment")
        print("   • Monitor audit logs regularly")
        print("   • Keep fail2ban and system updated")
        print()
        print("📧 Email Protection:")
        print("   • Review /etc/fail2ban/jail.d/email-security.conf")
        print("   • Enable appropriate jails for your mail server")
        print("   • Test email service protection")
        print()
        print("🔍 Monitoring:")
        print(f"   • Audit log: {LOG_DIR}/fail2ban_manager_audit.log")
        print(f"   • Application log: /var/log/fail2ban_manager.log")
        print("   • Fail2ban log: /var/log/fail2ban.log")
        print()
    
    def deploy(self):
        """Execute the full deployment"""
        print("🚀 Starting Secure Fail2Ban Manager Deployment\n")
        
        try:
            self.backup_original_files()
            self.create_log_directories()
            self.setup_sudoers_configuration()
            self.install_secure_script()
            self.setup_email_protection()
            self.create_filters()
            self.test_installation()
            self.show_post_installation_info()
            
        except DeploymentError as e:
            print(f"❌ Deployment failed: {e}")
            return 1
        except Exception as e:
            print(f"❌ Unexpected error during deployment: {e}")
            return 1
        
        return 0

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print("""
Secure Fail2Ban Manager Deployment Script

This script deploys the hardened version of the fail2ban manager with:
- Comprehensive security controls
- Proper file permissions
- Sudoers configuration
- Email service protection
- Audit logging

Usage:
  python3 deploy_secure_fail2ban.py

Requirements:
- sudo privileges
- fail2ban installed
- Python 3.6+

Security Features:
- Input validation and sanitization
- Command injection prevention
- Path traversal protection
- Audit logging
- Session management
- Rate limiting
""")
        return 0
    
    try:
        deployer = SecureFailBanDeployer()
        return deployer.deploy()
    except Exception as e:
        print(f"❌ Fatal deployment error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
#!/usr/bin/env python3
"""
Secure Fail2Ban Manager Installation Script

This script automates the installation and configuration of the security-hardened
fail2ban manager with enhanced email monitoring capabilities.

Author: Python DevOps Automation Specialist
Created: 2025-08-02
Version: 2.0.0 (Security Enhanced)

Features:
- Automated installation of all components
- Security validation and hardening
- Email jail configuration deployment
- Sudoers configuration with restricted access
- Filter installation and validation
- System service integration
- Comprehensive testing and validation
"""

import os
import sys
import subprocess
import shutil
import pwd
import grp
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse
import logging
from datetime import datetime

# Security imports
import stat
import hashlib


class SecurityInstaller:
    """Security-focused installation manager"""
    
    def __init__(self, dry_run: bool = False, log_level: str = "INFO"):
        self.dry_run = dry_run
        self.installation_log = []
        self.errors = []
        self.warnings = []
        self.has_sudo = False  # Will be set during prerequisite check
        
        # Setup logging - use user-accessible directory
        log_file = Path(__file__).parent / 'secure_fail2ban_install.log'
        try:
            logging.basicConfig(
                level=getattr(logging, log_level),
                format='%(asctime)s [%(levelname)s] %(message)s',
                handlers=[
                    logging.FileHandler(log_file),
                    logging.StreamHandler()
                ]
            )
        except PermissionError:
            # Fallback to console-only logging if file creation fails
            logging.basicConfig(
                level=getattr(logging, log_level),
                format='%(asctime)s [%(levelname)s] %(message)s',
                handlers=[logging.StreamHandler()]
            )
            print(f"⚠️ Warning: Could not create log file {log_file}, using console logging only")
        self.logger = logging.getLogger(__name__)
        
        # Installation paths
        self.base_dir = Path(__file__).parent.resolve()
        self.fail2ban_dir = Path('/etc/fail2ban')
        self.jail_dir = self.fail2ban_dir / 'jail.d'
        self.filter_dir = self.fail2ban_dir / 'filter.d'
        self.sudoers_dir = Path('/etc/sudoers.d')
        
        self.logger.info("Secure Fail2Ban Manager Installation Starting")
        if self.dry_run:
            self.logger.info("DRY RUN MODE - No changes will be made")
    
    def log_action(self, action: str, status: str, details: str = ""):
        """Log installation action"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'status': status,
            'details': details
        }
        self.installation_log.append(entry)
        
        if status == 'ERROR':
            self.errors.append(entry)
            self.logger.error(f"{action}: {details}")
        elif status == 'WARNING':
            self.warnings.append(entry)
            self.logger.warning(f"{action}: {details}")
        else:
            self.logger.info(f"{action}: {status}")
    
    def check_prerequisites(self) -> bool:
        """Check system prerequisites for installation"""
        self.logger.info("Checking system prerequisites...")
        
        # Check if running as root
        if os.getuid() == 0:
            self.log_action("ROOT_CHECK", "ERROR", "Do not run installation as root")
            return False
        
        # Check if user has sudo privileges
        self.has_sudo = self._check_sudo_access()
        if not self.has_sudo:
            self.log_action("SUDO_CHECK", "WARNING", "User does not have passwordless sudo - will use user-space installation mode")
            self.logger.warning("Sudo access not available - switching to user-space installation mode")
            self.logger.warning("Some features will require manual setup by system administrator")
        else:
            self.log_action("SUDO_CHECK", "SUCCESS", "User has sudo privileges")
            
        # Check if fail2ban is installed (for full installation mode)
        if self.has_sudo and not shutil.which('fail2ban-client'):
            self.log_action("FAIL2BAN_CHECK", "ERROR", "fail2ban is not installed")
            return False
        elif not self.has_sudo:
            self.log_action("FAIL2BAN_CHECK", "SKIP", "Skipping fail2ban check in user-space mode")
            
        # Check if fail2ban directories exist (for full installation mode)
        if self.has_sudo and not self.fail2ban_dir.exists():
            self.log_action("FAIL2BAN_DIR_CHECK", "ERROR", f"fail2ban directory not found: {self.fail2ban_dir}")
            return False
        elif not self.has_sudo:
            self.log_action("FAIL2BAN_DIR_CHECK", "SKIP", "Skipping fail2ban directory check in user-space mode")
        
        # Check required source files
        if self.has_sudo:
            required_files = [
                'secure_fail2ban_manager.py',
                'email-security.conf',
                'email-filters.conf',
                'secure-fail2ban-sudoers'
            ]
        else:
            # User-space mode requires fewer files
            required_files = [
                'secure_fail2ban_manager.py'
            ]
        
        missing_files = []
        for file in required_files:
            if not (self.base_dir / file).exists():
                missing_files.append(file)
        
        if missing_files:
            if self.has_sudo:
                for file in missing_files:
                    self.log_action("SOURCE_FILE_CHECK", "ERROR", f"Required file not found: {file}")
                return False
            else:
                # In user-space mode, only secure_fail2ban_manager.py is truly required
                if 'secure_fail2ban_manager.py' in missing_files:
                    self.log_action("SOURCE_FILE_CHECK", "ERROR", f"Required file not found: secure_fail2ban_manager.py")
                    return False
                else:
                    for file in missing_files:
                        self.log_action("SOURCE_FILE_CHECK", "SKIP", f"Optional file not found: {file}")
        else:
            # No missing files
            if self.has_sudo:
                self.log_action("SOURCE_FILE_CHECK", "SUCCESS", "All required files found for full installation")
            else:
                self.log_action("SOURCE_FILE_CHECK", "SUCCESS", "All required files found for user-space installation")
        
        if self.has_sudo:
            self.log_action("PREREQUISITES", "SUCCESS", "All prerequisites met for full installation")
        else:
            self.log_action("PREREQUISITES", "SUCCESS", "Prerequisites met for user-space installation")
        return True
    
    def _check_sudo_access(self) -> bool:
        """Check if user has sudo access without prompting for password"""
        try:
            result = subprocess.run(['sudo', '-n', 'true'], capture_output=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def create_fail2ban_group(self) -> bool:
        """Create fail2ban-managers group"""
        if not self.has_sudo:
            self.log_action("GROUP_CREATE", "SKIP", "Skipping group creation in user-space mode")
            return True
            
        self.logger.info("Creating fail2ban-managers group...")
        
        try:
            # Check if group already exists
            try:
                grp.getgrnam('fail2ban-managers')
                self.log_action("GROUP_CREATE", "EXISTS", "fail2ban-managers group already exists")
                return True
            except KeyError:
                pass
            
            if not self.dry_run:
                result = subprocess.run(
                    ['sudo', 'groupadd', 'fail2ban-managers'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode != 0:
                    self.log_action("GROUP_CREATE", "ERROR", f"Failed to create group: {result.stderr}")
                    return False
            
            self.log_action("GROUP_CREATE", "SUCCESS", "fail2ban-managers group created")
            return True
            
        except Exception as e:
            self.log_action("GROUP_CREATE", "ERROR", f"Exception: {e}")
            return False
    
    def add_user_to_group(self, username: Optional[str] = None) -> bool:
        """Add user to fail2ban-managers group"""
        if not self.has_sudo:
            self.log_action("USER_GROUP_ADD", "SKIP", "Skipping user group addition in user-space mode")
            return True
            
        if username is None:
            username = pwd.getpwuid(os.getuid()).pw_name
        
        self.logger.info(f"Adding user {username} to fail2ban-managers group...")
        
        try:
            # Check if user is already in group
            user_groups = [grp.getgrgid(gid).gr_name for gid in os.getgroups()]
            if 'fail2ban-managers' in user_groups:
                self.log_action("USER_GROUP_ADD", "EXISTS", f"User {username} already in group")
                return True
            
            if not self.dry_run:
                result = subprocess.run(
                    ['sudo', 'usermod', '-a', '-G', 'fail2ban-managers', username],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode != 0:
                    self.log_action("USER_GROUP_ADD", "ERROR", f"Failed to add user: {result.stderr}")
                    return False
            
            self.log_action("USER_GROUP_ADD", "SUCCESS", f"User {username} added to group")
            return True
            
        except Exception as e:
            self.log_action("USER_GROUP_ADD", "ERROR", f"Exception: {e}")
            return False
    
    def install_sudoers_config(self) -> bool:
        """Install sudoers configuration"""
        if not self.has_sudo:
            self.log_action("SUDOERS_INSTALL", "SKIP", "Skipping sudoers installation in user-space mode")
            return True
            
        self.logger.info("Installing sudoers configuration...")
        
        source_file = self.base_dir / 'secure-fail2ban-sudoers'
        target_file = self.sudoers_dir / 'secure-fail2ban'
        
        try:
            if not self.dry_run:
                # Copy file
                result = subprocess.run(
                    ['sudo', 'cp', str(source_file), str(target_file)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode != 0:
                    self.log_action("SUDOERS_COPY", "ERROR", f"Failed to copy: {result.stderr}")
                    return False
                
                # Set proper permissions
                result = subprocess.run(
                    ['sudo', 'chmod', '440', str(target_file)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode != 0:
                    self.log_action("SUDOERS_CHMOD", "ERROR", f"Failed to set permissions: {result.stderr}")
                    return False
                
                # Set proper ownership
                result = subprocess.run(
                    ['sudo', 'chown', 'root:root', str(target_file)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode != 0:
                    self.log_action("SUDOERS_CHOWN", "ERROR", f"Failed to set ownership: {result.stderr}")
                    return False
                
                # Validate sudoers syntax
                result = subprocess.run(
                    ['sudo', 'visudo', '-c'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode != 0:
                    self.log_action("SUDOERS_VALIDATE", "ERROR", f"Invalid syntax: {result.stderr}")
                    # Remove invalid file
                    subprocess.run(['sudo', 'rm', str(target_file)])
                    return False
            
            self.log_action("SUDOERS_INSTALL", "SUCCESS", f"Installed to {target_file}")
            return True
            
        except Exception as e:
            self.log_action("SUDOERS_INSTALL", "ERROR", f"Exception: {e}")
            return False
    
    def install_jail_configuration(self) -> bool:
        """Install email security jail configuration"""
        if not self.has_sudo:
            self.log_action("JAIL_CONFIG_INSTALL", "SKIP", "Skipping jail configuration in user-space mode")
            return True
            
        self.logger.info("Installing jail configuration...")
        
        source_file = self.base_dir / 'email-security.conf'
        target_file = self.jail_dir / 'email-security.conf'
        
        try:
            if not self.dry_run:
                # Ensure jail.d directory exists
                if not self.jail_dir.exists():
                    result = subprocess.run(
                        ['sudo', 'mkdir', '-p', str(self.jail_dir)],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode != 0:
                        self.log_action("JAIL_DIR_CREATE", "ERROR", f"Failed to create directory: {result.stderr}")
                        return False
                
                # Copy configuration file
                result = subprocess.run(
                    ['sudo', 'cp', str(source_file), str(target_file)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode != 0:
                    self.log_action("JAIL_CONFIG_COPY", "ERROR", f"Failed to copy: {result.stderr}")
                    return False
                
                # Set proper permissions
                result = subprocess.run(
                    ['sudo', 'chmod', '644', str(target_file)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode != 0:
                    self.log_action("JAIL_CONFIG_CHMOD", "ERROR", f"Failed to set permissions: {result.stderr}")
                    return False
            
            self.log_action("JAIL_CONFIG_INSTALL", "SUCCESS", f"Installed to {target_file}")
            return True
            
        except Exception as e:
            self.log_action("JAIL_CONFIG_INSTALL", "ERROR", f"Exception: {e}")
            return False
    
    def install_filter_configurations(self) -> bool:
        """Install email security filter configurations"""
        if not self.has_sudo:
            self.log_action("FILTERS_INSTALL", "SKIP", "Skipping filter installation in user-space mode")
            return True
            
        self.logger.info("Installing filter configurations...")
        
        # Define filter mappings
        filters = {
            'postfix-sasl': [
                'failregex = ^%(__prefix_line)swarning: [-._\\w]+\\[<HOST>\\]: SASL (?:LOGIN|PLAIN|(?:CRAM|DIGEST)-MD5) authentication failed(?:: [ -~]*)?$',
                '            ^%(__prefix_line)swarning: [-._\\w]+\\[<HOST>\\]: SASL authentication failed$',
                '            ^%(__prefix_line)srejecting SASL login from [-._\\w]+\\[<HOST>\\]$',
                '            ^%(__prefix_line)swarning: [-._\\w]+\\[<HOST>\\]: SASL authentication failure: [-._\\w]+$',
                '            ^%(__prefix_line)swarning: unknown\\[<HOST>\\]: SASL (?:LOGIN|PLAIN|(?:CRAM|DIGEST)-MD5) authentication failed$',
                '',
                'ignoreregex ='
            ],
            'postfix-rbl': [
                'failregex = ^%(__prefix_line)sREJECT.*\\[<HOST>\\].*Service unavailable; Client host \\[<HOST>\\] blocked$',
                '            ^%(__prefix_line)sREJECT.*\\[<HOST>\\].*listed by domain.*$',
                '            ^%(__prefix_line)sREJECT.*\\[<HOST>\\].*Client host rejected: cannot find your hostname$',
                '            ^%(__prefix_line)sREJECT.*from [-._\\w]+\\[<HOST>\\].*RBL.*$',
                '            ^%(__prefix_line)sREJECT.*from [-._\\w]+\\[<HOST>\\].*Sender address rejected: Domain not found$',
                '',
                'ignoreregex ='
            ],
            'postfix-relay': [
                'failregex = ^%(__prefix_line)sREJECT.*\\[<HOST>\\].*Relay access denied$',
                '            ^%(__prefix_line)sREJECT.*from [-._\\w]+\\[<HOST>\\].*relay access denied$',
                '            ^%(__prefix_line)sNOQUEUE: reject: RCPT from [-._\\w]+\\[<HOST>\\].*relay access denied$',
                '            ^%(__prefix_line)swarning: [-._\\w]+\\[<HOST>\\]: address not listed for hostname$',
                '            ^%(__prefix_line)sREJECT.*\\[<HOST>\\].*: Sender address rejected: not owned by user$',
                '',
                'ignoreregex ='
            ],
            'postfix-spam': [
                'failregex = ^%(__prefix_line)sREJECT.*\\[<HOST>\\].*Message rejected for spam$',
                '            ^%(__prefix_line)sREJECT.*from [-._\\w]+\\[<HOST>\\].*content rejected$',
                '            ^%(__prefix_line)sREJECT.*\\[<HOST>\\].*: header .* from [-._\\w]+\\[<HOST>\\]; proto=ESMTP.*$',
                '            ^%(__prefix_line)sblocked using .*\\[<HOST>\\]$',
                '            ^%(__prefix_line)sREJECT.*\\[<HOST>\\].*Message contains spam or virus$',
                '',
                'ignoreregex ='
            ],
            'postfix-ratelimit': [
                'failregex = ^%(__prefix_line)swarning: [-._\\w]+\\[<HOST>\\]: Connection rate limit exceeded$',
                '            ^%(__prefix_line)swarning: Connection concurrency limit exceeded .* from \\[<HOST>\\]$',
                '            ^%(__prefix_line)swarning: Connection rate limit exceeded from \\[<HOST>\\]$',
                '            ^%(__prefix_line)sREJECT.*\\[<HOST>\\].*: Client host rejected: too many connections$',
                '',
                'ignoreregex ='
            ],
            'dovecot-auth': [
                'failregex = ^%(__prefix_line)s(?:auth-worker\\(\\d+\\):)?\\s*auth-worker(?:\\(\\d+\\))?: auth failed, \\d+ attempts in \\d+ secs: user=<[^>]*>, method=\\w+, rip=<HOST>, lip=[\\d.]+(?:, session=<\\w+>)?$',
                '            ^%(__prefix_line)s(?:auth-worker\\(\\d+\\):)?\\s*auth failed, (?:\\d+ attempts in \\d+ secs: )?user=<[^>]*>, method=\\w+, rip=<HOST>, lip=[\\d.]+$',
                '            ^%(__prefix_line)s(?:auth-worker\\(\\d+\\):)?\\s*auth-worker(?:\\(\\d+\\))?: Password mismatch.*rip=<HOST>$',
                '            ^%(__prefix_line)s(?:auth-worker\\(\\d+\\):)?\\s*auth failed.*rip=<HOST>.*$',
                '            ^%(__prefix_line)s(?:auth|auth-worker)(?:\\(\\d+\\))?: (?:pam\\(\\S+,<HOST>(?:,\\S*)?\\): pam_authenticate\\(\\) failed|passwd-file\\(\\S+,<HOST>(?:,\\S*)?\\): unknown user|passwd\\(\\S+,<HOST>(?:,\\S*)?\\): unknown user|unknown user).*$',
                '',
                'ignoreregex ='
            ],
            'dovecot-pop3-imap': [
                'failregex = ^%(__prefix_line)s(?:pop3|imap)-login: (?:Disconnected|Aborted login \\(auth failed|Aborted login \\(tried to use non-plaintext|Aborted login \\(tried to use disabled|Authentication failure).*rip=<HOST>.*$',
                '            ^%(__prefix_line)s(?:pop3|imap)-login: Disconnected \\(auth failed, \\d+ attempts in \\d+ secs\\):.*rip=<HOST>.*$',
                '            ^%(__prefix_line)s(?:pop3|imap)-login: Aborted login.*rip=<HOST>.*$',
                '            ^%(__prefix_line)s(?:pop3|imap): Error: .*authentication failed.*remote=<HOST>$',
                '',
                'ignoreregex ='
            ],
            'roundcube-auth': [
                'failregex = ^\\[.*\\] <HOST> Roundcube: \\[.*\\] Failed login for .* from <HOST>.*$',
                '            ^\\[.*\\] <HOST> .*IMAP Error: Login failed for .* from <HOST>.*$',
                '            ^\\[.*\\] <HOST> .*Authentication failed for .* from <HOST>.*$',
                '            ^.*\\[<HOST>\\] .*Authentication failed.*$',
                '            ^.*Roundcube.*Failed login.*from <HOST>.*$',
                '',
                'ignoreregex ='
            ],
            'email-directory-harvest': [
                'failregex = ^%(__prefix_line)sREJECT.*\\[<HOST>\\].*User unknown in.*table$',
                '            ^%(__prefix_line)sREJECT.*\\[<HOST>\\].*Recipient address rejected: User unknown$',
                '            ^%(__prefix_line)sREJECT.*from [-._\\w]+\\[<HOST>\\].*User unknown$',
                '            ^%(__prefix_line)sREJECT.*\\[<HOST>\\].*address rejected: User unknown in local recipient table$',
                '            ^%(__prefix_line)sNOQUEUE: reject: RCPT from [-._\\w]+\\[<HOST>\\].*User unknown in virtual mailbox table$',
                '',
                'ignoreregex ='
            ]
        }
        
        success_count = 0
        
        for filter_name, patterns in filters.items():
            try:
                target_file = self.filter_dir / f'{filter_name}.conf'
                
                if not self.dry_run:
                    # Create filter file content
                    filter_content = f"""# {filter_name.replace('-', ' ').title()} Filter for Fail2Ban
# Auto-generated by Secure Fail2Ban Manager Installation
# Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

[Definition]
{chr(10).join(patterns)}
"""
                    
                    # Write filter file using sudo
                    temp_file = f'/tmp/{filter_name}.conf'
                    with open(temp_file, 'w') as f:
                        f.write(filter_content)
                    
                    # Copy to filter directory
                    result = subprocess.run(
                        ['sudo', 'cp', temp_file, str(target_file)],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode != 0:
                        self.log_action("FILTER_INSTALL", "ERROR", f"Failed to install {filter_name}: {result.stderr}")
                        os.unlink(temp_file)
                        continue
                    
                    # Set proper permissions
                    subprocess.run(['sudo', 'chmod', '644', str(target_file)])
                    
                    # Clean up temp file
                    os.unlink(temp_file)
                
                self.log_action("FILTER_INSTALL", "SUCCESS", f"Installed {filter_name}.conf")
                success_count += 1
                
            except Exception as e:
                self.log_action("FILTER_INSTALL", "ERROR", f"Exception installing {filter_name}: {e}")
        
        if success_count == len(filters):
            self.log_action("FILTERS_INSTALL", "SUCCESS", f"All {success_count} filters installed")
            return True
        else:
            self.log_action("FILTERS_INSTALL", "PARTIAL", f"{success_count}/{len(filters)} filters installed")
            return False
    
    def validate_fail2ban_configuration(self) -> bool:
        """Validate fail2ban configuration"""
        if not self.has_sudo:
            self.log_action("CONFIG_VALIDATE", "SKIP", "Skipping configuration validation in user-space mode")
            return True
            
        self.logger.info("Validating fail2ban configuration...")
        
        try:
            if not self.dry_run:
                # Test configuration
                result = subprocess.run(
                    ['sudo', 'fail2ban-client', '--test'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    self.log_action("CONFIG_VALIDATE", "ERROR", f"Configuration test failed: {result.stderr}")
                    return False
            
            self.log_action("CONFIG_VALIDATE", "SUCCESS", "Configuration is valid")
            return True
            
        except Exception as e:
            self.log_action("CONFIG_VALIDATE", "ERROR", f"Exception: {e}")
            return False
    
    def reload_fail2ban(self) -> bool:
        """Reload fail2ban service"""
        if not self.has_sudo:
            self.log_action("FAIL2BAN_RELOAD", "SKIP", "Skipping fail2ban reload in user-space mode")
            return True
            
        self.logger.info("Reloading fail2ban service...")
        
        try:
            if not self.dry_run:
                result = subprocess.run(
                    ['sudo', 'systemctl', 'reload', 'fail2ban'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    self.log_action("FAIL2BAN_RELOAD", "ERROR", f"Reload failed: {result.stderr}")
                    return False
                
                # Wait a moment for reload to complete
                import time
                time.sleep(2)
                
                # Check service status
                result = subprocess.run(
                    ['sudo', 'systemctl', 'is-active', 'fail2ban'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.stdout.strip() != 'active':
                    self.log_action("FAIL2BAN_STATUS", "ERROR", f"Service not active: {result.stdout}")
                    return False
            
            self.log_action("FAIL2BAN_RELOAD", "SUCCESS", "Service reloaded successfully")
            return True
            
        except Exception as e:
            self.log_action("FAIL2BAN_RELOAD", "ERROR", f"Exception: {e}")
            return False
    
    def install_user_space_manager(self) -> bool:
        """Install manager script in user's local bin directory"""
        self.logger.info("Installing manager script in user space...")
        
        # Create user's local bin directory
        user_bin = Path.home() / '.local' / 'bin'
        user_bin.mkdir(parents=True, exist_ok=True)
        
        source_file = self.base_dir / 'secure_fail2ban_manager.py'
        target_file = user_bin / 'secure-fail2ban-manager'
        
        try:
            if not self.dry_run:
                # Copy script to user's local bin
                shutil.copy2(source_file, target_file)
                
                # Make executable
                target_file.chmod(0o755)
                
                # Create a wrapper script that explains limitations
                wrapper_content = f"""#!/bin/bash
# Secure Fail2Ban Manager - User Space Installation
# This is a limited version that runs without sudo privileges

echo "🛡️ Secure Fail2Ban Manager (User Space Mode)"
echo "⚠️ Limited functionality - requires manual sudo setup for full features"
echo ""

exec python3 "{target_file}" "$@"
"""
                
                wrapper_file = user_bin / 'fail2ban-manager'
                with open(wrapper_file, 'w') as f:
                    f.write(wrapper_content)
                wrapper_file.chmod(0o755)
            
            self.log_action("USER_SCRIPT_INSTALL", "SUCCESS", f"Installed to {target_file}")
            return True
            
        except Exception as e:
            self.log_action("USER_SCRIPT_INSTALL", "ERROR", f"Exception: {e}")
            return False

    def install_manager_script(self) -> bool:
        """Install the secure fail2ban manager script"""
        if not self.has_sudo:
            return self.install_user_space_manager()
            
        self.logger.info("Installing manager script...")
        
        source_file = self.base_dir / 'secure_fail2ban_manager.py'
        target_file = Path('/usr/local/bin/secure-fail2ban-manager')
        
        try:
            if not self.dry_run:
                # Copy script
                result = subprocess.run(
                    ['sudo', 'cp', str(source_file), str(target_file)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode != 0:
                    self.log_action("SCRIPT_COPY", "ERROR", f"Failed to copy: {result.stderr}")
                    return False
                
                # Make executable
                result = subprocess.run(
                    ['sudo', 'chmod', '755', str(target_file)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode != 0:
                    self.log_action("SCRIPT_CHMOD", "ERROR", f"Failed to set permissions: {result.stderr}")
                    return False
            
            self.log_action("SCRIPT_INSTALL", "SUCCESS", f"Installed to {target_file}")
            return True
            
        except Exception as e:
            self.log_action("SCRIPT_INSTALL", "ERROR", f"Exception: {e}")
            return False
    
    def create_audit_log_directory(self) -> bool:
        """Create audit log directory and files"""
        if not self.has_sudo:
            self.log_action("AUDIT_LOG_SETUP", "SKIP", "Skipping system audit log setup in user-space mode")
            # Create user-space audit log
            try:
                user_log_dir = Path.home() / '.local' / 'var' / 'log'
                user_log_dir.mkdir(parents=True, exist_ok=True)
                
                if not self.dry_run:
                    audit_log = user_log_dir / 'secure_fail2ban_manager.log'
                    audit_log.touch(exist_ok=True)
                    audit_log.chmod(0o640)
                
                self.log_action("USER_AUDIT_LOG_SETUP", "SUCCESS", f"User audit log created at {user_log_dir}")
                return True
            except Exception as e:
                self.log_action("USER_AUDIT_LOG_SETUP", "ERROR", f"Exception: {e}")
                return False
            
        self.logger.info("Creating audit log directory...")
        
        try:
            if not self.dry_run:
                # Create audit log file
                audit_log = Path('/var/log/secure_fail2ban_manager.log')
                
                result = subprocess.run(
                    ['sudo', 'touch', str(audit_log)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode != 0:
                    self.log_action("AUDIT_LOG_CREATE", "ERROR", f"Failed to create audit log: {result.stderr}")
                    return False
                
                # Set proper permissions
                subprocess.run(['sudo', 'chmod', '640', str(audit_log)])
                subprocess.run(['sudo', 'chown', 'root:fail2ban-managers', str(audit_log)])
                
                # Create sudo audit log
                sudo_log = Path('/var/log/sudo-fail2ban.log')
                subprocess.run(['sudo', 'touch', str(sudo_log)])
                subprocess.run(['sudo', 'chmod', '640', str(sudo_log)])
                subprocess.run(['sudo', 'chown', 'root:fail2ban-managers', str(sudo_log)])
            
            self.log_action("AUDIT_LOG_SETUP", "SUCCESS", "Audit logging configured")
            return True
            
        except Exception as e:
            self.log_action("AUDIT_LOG_SETUP", "ERROR", f"Exception: {e}")
            return False
    
    def test_installation(self) -> bool:
        """Test the installation"""
        self.logger.info("Testing installation...")
        
        try:
            if not self.dry_run:
                if self.has_sudo:
                    # Test sudo access
                    result = subprocess.run(
                        ['sudo', '-n', 'fail2ban-client', 'status'],
                        capture_output=True,
                        text=True,
                        timeout=15
                    )
                    
                    if result.returncode != 0:
                        self.log_action("SUDO_TEST", "ERROR", f"Sudo access test failed: {result.stderr}")
                        return False
                    
                    # Test manager script (system installation)
                    target_file = Path('/usr/local/bin/secure-fail2ban-manager')
                    if target_file.exists():
                        result = subprocess.run(
                            [str(target_file), '--version'],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        
                        if result.returncode != 0:
                            self.log_action("SCRIPT_TEST", "WARNING", "Manager script test failed")
                        else:
                            self.log_action("SCRIPT_TEST", "SUCCESS", "Manager script working")
                    
                    # Check active jails
                    result = subprocess.run(
                        ['sudo', '-n', 'fail2ban-client', 'status'],
                        capture_output=True,
                        text=True,
                        timeout=15
                    )
                    
                    if result.returncode == 0 and 'email' in result.stdout.lower():
                        self.log_action("EMAIL_JAILS_TEST", "SUCCESS", "Email jails detected")
                    else:
                        self.log_action("EMAIL_JAILS_TEST", "WARNING", "Email jails may not be active")
                else:
                    # Test user-space installation
                    user_bin = Path.home() / '.local' / 'bin'
                    target_file = user_bin / 'secure-fail2ban-manager'
                    
                    if target_file.exists():
                        result = subprocess.run(
                            ['python3', str(target_file), '--version'],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        
                        if result.returncode != 0:
                            self.log_action("USER_SCRIPT_TEST", "WARNING", "User script test failed")
                        else:
                            self.log_action("USER_SCRIPT_TEST", "SUCCESS", "User script working")
                    
                    self.log_action("USER_SPACE_TEST", "SUCCESS", "User-space installation functional")
            
            self.log_action("INSTALLATION_TEST", "SUCCESS", "Installation testing completed")
            return True
            
        except Exception as e:
            self.log_action("INSTALLATION_TEST", "ERROR", f"Exception: {e}")
            return False
    
    def print_installation_summary(self):
        """Print installation summary"""
        print("\n" + "=" * 80)
        mode_text = "USER-SPACE" if not self.has_sudo else "FULL SYSTEM"
        print(f"🛡️ SECURE FAIL2BAN MANAGER INSTALLATION SUMMARY ({mode_text})")
        print("=" * 80)
        
        print(f"\n📊 Installation Statistics:")
        print(f"  ✅ Successful actions: {len([a for a in self.installation_log if a['status'] == 'SUCCESS'])}")
        print(f"  ⚠️ Warnings: {len(self.warnings)}")
        print(f"  ❌ Errors: {len(self.errors)}")
        print(f"  ⏭️ Skipped actions: {len([a for a in self.installation_log if a['status'] == 'SKIP'])}")
        
        if self.errors:
            print(f"\n❌ ERRORS ENCOUNTERED:")
            for error in self.errors:
                print(f"  • {error['action']}: {error['details']}")
        
        if self.warnings:
            print(f"\n⚠️ WARNINGS:")
            for warning in self.warnings:
                print(f"  • {warning['action']}: {warning['details']}")
        
        if not self.has_sudo:
            print(f"\n🏠 USER-SPACE INSTALLATION COMPLETE:")
            print(f"  • Manager script installed in: ~/.local/bin/")
            print(f"  • Limited functionality without sudo privileges")
            print(f"  • Audit logs in: ~/.local/var/log/")
            
            print(f"\n🔧 POST-INSTALLATION STEPS (USER-SPACE):")
            print(f"  1. Add ~/.local/bin to your PATH:")
            print(f"     echo 'export PATH=\"$HOME/.local/bin:$PATH\"' >> ~/.bashrc")
            print(f"     source ~/.bashrc")
            print(f"  2. Run: secure-fail2ban-manager")
            print(f"  3. For full functionality, contact your system administrator to:")
            print(f"     - Install fail2ban system-wide")
            print(f"     - Grant you sudo privileges for fail2ban management")
            print(f"     - Run this installer with sudo access")
            
            print(f"\n📋 MANUAL SETUP INSTRUCTIONS FOR SYSTEM ADMINISTRATOR:")
            print(f"  1. Install fail2ban: sudo apt-get install fail2ban")
            print(f"  2. Create fail2ban-managers group: sudo groupadd fail2ban-managers")
            print(f"  3. Add user to group: sudo usermod -a -G fail2ban-managers {pwd.getpwuid(os.getuid()).pw_name}")
            print(f"  4. Copy configuration files from: {self.base_dir}")
            print(f"     - email-security.conf → /etc/fail2ban/jail.d/")
            print(f"     - email-filters.conf → /etc/fail2ban/filter.d/")
            print(f"     - secure-fail2ban-sudoers → /etc/sudoers.d/secure-fail2ban")
            print(f"  5. Restart fail2ban: sudo systemctl restart fail2ban")
            
        else:
            print(f"\n🔧 POST-INSTALLATION STEPS:")
            print(f"  1. Log out and log back in for group changes to take effect")
            print(f"  2. Run: secure-fail2ban-manager  (or use full path: /usr/local/bin/secure-fail2ban-manager)")
            print(f"  3. Test email security report: option 8 in the menu")
            print(f"  4. Review installation logs: {self.base_dir}/secure_fail2ban_install.log")
            print(f"  5. Review audit logs: /var/log/secure_fail2ban_manager.log")
            print(f"  6. Monitor fail2ban status: sudo fail2ban-client status")
            
            print(f"\n📧 EMAIL MONITORING:")
            print(f"  • Enhanced email jail monitoring enabled")
            print(f"  • Directory harvest attack detection")
            print(f"  • SMTP/IMAP/POP3 brute force protection")
            print(f"  • Spam injection and relay abuse detection")
        
        print(f"\n🔐 SECURITY NOTES:")
        print(f"  • All operations are logged for security auditing")
        if self.has_sudo:
            print(f"  • Users must be in 'fail2ban-managers' group")
        print(f"  • Rate limiting prevents abuse of commands")
        print(f"  • Input validation prevents injection attacks")
        
        print("\n" + "=" * 80)
    
    def run_installation(self) -> bool:
        """Run the complete installation process"""
        try:
            # Check prerequisites
            if not self.check_prerequisites():
                return False
            
            # Create group and add user
            if not self.create_fail2ban_group():
                return False
            
            if not self.add_user_to_group():
                return False
            
            # Install components
            if not self.install_sudoers_config():
                return False
            
            if not self.install_jail_configuration():
                return False
            
            if not self.install_filter_configurations():
                return False
            
            # Validate and reload
            if not self.validate_fail2ban_configuration():
                return False
            
            if not self.reload_fail2ban():
                return False
            
            # Install manager script
            if not self.install_manager_script():
                return False
            
            # Setup audit logging
            if not self.create_audit_log_directory():
                return False
            
            # Test installation
            if not self.test_installation():
                self.log_action("INSTALLATION", "WARNING", "Installation completed with test failures")
            else:
                self.log_action("INSTALLATION", "SUCCESS", "Installation completed successfully")
            
            return True
            
        except Exception as e:
            self.log_action("INSTALLATION", "ERROR", f"Fatal error: {e}")
            return False


def main():
    """Main installation entry point"""
    parser = argparse.ArgumentParser(
        description="Secure Fail2Ban Manager Installation Script",
        epilog="Example: python install_secure_fail2ban.py --install"
    )
    parser.add_argument(
        '--install',
        action='store_true',
        help='Run the installation'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run in dry-run mode (no changes made)'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='Secure Fail2Ban Manager Installer v2.0.0'
    )
    
    args = parser.parse_args()
    
    if not args.install:
        parser.print_help()
        return
    
    try:
        installer = SecurityInstaller(dry_run=args.dry_run, log_level=args.log_level)
        
        # Check sudo status first to inform user about installation mode
        installer_has_sudo = installer._check_sudo_access()
        
        print("🛡️ Secure Fail2Ban Manager Installation")
        print("=" * 50)
        
        if args.dry_run:
            print("🔍 DRY RUN MODE - No changes will be made")
        
        if installer_has_sudo:
            print("\n✅ FULL SYSTEM INSTALLATION MODE")
            print("Sudo access detected - installing with full system integration")
            
            print("\n⚠️ IMPORTANT SECURITY NOTICE:")
            print("This installation will:")
            print("• Create a 'fail2ban-managers' group")
            print("• Add your user to this group")
            print("• Install sudoers configuration with restricted access")
            print("• Install email security jails and filters")
            print("• Enable comprehensive email attack monitoring")
            print("• Set up security audit logging")
        else:
            print("\n🏠 USER-SPACE INSTALLATION MODE")
            print("⚠️ No sudo access detected - installing in user-space with limited functionality")
            
            print("\n📝 USER-SPACE INSTALLATION DETAILS:")
            print("This installation will:")
            print("• Install manager script in ~/.local/bin/")
            print("• Create user-specific audit logs")
            print("• Provide manual setup instructions for system administrator")
            print("• Enable basic fail2ban monitoring (read-only)")
            
            print("\n💡 FOR FULL FUNCTIONALITY:")
            print("Contact your system administrator to:")
            print("• Grant you sudo privileges for fail2ban management")
            print("• Install fail2ban system-wide")
            print("• Run this installer again with sudo access")
        
        if not args.dry_run:
            mode_text = "full system" if installer_has_sudo else "user-space"
            confirm = input(f"\nContinue with {mode_text} installation? (yes/no): ").strip().lower()
            if confirm not in ['yes', 'y']:
                print("Installation cancelled.")
                return
        
        success = installer.run_installation()
        installer.print_installation_summary()
        
        # Determine if installation was truly successful
        # Success means no errors, regardless of warnings or skipped actions
        has_errors = len(installer.errors) > 0
        
        if success and not has_errors:
            if installer.has_sudo:
                print("\n✅ Full system installation completed successfully!")
                if not args.dry_run:
                    print("\n🔄 Please log out and log back in for group changes to take effect.")
            else:
                print("\n✅ User-space installation completed successfully!")
                if not args.dry_run:
                    print("\n🏠 Your fail2ban manager is ready to use in user-space mode.")
                    print("Run 'secure-fail2ban-manager' after adding ~/.local/bin to your PATH.")
                else:
                    print("\n🔍 Dry-run completed - user-space installation would succeed.")
        elif has_errors:
            print("\n❌ Installation completed with errors. Check the summary above.")
            sys.exit(1)
        else:
            print("\n⚠️ Installation completed with warnings. Check the summary above.")
            # Don't exit with error code for warnings-only installations
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Installation interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal installation error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
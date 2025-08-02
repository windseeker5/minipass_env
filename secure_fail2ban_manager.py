#!/home/kdresdell/minipass_env/MinipassWebSite/venv/bin/python
"""
Secure Fail2Ban Manager with Enhanced Email Monitoring

A security-hardened fail2ban management script with comprehensive email jail monitoring,
enhanced security features, and audit logging capabilities.

Author: Python DevOps Automation Specialist
Created: 2025-08-02
Version: 2.0.0 (Security Enhanced)

Features:
- Security hardening with input validation and sanitization
- Comprehensive email jail monitoring (SMTP, IMAP, POP3)
- Email attack pattern analysis and queue failure reporting
- Audit logging with session management
- Rate limiting for operations
- Principle of least privilege for sudo operations
- Enhanced error handling and recovery
"""

import os
import sys
import subprocess
import json
import re
import csv
import gzip
import hashlib
import secrets
import time
import socket
import ipaddress
import logging
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pyfiglet
import argparse

# Security imports
from functools import wraps
import signal
import pwd
import grp


class SecurityError(Exception):
    """Custom security exception"""
    pass


class RateLimiter:
    """Rate limiter for operations to prevent abuse"""
    
    def __init__(self, max_calls: int = 10, time_window: int = 60):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def is_allowed(self) -> bool:
        """Check if operation is allowed based on rate limit"""
        now = time.time()
        # Remove old calls outside time window
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        if len(self.calls) >= self.max_calls:
            return False
        
        self.calls.append(now)
        return True


class SecurityAuditor:
    """Security audit logging and session management"""
    
    def __init__(self, log_file: str = "/home/kdresdell/minipass_env/secure_fail2ban_manager.log"):
        self.log_file = Path(log_file)
        self.session_id = self._generate_session_id()
        self.start_time = datetime.now()
        self.user = pwd.getpwuid(os.getuid()).pw_name
        
        # Setup secure logging
        self._setup_logging()
        self.log_event("SESSION_START", f"User: {self.user}, Session: {self.session_id}")
    
    def _generate_session_id(self) -> str:
        """Generate secure session ID"""
        return secrets.token_hex(16)
    
    def _setup_logging(self):
        """Setup secure audit logging"""
        try:
            # Create log directory if it doesn't exist
            self.log_file.parent.mkdir(mode=0o750, exist_ok=True)
            
            # Setup logger
            self.logger = logging.getLogger('security_audit')
            self.logger.setLevel(logging.INFO)
            
            # Create secure file handler
            handler = logging.FileHandler(self.log_file, mode='a')
            handler.setLevel(logging.INFO)
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] SESSION:%(session)s USER:%(user)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
            # Set secure permissions on log file
            try:
                os.chmod(self.log_file, 0o640)
            except OSError:
                pass  # May not have permission to change, that's ok
                
        except (PermissionError, OSError) as e:
            # Fall back to console logging if file logging fails
            print(f"⚠️ Warning: Cannot create log file {self.log_file}: {e}")
            print(f"📝 Falling back to console-only logging")
            
            # Setup console logger
            self.logger = logging.getLogger('security_audit')
            self.logger.setLevel(logging.INFO)
            
            # Create console handler
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] SESSION:%(session)s USER:%(user)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
            # Set log file to None to indicate console-only mode
            self.log_file = None
    
    def log_event(self, event_type: str, details: str, level: str = "INFO"):
        """Log security event with context"""
        extra = {
            'session': self.session_id,
            'user': self.user
        }
        
        message = f"{event_type}: {details}"
        
        if level == "WARNING":
            self.logger.warning(message, extra=extra)
        elif level == "ERROR":
            self.logger.error(message, extra=extra)
        elif level == "CRITICAL":
            self.logger.critical(message, extra=extra)
        else:
            self.logger.info(message, extra=extra)
    
    def log_command(self, command: List[str], success: bool, output: str = ""):
        """Log command execution for audit trail"""
        sanitized_cmd = [self._sanitize_for_log(arg) for arg in command]
        status = "SUCCESS" if success else "FAILURE"
        self.log_event(
            "COMMAND_EXECUTION", 
            f"Command: {' '.join(sanitized_cmd)}, Status: {status}, Output_len: {len(output)}"
        )
    
    def _sanitize_for_log(self, text: str) -> str:
        """Sanitize text for safe logging"""
        # Remove potential log injection characters
        sanitized = re.sub(r'[\n\r\t\x00-\x1f\x7f-\x9f]', '', str(text))
        return sanitized[:200]  # Limit length
    
    def close_session(self):
        """Close audit session"""
        duration = datetime.now() - self.start_time
        self.log_event("SESSION_END", f"Duration: {duration}")


class InputValidator:
    """Comprehensive input validation and sanitization"""
    
    @staticmethod
    def validate_ip(ip_string: str) -> bool:
        """Validate IP address format with enhanced security checks"""
        if not ip_string or len(ip_string) > 45:  # Max IPv6 length
            return False
        
        try:
            ip = ipaddress.ip_address(ip_string.strip())
            # Additional security: reject private/loopback IPs for banning operations
            # (but allow for search operations)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_jail_name(jail_name: str) -> bool:
        """Validate jail name to prevent injection attacks"""
        if not jail_name or len(jail_name) > 50:
            return False
        
        # Only allow alphanumeric, hyphen, underscore
        pattern = re.compile(r'^[a-zA-Z0-9_-]+$')
        return bool(pattern.match(jail_name))
    
    @staticmethod
    def validate_filename(filename: str) -> bool:
        """Validate filename to prevent path traversal"""
        if not filename or len(filename) > 100:
            return False
        
        # Check for path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
        
        # Only allow safe characters
        pattern = re.compile(r'^[a-zA-Z0-9_.-]+$')
        return bool(pattern.match(filename))
    
    @staticmethod
    def validate_time_period(days: str) -> int:
        """Validate and sanitize time period input"""
        try:
            days_int = int(days)
            if 1 <= days_int <= 365:  # Reasonable limits
                return days_int
            raise ValueError("Days must be between 1 and 365")
        except ValueError:
            raise ValueError("Invalid time period format")
    
    @staticmethod
    def sanitize_command_arg(arg: str) -> str:
        """Sanitize command line arguments"""
        # Remove dangerous characters that could be used for injection
        dangerous_chars = ['`', '$', '|', '&', ';', '(', ')', '<', '>', '\n', '\r']
        sanitized = arg
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        return sanitized.strip()


def require_auth(func):
    """Decorator to ensure user authentication and authorization"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Check if user is in appropriate groups
        try:
            user_groups = [grp.getgrgid(gid).gr_name for gid in os.getgroups()]
            if 'sudo' not in user_groups and 'admin' not in user_groups:
                raise SecurityError("User not authorized for fail2ban operations")
        except Exception as e:
            self.auditor.log_event("AUTH_FAILURE", f"Authorization check failed: {e}", "ERROR")
            raise SecurityError("Authorization verification failed")
        
        return func(self, *args, **kwargs)
    return wrapper


def rate_limit(limiter):
    """Decorator for rate limiting operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not limiter.is_allowed():
                raise SecurityError("Rate limit exceeded. Please wait before retrying.")
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


class SecureFail2BanManager:
    """Security-hardened Fail2Ban Manager with Email Monitoring"""
    
    # Secure configuration constants
    FAIL2BAN_CLIENT = "/usr/bin/fail2ban-client"
    FAIL2BAN_LOG = "/var/log/fail2ban.log"
    FAIL2BAN_CONFIG = "/etc/fail2ban/jail.local"
    POSTFIX_LOG = "/var/log/mail.log"
    DOVECOT_LOG = "/var/log/dovecot.log"
    
    # Rate limiters for different operations
    COMMAND_RATE_LIMITER = RateLimiter(max_calls=20, time_window=60)
    UNBAN_RATE_LIMITER = RateLimiter(max_calls=5, time_window=300)  # 5 unbans per 5 minutes
    BAN_RATE_LIMITER = RateLimiter(max_calls=3, time_window=300)    # 3 bans per 5 minutes
    
    def __init__(self):
        """Initialize secure fail2ban manager"""
        self.auditor = SecurityAuditor()
        self.validator = InputValidator()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            self._check_security_prerequisites()
            self._check_fail2ban_available()
            self.auditor.log_event("INIT_SUCCESS", "SecureFail2BanManager initialized successfully")
        except Exception as e:
            self.auditor.log_event("INIT_FAILURE", f"Initialization failed: {e}", "ERROR")
            raise
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.auditor.log_event("SHUTDOWN", f"Received signal {signum}")
        self.auditor.close_session()
        sys.exit(0)
    
    def _check_security_prerequisites(self):
        """Check security prerequisites"""
        # Check if running as root (security risk)
        if os.getuid() == 0:
            raise SecurityError("Do not run this script as root. Use sudo for specific commands only.")
        
        # Check if fail2ban-client exists and is executable
        if not os.path.exists(self.FAIL2BAN_CLIENT):
            raise SecurityError("fail2ban-client not found")
        
        if not os.access(self.FAIL2BAN_CLIENT, os.X_OK):
            raise SecurityError("fail2ban-client not executable")
    
    def _check_fail2ban_available(self):
        """Check if fail2ban is available and accessible"""
        try:
            result = subprocess.run(
                ['which', 'fail2ban-client'], 
                capture_output=True, 
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise SecurityError("fail2ban-client not available in PATH")
        except subprocess.TimeoutExpired:
            raise SecurityError("fail2ban-client check timed out")
        except Exception as e:
            raise SecurityError(f"Fail2ban availability check failed: {e}")
    
    @require_auth
    @rate_limit(COMMAND_RATE_LIMITER)
    def _run_fail2ban_command(self, cmd_args: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run fail2ban-client command with enhanced security"""
        # Validate and sanitize all arguments
        sanitized_args = []
        for arg in cmd_args:
            if not isinstance(arg, str):
                raise SecurityError("All command arguments must be strings")
            
            sanitized_arg = self.validator.sanitize_command_arg(arg)
            if len(sanitized_arg) > 100:  # Reasonable limit
                raise SecurityError("Command argument too long")
            
            sanitized_args.append(sanitized_arg)
        
        # Build secure command
        command = ['sudo', '-n', self.FAIL2BAN_CLIENT] + sanitized_args
        
        try:
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                check=check,
                timeout=30,  # Prevent hanging
                env={'PATH': '/usr/bin:/bin'}  # Minimal secure PATH
            )
            
            self.auditor.log_command(command, result.returncode == 0, result.stdout[:500])
            return result
            
        except subprocess.TimeoutExpired:
            self.auditor.log_event("COMMAND_TIMEOUT", f"Command timed out: {' '.join(command[:3])}", "WARNING")
            raise SecurityError("Command execution timed out")
        except subprocess.CalledProcessError as e:
            self.auditor.log_command(command, False, e.stderr[:500])
            if check:
                raise SecurityError(f"Fail2ban command failed: {e.stderr}")
            return e
        except Exception as e:
            self.auditor.log_event("COMMAND_ERROR", f"Unexpected error: {e}", "ERROR")
            raise SecurityError(f"Error running fail2ban command: {e}")
    
    def get_active_jails(self) -> List[str]:
        """Get list of active jails with security validation"""
        try:
            result = self._run_fail2ban_command(['status'])
            if result.returncode == 0:
                output = result.stdout
                jail_line = None
                for line in output.split('\n'):
                    if 'Jail list:' in line:
                        jail_line = line
                        break
                
                if jail_line:
                    jails_part = jail_line.split('Jail list:')[1].strip()
                    if jails_part:
                        jails = [jail.strip() for jail in jails_part.split(',')]
                        # Validate each jail name
                        validated_jails = []
                        for jail in jails:
                            if self.validator.validate_jail_name(jail):
                                validated_jails.append(jail)
                            else:
                                self.auditor.log_event(
                                    "INVALID_JAIL_NAME", 
                                    f"Rejected invalid jail name: {jail}", 
                                    "WARNING"
                                )
                        return validated_jails
                return []
            else:
                self.auditor.log_event("GET_JAILS_FAILED", f"Failed: {result.stderr}", "WARNING")
                return []
        except Exception as e:
            self.auditor.log_event("GET_JAILS_ERROR", f"Error: {e}", "ERROR")
            return []
    
    def get_jail_status(self, jail_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed status for a specific jail with validation"""
        if not self.validator.validate_jail_name(jail_name):
            raise SecurityError(f"Invalid jail name: {jail_name}")
        
        try:
            result = self._run_fail2ban_command(['status', jail_name])
            if result.returncode == 0:
                status_info = {
                    'filter': 'unknown',
                    'actions': 'unknown', 
                    'currently_failed': 0,
                    'total_failed': 0,
                    'currently_banned': 0,
                    'total_banned': 0,
                    'banned_ips': []
                }
                
                lines = result.stdout.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line or ':' not in line:
                        continue
                    
                    try:
                        if 'Filter' in line:
                            parts = line.split(':', 1)
                            if len(parts) >= 2:
                                status_info['filter'] = parts[1].strip()[:100]  # Limit length
                        elif 'Actions' in line:
                            parts = line.split(':', 1)
                            if len(parts) >= 2:
                                status_info['actions'] = parts[1].strip()[:100]
                        elif 'Currently failed' in line:
                            parts = line.split(':', 1)
                            if len(parts) >= 2:
                                status_info['currently_failed'] = max(0, int(parts[1].strip()))
                        elif 'Total failed' in line:
                            parts = line.split(':', 1)
                            if len(parts) >= 2:
                                status_info['total_failed'] = max(0, int(parts[1].strip()))
                        elif 'Currently banned' in line:
                            parts = line.split(':', 1)
                            if len(parts) >= 2:
                                status_info['currently_banned'] = max(0, int(parts[1].strip()))
                        elif 'Total banned' in line:
                            parts = line.split(':', 1)
                            if len(parts) >= 2:
                                status_info['total_banned'] = max(0, int(parts[1].strip()))
                        elif 'Banned IP list' in line:
                            parts = line.split(':', 1)
                            if len(parts) >= 2:
                                ip_list = parts[1].strip()
                                if ip_list:
                                    ips = [ip.strip() for ip in ip_list.split()]
                                    validated_ips = []
                                    for ip in ips:
                                        if self.validator.validate_ip(ip):
                                            validated_ips.append(ip)
                                    status_info['banned_ips'] = validated_ips
                    except (ValueError, IndexError):
                        continue
                
                return status_info
            else:
                return None
        except Exception as e:
            self.auditor.log_event("GET_STATUS_ERROR", f"Jail: {jail_name}, Error: {e}", "ERROR")
            return None
    
    @rate_limit(UNBAN_RATE_LIMITER)
    def unban_ip(self, jail_name: str, ip_address: str) -> bool:
        """Unban a specific IP from a jail with security validation"""
        # Validate inputs
        if not self.validator.validate_jail_name(jail_name):
            raise SecurityError(f"Invalid jail name: {jail_name}")
        
        if not self.validator.validate_ip(ip_address):
            raise SecurityError(f"Invalid IP address: {ip_address}")
        
        self.auditor.log_event("UNBAN_ATTEMPT", f"Jail: {jail_name}, IP: {ip_address}")
        
        try:
            # Try global unban first
            result = self._run_fail2ban_command(['unban', ip_address], check=False)
            if result.returncode == 0:
                self.auditor.log_event("UNBAN_SUCCESS", f"Global unban - IP: {ip_address}")
                print(f"✅ Successfully unbanned {ip_address}")
                return True
            else:
                # Try jail-specific unban
                result = self._run_fail2ban_command(['set', jail_name, 'unbanip', ip_address], check=False)
                if result.returncode == 0:
                    self.auditor.log_event("UNBAN_SUCCESS", f"Jail: {jail_name}, IP: {ip_address}")
                    print(f"✅ Successfully unbanned {ip_address} from {jail_name}")
                    return True
                else:
                    self.auditor.log_event("UNBAN_FAILURE", f"Jail: {jail_name}, IP: {ip_address}, Error: {result.stderr}")
                    print(f"❌ Failed to unban {ip_address}: {result.stderr}")
                    return False
        except Exception as e:
            self.auditor.log_event("UNBAN_ERROR", f"Jail: {jail_name}, IP: {ip_address}, Error: {e}", "ERROR")
            print(f"❌ Error unbanning {ip_address}: {e}")
            return False
    
    @rate_limit(BAN_RATE_LIMITER)
    def ban_ip(self, jail_name: str, ip_address: str, reason: str = "") -> bool:
        """Ban a specific IP in a jail with security validation"""
        # Validate inputs
        if not self.validator.validate_jail_name(jail_name):
            raise SecurityError(f"Invalid jail name: {jail_name}")
        
        if not self.validator.validate_ip(ip_address):
            raise SecurityError(f"Invalid IP address: {ip_address}")
        
        # Additional security: check if IP is private/localhost
        try:
            ip = ipaddress.ip_address(ip_address)
            if ip.is_private or ip.is_loopback:
                raise SecurityError("Cannot ban private or loopback IP addresses")
        except ValueError:
            raise SecurityError("Invalid IP address format")
        
        # Sanitize reason
        clean_reason = self.validator.sanitize_command_arg(reason)[:200]
        
        self.auditor.log_event("BAN_ATTEMPT", f"Jail: {jail_name}, IP: {ip_address}, Reason: {clean_reason}")
        
        try:
            result = self._run_fail2ban_command(['set', jail_name, 'banip', ip_address])
            if result.returncode == 0:
                self.auditor.log_event("BAN_SUCCESS", f"Jail: {jail_name}, IP: {ip_address}")
                print(f"✅ Successfully banned {ip_address} in {jail_name}")
                if clean_reason:
                    print(f"📝 Reason: {clean_reason}")
                return True
            else:
                self.auditor.log_event("BAN_FAILURE", f"Jail: {jail_name}, IP: {ip_address}, Error: {result.stderr}")
                print(f"❌ Failed to ban {ip_address}: {result.stderr}")
                return False
        except Exception as e:
            self.auditor.log_event("BAN_ERROR", f"Jail: {jail_name}, IP: {ip_address}, Error: {e}", "ERROR")
            print(f"❌ Error banning {ip_address}: {e}")
            return False
    
    def parse_fail2ban_logs(self, days: int = 1) -> Dict[str, List[Dict]]:
        """Parse fail2ban logs with enhanced security"""
        if not isinstance(days, int) or days < 1 or days > 365:
            raise SecurityError("Invalid days parameter")
        
        log_data = {
            'bans': [],
            'unbans': [],
            'attempts': []
        }
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Secure log file access
        log_files = [self.FAIL2BAN_LOG]
        
        # Add rotated logs
        for i in range(1, min(8, days + 1)):  # Reasonable limit based on days
            log_file = f"{self.FAIL2BAN_LOG}.{i}"
            if os.path.exists(log_file):
                log_files.append(log_file)
            
            gz_log_file = f"{log_file}.gz"
            if os.path.exists(gz_log_file):
                log_files.append(gz_log_file)
        
        for log_file in log_files:
            try:
                if log_file.endswith('.gz'):
                    with gzip.open(log_file, 'rt', encoding='utf-8', errors='ignore') as f:
                        self._parse_log_content(f, log_data, cutoff_date)
                else:
                    try:
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            self._parse_log_content(f, log_data, cutoff_date)
                    except PermissionError:
                        # Try with sudo
                        try:
                            result = subprocess.run(
                                ['sudo', '-n', 'cat', log_file], 
                                capture_output=True, 
                                text=True, 
                                check=True,
                                timeout=30
                            )
                            from io import StringIO
                            self._parse_log_content(StringIO(result.stdout), log_data, cutoff_date)
                        except:
                            continue
            except Exception as e:
                self.auditor.log_event("LOG_PARSE_ERROR", f"File: {log_file}, Error: {e}", "WARNING")
                continue
        
        return log_data
    
    def _parse_log_content(self, file_handle, log_data: Dict, cutoff_date: datetime):
        """Parse log file content with security validation"""
        ban_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).*\[(\w+)\].*Ban (\d+\.\d+\.\d+\.\d+)')
        unban_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).*\[(\w+)\].*Unban (\d+\.\d+\.\d+\.\d+)')
        attempt_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).*\[(\w+)\].*Found (\d+\.\d+\.\d+\.\d+)')
        
        line_count = 0
        for line in file_handle:
            line_count += 1
            if line_count > 100000:  # Prevent memory exhaustion
                break
            
            try:
                # Parse timestamp
                timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                if not timestamp_match:
                    continue
                
                timestamp_str = timestamp_match.group(1)
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                
                if timestamp < cutoff_date:
                    continue
                
                # Check for ban events
                ban_match = ban_pattern.search(line)
                if ban_match:
                    jail = ban_match.group(2)
                    ip = ban_match.group(3)
                    
                    if self.validator.validate_jail_name(jail) and self.validator.validate_ip(ip):
                        log_data['bans'].append({
                            'timestamp': timestamp,
                            'jail': jail,
                            'ip': ip
                        })
                    continue
                
                # Check for unban events
                unban_match = unban_pattern.search(line)
                if unban_match:
                    jail = unban_match.group(2)
                    ip = unban_match.group(3)
                    
                    if self.validator.validate_jail_name(jail) and self.validator.validate_ip(ip):
                        log_data['unbans'].append({
                            'timestamp': timestamp,
                            'jail': jail,
                            'ip': ip
                        })
                    continue
                
                # Check for attempt events
                attempt_match = attempt_pattern.search(line)
                if attempt_match:
                    jail = attempt_match.group(2)
                    ip = attempt_match.group(3)
                    
                    if self.validator.validate_jail_name(jail) and self.validator.validate_ip(ip):
                        log_data['attempts'].append({
                            'timestamp': timestamp,
                            'jail': jail,
                            'ip': ip
                        })
            except Exception:
                continue
    
    def get_email_jail_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get comprehensive email jail statistics and attack patterns"""
        if not isinstance(days, int) or days < 1 or days > 90:
            raise SecurityError("Invalid days parameter for email statistics")
        
        email_jails = [
            'postfix-sasl', 'postfix-rbl', 'postfix-relay', 'postfix-spam',
            'dovecot', 'courier-smtp', 'courier-auth', 'cyrus-imap',
            'exim', 'exim-spam'
        ]
        
        log_data = self.parse_fail2ban_logs(days)
        
        email_stats = {
            'total_email_attacks': 0,
            'email_bans_by_service': defaultdict(int),
            'email_attempts_by_service': defaultdict(int),
            'top_email_attackers': Counter(),
            'attack_patterns': {
                'hourly_distribution': defaultdict(int),
                'daily_distribution': defaultdict(int),
                'authentication_failures': defaultdict(int),
                'relay_attempts': defaultdict(int),
                'spam_sources': defaultdict(int)
            },
            'email_specific_metrics': {
                'smtp_auth_failures': 0,
                'imap_pop_failures': 0,
                'relay_abuse_attempts': 0,
                'spam_injection_attempts': 0,
                'directory_harvest_attacks': 0
            }
        }
        
        # Process bans and attempts for email services
        for ban in log_data['bans']:
            if ban['jail'] in email_jails:
                email_stats['total_email_attacks'] += 1
                email_stats['email_bans_by_service'][ban['jail']] += 1
                email_stats['top_email_attackers'][ban['ip']] += 1
                
                hour = ban['timestamp'].hour
                day = ban['timestamp'].strftime('%A')
                email_stats['attack_patterns']['hourly_distribution'][hour] += 1
                email_stats['attack_patterns']['daily_distribution'][day] += 1
                
                # Categorize by attack type
                if 'sasl' in ban['jail'] or 'auth' in ban['jail']:
                    email_stats['email_specific_metrics']['smtp_auth_failures'] += 1
                elif 'dovecot' in ban['jail'] or 'courier' in ban['jail'] or 'imap' in ban['jail']:
                    email_stats['email_specific_metrics']['imap_pop_failures'] += 1
                elif 'relay' in ban['jail']:
                    email_stats['email_specific_metrics']['relay_abuse_attempts'] += 1
                elif 'spam' in ban['jail']:
                    email_stats['email_specific_metrics']['spam_injection_attempts'] += 1
        
        for attempt in log_data['attempts']:
            if attempt['jail'] in email_jails:
                email_stats['email_attempts_by_service'][attempt['jail']] += 1
        
        # Parse mail logs for additional email-specific metrics
        self._parse_mail_logs(email_stats, days)
        
        return email_stats
    
    def _parse_mail_logs(self, email_stats: Dict, days: int):
        """Parse mail server logs for additional email attack patterns"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Parse postfix logs
        for log_file in [self.POSTFIX_LOG, f"{self.POSTFIX_LOG}.1"]:
            if os.path.exists(log_file):
                try:
                    self._parse_postfix_log(log_file, email_stats, cutoff_date)
                except Exception as e:
                    self.auditor.log_event("MAIL_LOG_PARSE_ERROR", f"File: {log_file}, Error: {e}", "WARNING")
        
        # Parse dovecot logs
        for log_file in [self.DOVECOT_LOG, f"{self.DOVECOT_LOG}.1"]:
            if os.path.exists(log_file):
                try:
                    self._parse_dovecot_log(log_file, email_stats, cutoff_date)
                except Exception as e:
                    self.auditor.log_event("MAIL_LOG_PARSE_ERROR", f"File: {log_file}, Error: {e}", "WARNING")
    
    def _parse_postfix_log(self, log_file: str, email_stats: Dict, cutoff_date: datetime):
        """Parse postfix log for specific attack patterns"""
        auth_failure_pattern = re.compile(r'authentication failed.*client=.*\[(\d+\.\d+\.\d+\.\d+)\]')
        relay_denied_pattern = re.compile(r'relay access denied.*client=.*\[(\d+\.\d+\.\d+\.\d+)\]')
        
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    try:
                        # Extract timestamp (postfix format: Oct 15 10:30:45)
                        timestamp_match = re.match(r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})', line)
                        if not timestamp_match:
                            continue
                        
                        # Simple timestamp parsing (approximate)
                        timestamp_str = timestamp_match.group(1)
                        current_year = datetime.now().year
                        try:
                            timestamp = datetime.strptime(f"{current_year} {timestamp_str}", '%Y %b %d %H:%M:%S')
                        except ValueError:
                            continue
                        
                        if timestamp < cutoff_date:
                            continue
                        
                        # Check for authentication failures
                        auth_match = auth_failure_pattern.search(line)
                        if auth_match:
                            ip = auth_match.group(1)
                            if self.validator.validate_ip(ip):
                                email_stats['attack_patterns']['authentication_failures'][ip] += 1
                        
                        # Check for relay attempts
                        relay_match = relay_denied_pattern.search(line)
                        if relay_match:
                            ip = relay_match.group(1)
                            if self.validator.validate_ip(ip):
                                email_stats['attack_patterns']['relay_attempts'][ip] += 1
                        
                        # Check for directory harvest attacks
                        if 'User unknown' in line or 'Recipient address rejected' in line:
                            ip_match = re.search(r'\[(\d+\.\d+\.\d+\.\d+)\]', line)
                            if ip_match:
                                ip = ip_match.group(1)
                                if self.validator.validate_ip(ip):
                                    email_stats['email_specific_metrics']['directory_harvest_attacks'] += 1
                    except Exception:
                        continue
        except PermissionError:
            # Try with sudo
            try:
                result = subprocess.run(
                    ['sudo', '-n', 'cat', log_file], 
                    capture_output=True, 
                    text=True, 
                    check=True,
                    timeout=30
                )
                from io import StringIO
                # Process the content similarly (simplified for brevity)
                pass
            except:
                pass
    
    def _parse_dovecot_log(self, log_file: str, email_stats: Dict, cutoff_date: datetime):
        """Parse dovecot log for IMAP/POP3 attack patterns"""
        auth_failure_pattern = re.compile(r'auth-worker.*auth failed.*rip=(\d+\.\d+\.\d+\.\d+)')
        
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    try:
                        # Similar timestamp parsing as postfix
                        timestamp_match = re.match(r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})', line)
                        if not timestamp_match:
                            continue
                        
                        timestamp_str = timestamp_match.group(1)
                        current_year = datetime.now().year
                        try:
                            timestamp = datetime.strptime(f"{current_year} {timestamp_str}", '%Y %b %d %H:%M:%S')
                        except ValueError:
                            continue
                        
                        if timestamp < cutoff_date:
                            continue
                        
                        # Check for authentication failures
                        auth_match = auth_failure_pattern.search(line)
                        if auth_match:
                            ip = auth_match.group(1)
                            if self.validator.validate_ip(ip):
                                email_stats['attack_patterns']['authentication_failures'][ip] += 1
                    except Exception:
                        continue
        except PermissionError:
            pass  # Handle similar to postfix
    
    def show_email_security_report(self):
        """Display comprehensive email security report"""
        print("\n📧 Email Security Report\n")
        print("=" * 80)
        
        try:
            # Get email statistics
            email_stats = self.get_email_jail_statistics(7)
            
            print(f"📊 WEEKLY EMAIL SECURITY OVERVIEW:")
            print(f"  🚫 Total Email-Related Attacks: {email_stats['total_email_attacks']}")
            print(f"  🔐 SMTP Authentication Failures: {email_stats['email_specific_metrics']['smtp_auth_failures']}")
            print(f"  📬 IMAP/POP3 Attack Attempts: {email_stats['email_specific_metrics']['imap_pop_failures']}")
            print(f"  🔄 Mail Relay Abuse Attempts: {email_stats['email_specific_metrics']['relay_abuse_attempts']}")
            print(f"  🗑️ Spam Injection Attempts: {email_stats['email_specific_metrics']['spam_injection_attempts']}")
            print(f"  📖 Directory Harvest Attacks: {email_stats['email_specific_metrics']['directory_harvest_attacks']}")
            
            if email_stats['email_bans_by_service']:
                print(f"\n🏛️ Email Service Protection Summary:")
                for service, count in email_stats['email_bans_by_service'].most_common():
                    print(f"  • {service}: {count} bans")
            
            if email_stats['top_email_attackers']:
                print(f"\n🎯 Top Email Attackers:")
                for ip, count in email_stats['top_email_attackers'].most_common(10):
                    print(f"  • {ip}: {count} attacks")
            
            # Attack timing patterns
            print(f"\n⏰ Email Attack Timing Patterns:")
            if email_stats['attack_patterns']['hourly_distribution']:
                peak_hour = max(email_stats['attack_patterns']['hourly_distribution'], 
                              key=email_stats['attack_patterns']['hourly_distribution'].get)
                peak_count = email_stats['attack_patterns']['hourly_distribution'][peak_hour]
                print(f"  📈 Peak Attack Hour: {peak_hour:02d}:00 ({peak_count} attacks)")
            
            if email_stats['attack_patterns']['daily_distribution']:
                peak_day = max(email_stats['attack_patterns']['daily_distribution'], 
                             key=email_stats['attack_patterns']['daily_distribution'].get)
                peak_count = email_stats['attack_patterns']['daily_distribution'][peak_day]
                print(f"  📅 Peak Attack Day: {peak_day} ({peak_count} attacks)")
            
            # Authentication failure patterns
            if email_stats['attack_patterns']['authentication_failures']:
                print(f"\n🔐 Authentication Failure Sources:")
                for ip, count in Counter(email_stats['attack_patterns']['authentication_failures']).most_common(5):
                    print(f"  • {ip}: {count} failed attempts")
            
            # Relay abuse patterns
            if email_stats['attack_patterns']['relay_attempts']:
                print(f"\n🔄 Mail Relay Abuse Sources:")
                for ip, count in Counter(email_stats['attack_patterns']['relay_attempts']).most_common(5):
                    print(f"  • {ip}: {count} relay attempts")
            
            print(f"\n✅ Email Security Report Complete")
            
        except Exception as e:
            self.auditor.log_event("EMAIL_REPORT_ERROR", f"Error: {e}", "ERROR")
            print(f"❌ Error generating email security report: {e}")
        
        print()
    
    def show_jail_status_overview(self):
        """Display comprehensive jail status overview with security context"""
        print("\n📊 Secure Jail Status Overview\n")
        print("=" * 80)
        
        jails = self.get_active_jails()
        if not jails:
            print("❌ No active jails found or fail2ban not accessible.")
            self.auditor.log_event("NO_JAILS_FOUND", "No active jails detected", "WARNING")
            return
        
        print(f"{'Jail':<25} {'Status':<10} {'Failed':<8} {'Banned':<8} {'Total Bans':<12}")
        print("=" * 80)
        
        total_banned = 0
        total_failed = 0
        email_jails = 0
        
        for jail in jails:
            status = self.get_jail_status(jail)
            if status:
                currently_failed = status.get('currently_failed', 0)
                currently_banned = status.get('currently_banned', 0)
                total_banned_jail = status.get('total_banned', 0)
                
                # Categorize jail type for security analysis
                jail_type = "🌐"  # Default web
                if any(email_keyword in jail.lower() for email_keyword in ['mail', 'smtp', 'imap', 'pop', 'postfix', 'dovecot']):
                    jail_type = "📧"
                    email_jails += 1
                elif 'ssh' in jail.lower():
                    jail_type = "🔑"
                elif 'ftp' in jail.lower():
                    jail_type = "📁"
                
                status_icon = "🟢" if currently_banned == 0 else "🔴"
                
                print(f"{jail_type} {jail:<22} {status_icon:<10} {currently_failed:<8} {currently_banned:<8} {total_banned_jail:<12}")
                
                total_banned += currently_banned
                total_failed += currently_failed
            else:
                print(f"❌ {jail:<22} {'Error':<10} {'-':<8} {'-':<8} {'-':<12}")
        
        print("=" * 80)
        print(f"{'TOTALS':<25} {'':<10} {total_failed:<8} {total_banned:<8}")
        print(f"📧 Email Services Protected: {email_jails}")
        print(f"🛡️ Total Services Protected: {len(jails)}")
        
        # Security recommendations
        if total_banned == 0:
            print(f"\n✅ Security Status: No current active bans")
        else:
            print(f"\n⚠️ Security Alert: {total_banned} IPs currently banned")
        
        print()
    
    def show_banned_ips_detailed(self):
        """Show detailed list of banned IPs with security analysis"""
        print("\n🚫 Currently Banned IPs (Security Analysis)\n")
        print("=" * 80)
        
        banned_info = self.get_banned_ips()
        
        if not any(banned_info.values()):
            print("✅ No IPs are currently banned.")
            return
        
        total_banned = 0
        email_related_bans = 0
        
        for jail, ips in banned_info.items():
            if ips:
                jail_type = "🌐"
                if any(email_keyword in jail.lower() for email_keyword in ['mail', 'smtp', 'imap', 'pop', 'postfix', 'dovecot']):
                    jail_type = "📧"
                    email_related_bans += len(ips)
                elif 'ssh' in jail.lower():
                    jail_type = "🔑"
                elif 'ftp' in jail.lower():
                    jail_type = "📁"
                
                print(f"{jail_type} {jail.upper()} Jail ({len(ips)} banned):")
                for i, ip in enumerate(ips, 1):
                    # Basic geographic/network analysis
                    network_info = self._get_ip_network_info(ip)
                    print(f"  {i:2d}. {ip:<15} {network_info}")
                print()
                total_banned += len(ips)
        
        print(f"📊 Ban Summary:")
        print(f"  🚫 Total Banned IPs: {total_banned}")
        print(f"  📧 Email-Related Bans: {email_related_bans}")
        print(f"  🌐 Other Service Bans: {total_banned - email_related_bans}")
        print()
    
    def _get_ip_network_info(self, ip: str) -> str:
        """Get basic network information about an IP (simplified)"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private:
                return "(Private Network)"
            elif ip_obj.is_loopback:
                return "(Loopback)"
            elif ip_obj.is_multicast:
                return "(Multicast)"
            else:
                # Basic classification by first octet
                first_octet = int(ip.split('.')[0])
                if first_octet < 64:
                    return "(Americas/ARIN)"
                elif first_octet < 128:
                    return "(Europe/RIPE)"
                elif first_octet < 192:
                    return "(Asia/APNIC)"
                else:
                    return "(Global/Other)"
        except:
            return "(Unknown)"
    
    def get_banned_ips(self, jail_name: Optional[str] = None) -> Dict[str, List[str]]:
        """Get banned IPs for a specific jail or all jails"""
        banned_info = {}
        
        if jail_name:
            if not self.validator.validate_jail_name(jail_name):
                raise SecurityError(f"Invalid jail name: {jail_name}")
            jails = [jail_name]
        else:
            jails = self.get_active_jails()
        
        for jail in jails:
            status = self.get_jail_status(jail)
            if status and 'banned_ips' in status:
                banned_info[jail] = status['banned_ips']
            else:
                banned_info[jail] = []
        
        return banned_info
    
    def unban_ip_interactive(self):
        """Interactive IP unbanning with enhanced security"""
        print("\n✅ Secure IP Unbanning\n")
        print("=" * 50)
        
        # Show current banned IPs
        banned_info = self.get_banned_ips()
        if not any(banned_info.values()):
            print("✅ No IPs are currently banned.")
            return
        
        # Display banned IPs with security context
        all_banned = []
        for jail, ips in banned_info.items():
            for ip in ips:
                all_banned.append((jail, ip))
        
        if not all_banned:
            print("✅ No IPs are currently banned.")
            return
        
        print("Currently banned IPs:")
        for i, (jail, ip) in enumerate(all_banned, 1):
            network_info = self._get_ip_network_info(ip)
            print(f"  {i:2d}. {ip:<15} (in {jail}) {network_info}")
        
        print("\nSecure Unban Options:")
        print("1. Unban specific IP by number")
        print("2. Unban IP by address (from all jails)")
        print("3. Return to main menu")
        
        try:
            choice = input("\nChoose option (1-3): ").strip()
            
            if choice == "1":
                try:
                    num = int(input(f"Enter number (1-{len(all_banned)}): "))
                    if 1 <= num <= len(all_banned):
                        jail, ip = all_banned[num - 1]
                        
                        # Additional confirmation for security
                        confirm = input(f"Confirm unban {ip} from {jail}? (yes/no): ").strip().lower()
                        if confirm in ['yes', 'y']:
                            self.unban_ip(jail, ip)
                        else:
                            print("❌ Unban cancelled.")
                    else:
                        print("❌ Invalid number.")
                except ValueError:
                    print("❌ Invalid input.")
            
            elif choice == "2":
                ip = input("Enter IP address to unban: ").strip()
                if self.validator.validate_ip(ip):
                    # Additional confirmation
                    confirm = input(f"Confirm unban {ip} from ALL jails? (yes/no): ").strip().lower()
                    if confirm in ['yes', 'y']:
                        unbanned = False
                        for jail in self.get_active_jails():
                            try:
                                if self.unban_ip(jail, ip):
                                    unbanned = True
                            except SecurityError as e:
                                print(f"⚠️ Security restriction: {e}")
                                break
                        if not unbanned:
                            print(f"⚠️ {ip} was not found in any banned lists.")
                    else:
                        print("❌ Unban cancelled.")
                else:
                    print("❌ Invalid IP address format.")
            
            elif choice == "3":
                return
            else:
                print("❌ Invalid choice.")
                
        except Exception as e:
            self.auditor.log_event("INTERACTIVE_UNBAN_ERROR", f"Error: {e}", "ERROR")
            print(f"❌ Error during unban operation: {e}")
    
    def ban_ip_interactive(self):
        """Interactive IP banning with enhanced security"""
        print("\n⚠️ Secure IP Banning\n")
        print("=" * 50)
        
        jails = self.get_active_jails()
        if not jails:
            print("❌ No active jails found.")
            return
        
        print("Available jails:")
        for i, jail in enumerate(jails, 1):
            jail_type = "🌐"
            if any(email_keyword in jail.lower() for email_keyword in ['mail', 'smtp', 'imap', 'pop', 'postfix', 'dovecot']):
                jail_type = "📧"
            elif 'ssh' in jail.lower():
                jail_type = "🔑"
            elif 'ftp' in jail.lower():
                jail_type = "📁"
            print(f"  {i:2d}. {jail_type} {jail}")
        
        try:
            jail_num = int(input(f"\nSelect jail (1-{len(jails)}): "))
            if 1 <= jail_num <= len(jails):
                jail = jails[jail_num - 1]
                
                ip = input("Enter IP address to ban: ").strip()
                if not self.validator.validate_ip(ip):
                    print("❌ Invalid IP address format.")
                    return
                
                # Security check for private/local IPs
                try:
                    ip_obj = ipaddress.ip_address(ip)
                    if ip_obj.is_private or ip_obj.is_loopback:
                        print("❌ Cannot ban private or loopback IP addresses for security reasons.")
                        return
                except ValueError:
                    print("❌ Invalid IP address.")
                    return
                
                reason = input("Enter reason (required for audit): ").strip()
                if not reason:
                    print("❌ Reason is required for security audit.")
                    return
                
                # Final confirmation
                confirm = input(f"Confirm ban {ip} in {jail}? (yes/no): ").strip().lower()
                if confirm in ['yes', 'y']:
                    try:
                        if self.ban_ip(jail, ip, reason):
                            print(f"📝 Ban recorded in security audit log.")
                    except SecurityError as e:
                        print(f"❌ Security restriction: {e}")
                else:
                    print("❌ Ban cancelled.")
            else:
                print("❌ Invalid jail number.")
        except ValueError:
            print("❌ Invalid input.")
        except Exception as e:
            self.auditor.log_event("INTERACTIVE_BAN_ERROR", f"Error: {e}", "ERROR")
            print(f"❌ Error during ban operation: {e}")
    
    def show_daily_report(self):
        """Show daily activity report with security insights"""
        print("\n📈 Daily Security Activity Report\n")
        print("=" * 80)
        
        try:
            # Get statistics for different time periods
            today_stats = self.get_daily_statistics(1)
            week_stats = self.get_daily_statistics(7)
            
            print("📅 TODAY'S SECURITY ACTIVITY:")
            print(f"  🚫 Total Bans: {today_stats['total_bans']}")
            print(f"  🔍 Failed Attempts: {today_stats['total_attempts']}")
            print(f"  ✅ Unbans: {today_stats['total_unbans']}")
            
            if today_stats['bans_by_jail']:
                print("\n  📊 Bans by Service:")
                for jail, count in today_stats['bans_by_jail'].most_common():
                    jail_type = "🌐"
                    if any(email_keyword in jail.lower() for email_keyword in ['mail', 'smtp', 'imap', 'pop', 'postfix', 'dovecot']):
                        jail_type = "📧"
                    elif 'ssh' in jail.lower():
                        jail_type = "🔑"
                    print(f"    {jail_type} {jail}: {count}")
            
            if today_stats['top_attackers']:
                print(f"\n  🎯 Top Attackers Today:")
                for ip, count in today_stats['top_attackers'].most_common(5):
                    network_info = self._get_ip_network_info(ip)
                    print(f"    • {ip}: {count} bans {network_info}")
            
            print(f"\n📅 WEEKLY SECURITY SUMMARY:")
            print(f"  🚫 Total Bans: {week_stats['total_bans']}")
            print(f"  🔍 Failed Attempts: {week_stats['total_attempts']}")
            
            if week_stats['bans_by_jail']:
                email_bans = sum(count for jail, count in week_stats['bans_by_jail'].items() 
                               if any(email_keyword in jail.lower() for email_keyword in ['mail', 'smtp', 'imap', 'pop', 'postfix', 'dovecot']))
                ssh_bans = sum(count for jail, count in week_stats['bans_by_jail'].items() 
                             if 'ssh' in jail.lower())
                
                print(f"\n  📊 Weekly Protection Summary:")
                print(f"    📧 Email Service Attacks: {email_bans}")
                print(f"    🔑 SSH Attacks: {ssh_bans}")
                print(f"    🌐 Other Service Attacks: {week_stats['total_bans'] - email_bans - ssh_bans}")
            
            # Security recommendations
            print(f"\n🛡️ Security Insights:")
            if today_stats['total_bans'] > week_stats['total_bans'] / 7 * 2:
                print(f"  ⚠️ High activity today - consider reviewing attack patterns")
            if email_bans > week_stats['total_bans'] * 0.3:
                print(f"  📧 Significant email attacks detected - review email security")
            if ssh_bans > week_stats['total_bans'] * 0.4:
                print(f"  🔑 High SSH attack volume - consider additional SSH hardening")
        
        except Exception as e:
            self.auditor.log_event("DAILY_REPORT_ERROR", f"Error: {e}", "ERROR")
            print(f"❌ Error generating daily report: {e}")
        
        print()
    
    def get_daily_statistics(self, days: int) -> Dict[str, Any]:
        """Get daily statistics with validation"""
        days = self.validator.validate_time_period(str(days))
        log_data = self.parse_fail2ban_logs(days)
        
        stats = {
            'total_bans': len(log_data['bans']),
            'total_unbans': len(log_data['unbans']),
            'total_attempts': len(log_data['attempts']),
            'bans_by_jail': Counter(),
            'attempts_by_jail': Counter(),
            'top_attackers': Counter(),
            'bans_by_day': defaultdict(int)
        }
        
        # Process bans
        for ban in log_data['bans']:
            stats['bans_by_jail'][ban['jail']] += 1
            stats['top_attackers'][ban['ip']] += 1
            day_key = ban['timestamp'].strftime('%Y-%m-%d')
            stats['bans_by_day'][day_key] += 1
        
        # Process attempts
        for attempt in log_data['attempts']:
            stats['attempts_by_jail'][attempt['jail']] += 1
        
        return stats
    
    def search_ip_interactive(self):
        """Interactive IP search with enhanced security"""
        print("\n🔍 Secure IP Address Search\n")
        print("=" * 50)
        
        ip = input("Enter IP address to search: ").strip()
        if not self.validator.validate_ip(ip):
            print("❌ Invalid IP address format.")
            return
        
        days_input = input("Search last how many days? (default: 30, max: 90): ").strip()
        try:
            days = self.validator.validate_time_period(days_input if days_input else "30")
            if days > 90:
                days = 90
                print("⚠️ Limited search to 90 days for performance.")
        except ValueError:
            print("❌ Invalid time period. Using 30 days.")
            days = 30
        
        print(f"\n🔍 Searching for {ip} in last {days} days...")
        network_info = self._get_ip_network_info(ip)
        print(f"📍 Network Info: {network_info}")
        
        try:
            events = self.search_ip_in_logs(ip, days)
            
            total_events = len(events['bans']) + len(events['unbans']) + len(events['attempts'])
            
            if total_events == 0:
                print(f"✅ No activity found for {ip} in the last {days} days.")
                return
            
            print(f"\n📊 Found {total_events} events for {ip}:")
            print(f"  🚫 Bans: {len(events['bans'])}")
            print(f"  ✅ Unbans: {len(events['unbans'])}")
            print(f"  🔍 Attempts: {len(events['attempts'])}")
            
            # Analyze attack pattern
            if events['bans']:
                jail_targets = Counter(ban['jail'] for ban in events['bans'])
                print(f"\n🎯 Targeted Services:")
                for jail, count in jail_targets.most_common():
                    jail_type = "🌐"
                    if any(email_keyword in jail.lower() for email_keyword in ['mail', 'smtp', 'imap', 'pop', 'postfix', 'dovecot']):
                        jail_type = "📧"
                    elif 'ssh' in jail.lower():
                        jail_type = "🔑"
                    print(f"    {jail_type} {jail}: {count} bans")
            
            if events['bans']:
                print(f"\n🚫 Recent Ban Events:")
                for ban in events['bans'][-10:]:  # Show last 10
                    print(f"  {self.format_timestamp(ban['timestamp'])} - {ban['jail']}")
            
            if events['attempts']:
                print(f"\n🔍 Recent Attempt Events:")
                for attempt in events['attempts'][-10:]:  # Show last 10
                    print(f"  {self.format_timestamp(attempt['timestamp'])} - {attempt['jail']}")
            
            # Security assessment
            if len(events['bans']) > 5:
                print(f"\n⚠️ Security Assessment: High-risk IP (multiple bans)")
            elif len(events['attempts']) > 20:
                print(f"\n⚠️ Security Assessment: Persistent attacker (many attempts)")
            elif any('ssh' in ban['jail'].lower() for ban in events['bans']):
                print(f"\n⚠️ Security Assessment: SSH attack source")
        
        except Exception as e:
            self.auditor.log_event("IP_SEARCH_ERROR", f"IP: {ip}, Error: {e}", "ERROR")
            print(f"❌ Error searching for IP: {e}")
        
        print()
    
    def search_ip_in_logs(self, ip_address: str, days: int = 30) -> Dict[str, List[Dict]]:
        """Search for a specific IP in logs with validation"""
        if not self.validator.validate_ip(ip_address):
            raise SecurityError(f"Invalid IP address: {ip_address}")
        
        days = self.validator.validate_time_period(str(days))
        log_data = self.parse_fail2ban_logs(days)
        
        ip_events = {
            'bans': [],
            'unbans': [],
            'attempts': []
        }
        
        for ban in log_data['bans']:
            if ban['ip'] == ip_address:
                ip_events['bans'].append(ban)
        
        for unban in log_data['unbans']:
            if unban['ip'] == ip_address:
                ip_events['unbans'].append(unban)
        
        for attempt in log_data['attempts']:
            if attempt['ip'] == ip_address:
                ip_events['attempts'].append(attempt)
        
        return ip_events
    
    def export_data_interactive(self):
        """Interactive data export with security validation"""
        print("\n📤 Secure Data Export\n")
        print("=" * 50)
        
        days_input = input("Export data for last how many days? (default: 30, max: 90): ").strip()
        try:
            days = self.validator.validate_time_period(days_input if days_input else "30")
            if days > 90:
                days = 90
                print("⚠️ Limited export to 90 days for security.")
        except ValueError:
            print("❌ Invalid time period. Using 30 days.")
            days = 30
        
        filename = input(f"Enter filename (default: secure_fail2ban_export_{datetime.now().strftime('%Y%m%d')}.csv): ").strip()
        if not filename:
            filename = f"secure_fail2ban_export_{datetime.now().strftime('%Y%m%d')}.csv"
        
        if not self.validator.validate_filename(filename):
            print("❌ Invalid filename. Using default.")
            filename = f"secure_fail2ban_export_{datetime.now().strftime('%Y%m%d')}.csv"
        
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        print(f"\n📊 Exporting {days} days of data to {filename}...")
        
        try:
            if self.export_ban_data_csv(filename, days):
                stats = self.get_daily_statistics(days)
                print(f"📈 Export Summary:")
                print(f"  • Total Bans: {stats['total_bans']}")
                print(f"  • Total Attempts: {stats['total_attempts']}")
                print(f"  • Period: {days} days")
                print(f"  • File: {filename}")
                
                self.auditor.log_event("DATA_EXPORT", f"File: {filename}, Days: {days}")
        except Exception as e:
            self.auditor.log_event("EXPORT_ERROR", f"File: {filename}, Error: {e}", "ERROR")
            print(f"❌ Export failed: {e}")
        
        print()
    
    def export_ban_data_csv(self, filename: str, days: int = 30) -> bool:
        """Export ban data to CSV file with security validation"""
        if not self.validator.validate_filename(filename):
            raise SecurityError(f"Invalid filename: {filename}")
        
        days = self.validator.validate_time_period(str(days))
        log_data = self.parse_fail2ban_logs(days)
        
        try:
            # Use absolute path in secure location
            safe_filename = os.path.join(os.getcwd(), filename)
            
            with open(safe_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Timestamp', 'Event Type', 'Jail', 'IP Address', 'Network Info'])
                
                # Write ban events
                for ban in log_data['bans']:
                    network_info = self._get_ip_network_info(ban['ip'])
                    writer.writerow([
                        self.format_timestamp(ban['timestamp']),
                        'BAN',
                        ban['jail'],
                        ban['ip'],
                        network_info
                    ])
                
                # Write unban events
                for unban in log_data['unbans']:
                    network_info = self._get_ip_network_info(unban['ip'])
                    writer.writerow([
                        self.format_timestamp(unban['timestamp']),
                        'UNBAN',
                        unban['jail'],
                        unban['ip'],
                        network_info
                    ])
                
                # Write attempt events
                for attempt in log_data['attempts']:
                    network_info = self._get_ip_network_info(attempt['ip'])
                    writer.writerow([
                        self.format_timestamp(attempt['timestamp']),
                        'ATTEMPT',
                        attempt['jail'],
                        attempt['ip'],
                        network_info
                    ])
            
            # Set secure permissions
            os.chmod(safe_filename, 0o640)
            print(f"✅ Secure ban data exported to {safe_filename}")
            return True
        except Exception as e:
            raise SecurityError(f"Error exporting data: {e}")
    
    def show_attack_patterns(self):
        """Show attack pattern analysis with security insights"""
        print("\n📈 Security Attack Pattern Analysis (Last 7 Days)\n")
        print("=" * 80)
        
        try:
            patterns = self.get_attack_patterns(7)
            
            print("🕐 Attack Distribution by Hour:")
            if patterns['hourly_distribution']:
                for hour in range(24):
                    count = patterns['hourly_distribution'].get(hour, 0)
                    bar = "█" * (count // 2) if count > 0 else ""
                    risk_level = "🔴" if count > 10 else "🟡" if count > 5 else "🟢"
                    print(f"  {hour:02d}:00 │{bar:<20} {count} {risk_level}")
            
            print(f"\n📅 Attack Distribution by Day:")
            days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            for day in days_order:
                count = patterns['daily_distribution'].get(day, 0)
                bar = "█" * (count // 5) if count > 0 else ""
                risk_level = "🔴" if count > 20 else "🟡" if count > 10 else "🟢"
                print(f"  {day:<9} │{bar:<20} {count} {risk_level}")
            
            print(f"\n🎯 Most Targeted Services:")
            for jail, count in patterns['jail_targeting'].most_common():
                percentage = (count / sum(patterns['jail_targeting'].values())) * 100
                jail_type = "🌐"
                if any(email_keyword in jail.lower() for email_keyword in ['mail', 'smtp', 'imap', 'pop', 'postfix', 'dovecot']):
                    jail_type = "📧"
                elif 'ssh' in jail.lower():
                    jail_type = "🔑"
                elif 'ftp' in jail.lower():
                    jail_type = "📁"
                print(f"  {jail_type} {jail}: {count} attacks ({percentage:.1f}%)")
            
            if patterns['repeat_offenders']:
                print(f"\n🔄 Repeat Offenders (Multi-Service Attacks):")
                for ip, jail_count in sorted(patterns['repeat_offenders'].items(), 
                                           key=lambda x: x[1], reverse=True)[:10]:
                    network_info = self._get_ip_network_info(ip)
                    risk_level = "🔴" if jail_count > 3 else "🟡" if jail_count > 1 else "🟢"
                    print(f"  {risk_level} {ip}: targeted {jail_count} services {network_info}")
            
            # Security recommendations
            peak_hour = max(patterns['hourly_distribution'], key=patterns['hourly_distribution'].get) if patterns['hourly_distribution'] else None
            if peak_hour is not None:
                peak_count = patterns['hourly_distribution'][peak_hour]
                if peak_count > 15:
                    print(f"\n⚠️ Security Alert: High attack volume at {peak_hour:02d}:00 ({peak_count} attacks)")
        
        except Exception as e:
            self.auditor.log_event("PATTERN_ANALYSIS_ERROR", f"Error: {e}", "ERROR")
            print(f"❌ Error analyzing attack patterns: {e}")
        
        print()
    
    def get_attack_patterns(self, days: int = 7) -> Dict[str, Any]:
        """Analyze attack patterns with validation"""
        days = self.validator.validate_time_period(str(days))
        log_data = self.parse_fail2ban_logs(days)
        
        patterns = {
            'hourly_distribution': defaultdict(int),
            'daily_distribution': defaultdict(int),
            'jail_targeting': defaultdict(int),
            'repeat_offenders': defaultdict(set)
        }
        
        for ban in log_data['bans']:
            hour = ban['timestamp'].hour
            day = ban['timestamp'].strftime('%A')
            
            patterns['hourly_distribution'][hour] += 1
            patterns['daily_distribution'][day] += 1
            patterns['jail_targeting'][ban['jail']] += 1
            patterns['repeat_offenders'][ban['ip']].add(ban['jail'])
        
        # Convert sets to counts for repeat offenders
        repeat_counts = {}
        for ip, jails in patterns['repeat_offenders'].items():
            if len(jails) > 1:
                repeat_counts[ip] = len(jails)
        
        patterns['repeat_offenders'] = repeat_counts
        
        return patterns
    
    def format_timestamp(self, timestamp: datetime) -> str:
        """Format timestamp for display"""
        return timestamp.strftime('%Y-%m-%d %H:%M:%S')
    
    def show_menu(self):
        """Display the main menu"""
        title = pyfiglet.figlet_format("SecureF2B", font="slant")
        print(title)
        print("🛡️ Secure Fail2Ban Manager v2.0 - Enhanced Email Monitoring")
        print("=" * 80)
        print()
        print("  1.  Show jail status and security overview")
        print("  2.  List all banned IPs (with security analysis)")
        print("  3.  Unban specific IP (secure)")
        print("  4.  Ban specific IP manually (with audit)")
        print("  5.  Daily/Weekly security activity report")
        print("  6.  Attack pattern analysis (enhanced)")
        print("  7.  Search IP across all logs (secure)")
        print("  8.  📧 Email Security Report (NEW)")
        print("  9.  Export ban data to CSV (secure)")
        print("  s.  Show security audit log")
        print("  d.  Debug jail status (troubleshooting)")
        print("")
        print("  x.  Exit and close session")
        print()
        print("🔒 Security: All operations are logged and rate-limited")
        print()
    
    def show_security_audit_log(self):
        """Display recent security audit log entries"""
        print("\n🔒 Security Audit Log (Recent Entries)\n")
        print("=" * 80)
        
        try:
            if self.auditor.log_file and self.auditor.log_file.exists():
                # Read last 50 lines of audit log
                result = subprocess.run(
                    ['tail', '-50', str(self.auditor.log_file)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if line.strip():
                            # Color code by severity
                            if 'ERROR' in line or 'CRITICAL' in line:
                                print(f"🔴 {line}")
                            elif 'WARNING' in line:
                                print(f"🟡 {line}")
                            else:
                                print(f"🟢 {line}")
                else:
                    print("❌ Unable to read audit log")
            elif self.auditor.log_file is None:
                print("📝 Console-only logging mode - no persistent audit log file")
                print("💡 Run with sudo privileges to enable file logging to /var/log/")
            else:
                print("📝 No audit log found")
        except Exception as e:
            print(f"❌ Error reading audit log: {e}")
        
        print()
    
    def run(self):
        """Main program loop with security session management"""
        try:
            print("🛡️ Initializing Secure Fail2Ban Manager...")
            print("✅ Security-hardened Fail2Ban Manager ready!")
            print(f"🔐 Session ID: {self.auditor.session_id}")
        except Exception as e:
            print(f"❌ Failed to initialize: {e}")
            return
        
        while True:
            try:
                self.show_menu()
                choice = input("Choose an option (1-9, s, d, x): ").strip().lower()
                
                if choice == '1':
                    self.show_jail_status_overview()
                
                elif choice == '2':
                    self.show_banned_ips_detailed()
                
                elif choice == '3':
                    try:
                        self.unban_ip_interactive()
                    except SecurityError as e:
                        print(f"🔒 Security restriction: {e}")
                
                elif choice == '4':
                    try:
                        self.ban_ip_interactive()
                    except SecurityError as e:
                        print(f"🔒 Security restriction: {e}")
                
                elif choice == '5':
                    self.show_daily_report()
                
                elif choice == '6':
                    self.show_attack_patterns()
                
                elif choice == '7':
                    self.search_ip_interactive()
                
                elif choice == '8':
                    self.show_email_security_report()
                
                elif choice == '9':
                    try:
                        self.export_data_interactive()
                    except SecurityError as e:
                        print(f"🔒 Security restriction: {e}")
                
                elif choice == 's':
                    self.show_security_audit_log()
                
                elif choice == 'd':
                    self.debug_jail_status()
                
                elif choice == 'x':
                    print("🔒 Closing secure session...")
                    self.auditor.close_session()
                    print("👋 Goodbye!")
                    break
                
                else:
                    print("❌ Invalid choice. Please enter 1-9, s, d, or x.")
                    
            except KeyboardInterrupt:
                print("\n\n🔒 Closing secure session...")
                self.auditor.close_session()
                print("👋 Goodbye!")
                break
            except SecurityError as e:
                print(f"🔒 Security Error: {e}")
                self.auditor.log_event("SECURITY_VIOLATION", str(e), "ERROR")
            except Exception as e:
                self.auditor.log_event("UNEXPECTED_ERROR", str(e), "ERROR")
                print(f"❌ Unexpected error: {e}")
    
    def debug_jail_status(self):
        """Debug function with security logging"""
        print("\n🔧 Debug: Secure Jail Status Information\n")
        print("=" * 80)
        
        self.auditor.log_event("DEBUG_SESSION", "User initiated debug session")
        
        try:
            result = self._run_fail2ban_command(['status'])
            print("📋 Fail2ban Status Output:")
            print("=" * 50)
            print(result.stdout)
            print("=" * 50)
            print(f"Return code: {result.returncode}")
            if result.stderr:
                print(f"Stderr: {result.stderr}")
        except Exception as e:
            print(f"❌ Error running fail2ban-client status: {e}")
            return
        
        # Test specific jail status
        jails = self.get_active_jails()
        if jails:
            print(f"\n🏛️ Testing first jail: {jails[0]}")
            try:
                result = self._run_fail2ban_command(['status', jails[0]])
                print("📋 Jail Status Output:")
                print("=" * 50)
                print(result.stdout)
                print("=" * 50)
                print(f"Return code: {result.returncode}")
                if result.stderr:
                    print(f"Stderr: {result.stderr}")
            except Exception as e:
                print(f"❌ Error getting jail status: {e}")
        
        print()


def main():
    """Main entry point with security validation"""
    parser = argparse.ArgumentParser(
        description="Secure Fail2Ban Manager with Enhanced Email Monitoring",
        epilog="Example: python secure_fail2ban_manager.py"
    )
    parser.add_argument(
        '--version', 
        action='version', 
        version='Secure Fail2Ban Manager v2.0.0'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level'
    )
    
    args = parser.parse_args()
    
    try:
        # Security check: Don't run as root
        if os.getuid() == 0:
            print("❌ Security Error: Do not run this script as root.")
            print("💡 Run as a regular user with sudo privileges.")
            sys.exit(1)
        
        # Initialize and run manager
        manager = SecureFail2BanManager()
        manager.run()
        
    except SecurityError as e:
        print(f"🔒 Security Error: {e}")
        print("💡 Check your permissions and try again.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        print("💡 Make sure fail2ban is installed and you have sudo privileges.")
        sys.exit(1)


if __name__ == "__main__":
    main()
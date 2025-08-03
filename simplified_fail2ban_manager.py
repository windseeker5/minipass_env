#!/home/kdresdell/minipass_env/MinipassWebSite/venv/bin/python
"""
Simplified Secure Fail2Ban Manager - Fixed Logging Issues

A streamlined security-hardened fail2ban management script with aggressive
audit log management and minimal disk usage.

Author: Python DevOps Automation Specialist
Created: 2025-08-03
Version: 3.0.0 (Simplified & Optimized)

Key Features:
- Minimal audit logging (only critical security events)
- Automatic audit log cleanup and size limits (max 10MB)
- Lightweight email security reporting with batch processing
- Aggressive session cleanup
- Memory-based log processing to minimize disk I/O
- Production-safe with minimal disk footprint
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


class MinimalSecurityAuditor:
    """Minimal security audit logging with aggressive cleanup"""
    
    # Maximum audit log size (10MB)
    MAX_AUDIT_SIZE = 10 * 1024 * 1024
    
    # Events that actually need logging (minimal set)
    CRITICAL_EVENTS = {
        'SESSION_START', 'SESSION_END', 'UNBAN_SUCCESS', 'BAN_SUCCESS',
        'SECURITY_VIOLATION', 'AUTH_FAILURE', 'COMMAND_TIMEOUT'
    }
    
    def __init__(self, log_file: str = "/home/kdresdell/minipass_env/simplified_fail2ban_manager.log"):
        self.log_file = Path(log_file)
        self.session_id = self._generate_session_id()
        self.start_time = datetime.now()
        self.user = pwd.getpwuid(os.getuid()).pw_name
        self.event_count = 0
        
        # Setup minimal logging
        self._setup_minimal_logging()
        
        # Check and cleanup audit log if needed
        self._check_and_cleanup_audit_log()
        
        # Only log session start if it's a critical event
        self.log_critical_event("SESSION_START", f"User: {self.user}")
    
    def _generate_session_id(self) -> str:
        """Generate secure session ID"""
        return secrets.token_hex(8)  # Shorter ID to save space
    
    def _setup_minimal_logging(self):
        """Setup minimal audit logging"""
        try:
            # Create log directory if it doesn't exist
            self.log_file.parent.mkdir(mode=0o750, exist_ok=True)
            
            # Setup logger with minimal configuration
            self.logger = logging.getLogger('minimal_audit')
            self.logger.setLevel(logging.CRITICAL)  # Only critical events
            
            # Remove any existing handlers to prevent duplicate logging
            for handler in self.logger.handlers[:]:
                self.logger.removeHandler(handler)
            
            # Create minimal file handler
            handler = logging.FileHandler(self.log_file, mode='a')
            handler.setLevel(logging.CRITICAL)
            
            # Minimal formatter to save space
            formatter = logging.Formatter('%(asctime)s [%(session)s] %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
            # Set secure permissions on log file
            try:
                os.chmod(self.log_file, 0o640)
            except OSError:
                pass
                
        except (PermissionError, OSError):
            # Fall back to no logging rather than console spam
            self.logger = None
            self.log_file = None
    
    def _check_and_cleanup_audit_log(self):
        """Check audit log size and cleanup if needed"""
        if not self.log_file or not self.log_file.exists():
            return
        
        try:
            # Check file size
            file_size = self.log_file.stat().st_size
            
            if file_size > self.MAX_AUDIT_SIZE:
                self._truncate_audit_log()
        except Exception:
            # If we can't check size, just continue
            pass
    
    def _truncate_audit_log(self):
        """Truncate audit log to keep only recent entries"""
        if not self.log_file or not self.log_file.exists():
            return
        
        try:
            # Keep only last 500 lines
            result = subprocess.run(
                ['tail', '-500', str(self.log_file)],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Write truncated content back
                with open(self.log_file, 'w') as f:
                    f.write(result.stdout)
        except Exception:
            # If truncation fails, remove the file entirely
            try:
                self.log_file.unlink()
            except:
                pass
    
    def log_critical_event(self, event_type: str, details: str):
        """Log only critical security events"""
        if event_type not in self.CRITICAL_EVENTS:
            return  # Skip non-critical events
        
        if not self.logger:
            return  # No logging available
        
        extra = {'session': self.session_id}
        message = f"{event_type}: {details}"
        
        try:
            self.logger.critical(message, extra=extra)
            self.event_count += 1
            
            # Aggressive cleanup after every 50 events
            if self.event_count % 50 == 0:
                self._check_and_cleanup_audit_log()
        except Exception:
            # Ignore logging errors to prevent cascading failures
            pass
    
    def cleanup_session(self):
        """Aggressive session cleanup"""
        duration = datetime.now() - self.start_time
        self.log_critical_event("SESSION_END", f"Duration: {duration}")
        
        # Final audit log cleanup
        self._check_and_cleanup_audit_log()
        
        # Close logging handlers to release resources
        if self.logger:
            for handler in self.logger.handlers[:]:
                handler.close()
                self.logger.removeHandler(handler)


class InputValidator:
    """Streamlined input validation"""
    
    @staticmethod
    def validate_ip(ip_string: str) -> bool:
        """Validate IP address format"""
        if not ip_string or len(ip_string) > 45:
            return False
        
        try:
            ipaddress.ip_address(ip_string.strip())
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_jail_name(jail_name: str) -> bool:
        """Validate jail name"""
        if not jail_name or len(jail_name) > 50:
            return False
        
        pattern = re.compile(r'^[a-zA-Z0-9_-]+$')
        return bool(pattern.match(jail_name))
    
    @staticmethod
    def validate_filename(filename: str) -> bool:
        """Validate filename"""
        if not filename or len(filename) > 100:
            return False
        
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
        
        pattern = re.compile(r'^[a-zA-Z0-9_.-]+$')
        return bool(pattern.match(filename))
    
    @staticmethod
    def validate_time_period(days: str) -> int:
        """Validate time period"""
        try:
            days_int = int(days)
            if 1 <= days_int <= 90:  # Reduced max to limit processing
                return days_int
            raise ValueError("Days must be between 1 and 90")
        except ValueError:
            raise ValueError("Invalid time period format")
    
    @staticmethod
    def sanitize_command_arg(arg: str) -> str:
        """Sanitize command arguments"""
        dangerous_chars = ['`', '$', '|', '&', ';', '(', ')', '<', '>', '\n', '\r']
        sanitized = arg
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        return sanitized.strip()


def require_auth(func):
    """Decorator to ensure user authentication and authorization"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            user_groups = [grp.getgrgid(gid).gr_name for gid in os.getgroups()]
            if 'sudo' not in user_groups and 'admin' not in user_groups:
                raise SecurityError("User not authorized for fail2ban operations")
        except Exception as e:
            self.auditor.log_critical_event("AUTH_FAILURE", f"Authorization failed: {e}")
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


class SimplifiedFail2BanManager:
    """Simplified, production-safe Fail2Ban Manager"""
    
    # Configuration constants
    FAIL2BAN_CLIENT = "/usr/bin/fail2ban-client"
    FAIL2BAN_LOG = "/var/log/fail2ban.log"
    POSTFIX_LOG = "/var/log/mail.log"
    DOVECOT_LOG = "/var/log/dovecot.log"
    
    # Rate limiters
    COMMAND_RATE_LIMITER = RateLimiter(max_calls=20, time_window=60)
    UNBAN_RATE_LIMITER = RateLimiter(max_calls=5, time_window=300)
    BAN_RATE_LIMITER = RateLimiter(max_calls=3, time_window=300)
    
    def __init__(self):
        """Initialize simplified fail2ban manager"""
        self.auditor = MinimalSecurityAuditor()
        self.validator = InputValidator()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            self._check_security_prerequisites()
            self._check_fail2ban_available()
        except Exception as e:
            self.auditor.log_critical_event("INIT_FAILURE", f"Initialization failed: {e}")
            raise
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.auditor.cleanup_session()
        sys.exit(0)
    
    def _check_security_prerequisites(self):
        """Check security prerequisites"""
        if os.getuid() == 0:
            raise SecurityError("Do not run this script as root. Use sudo for specific commands only.")
        
        if not os.path.exists(self.FAIL2BAN_CLIENT):
            raise SecurityError("fail2ban-client not found")
        
        if not os.access(self.FAIL2BAN_CLIENT, os.X_OK):
            raise SecurityError("fail2ban-client not executable")
    
    def _check_fail2ban_available(self):
        """Check if fail2ban is available"""
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
        """Run fail2ban-client command with minimal logging"""
        # Validate and sanitize all arguments
        sanitized_args = []
        for arg in cmd_args:
            if not isinstance(arg, str):
                raise SecurityError("All command arguments must be strings")
            
            sanitized_arg = self.validator.sanitize_command_arg(arg)
            if len(sanitized_arg) > 100:
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
                timeout=30,
                env={'PATH': '/usr/bin:/bin'}
            )
            
            # Only log command timeouts and failures (not success)
            return result
            
        except subprocess.TimeoutExpired:
            self.auditor.log_critical_event("COMMAND_TIMEOUT", f"Command timed out: {' '.join(command[:3])}")
            raise SecurityError("Command execution timed out")
        except subprocess.CalledProcessError as e:
            if check:
                raise SecurityError(f"Fail2ban command failed: {e.stderr}")
            return e
        except Exception as e:
            raise SecurityError(f"Error running fail2ban command: {e}")
    
    def get_active_jails(self) -> List[str]:
        """Get list of active jails"""
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
                        return validated_jails
                return []
            else:
                return []
        except Exception:
            return []
    
    def get_jail_status(self, jail_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed status for a specific jail"""
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
                                status_info['filter'] = parts[1].strip()[:100]
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
        except Exception:
            return None
    
    @rate_limit(UNBAN_RATE_LIMITER)
    def unban_ip(self, jail_name: str, ip_address: str) -> bool:
        """Unban a specific IP from a jail"""
        if not self.validator.validate_jail_name(jail_name):
            raise SecurityError(f"Invalid jail name: {jail_name}")
        
        if not self.validator.validate_ip(ip_address):
            raise SecurityError(f"Invalid IP address: {ip_address}")
        
        try:
            # Try global unban first
            result = self._run_fail2ban_command(['unban', ip_address], check=False)
            if result.returncode == 0:
                self.auditor.log_critical_event("UNBAN_SUCCESS", f"Global unban - IP: {ip_address}")
                print(f"✅ Successfully unbanned {ip_address}")
                return True
            else:
                # Try jail-specific unban
                result = self._run_fail2ban_command(['set', jail_name, 'unbanip', ip_address], check=False)
                if result.returncode == 0:
                    self.auditor.log_critical_event("UNBAN_SUCCESS", f"Jail: {jail_name}, IP: {ip_address}")
                    print(f"✅ Successfully unbanned {ip_address} from {jail_name}")
                    return True
                else:
                    print(f"❌ Failed to unban {ip_address}: {result.stderr}")
                    return False
        except Exception as e:
            print(f"❌ Error unbanning {ip_address}: {e}")
            return False
    
    @rate_limit(BAN_RATE_LIMITER)
    def ban_ip(self, jail_name: str, ip_address: str, reason: str = "") -> bool:
        """Ban a specific IP in a jail"""
        if not self.validator.validate_jail_name(jail_name):
            raise SecurityError(f"Invalid jail name: {jail_name}")
        
        if not self.validator.validate_ip(ip_address):
            raise SecurityError(f"Invalid IP address: {ip_address}")
        
        # Security check for private/localhost
        try:
            ip = ipaddress.ip_address(ip_address)
            if ip.is_private or ip.is_loopback:
                raise SecurityError("Cannot ban private or loopback IP addresses")
        except ValueError:
            raise SecurityError("Invalid IP address format")
        
        clean_reason = self.validator.sanitize_command_arg(reason)[:200]
        
        try:
            result = self._run_fail2ban_command(['set', jail_name, 'banip', ip_address])
            if result.returncode == 0:
                self.auditor.log_critical_event("BAN_SUCCESS", f"Jail: {jail_name}, IP: {ip_address}")
                print(f"✅ Successfully banned {ip_address} in {jail_name}")
                if clean_reason:
                    print(f"📝 Reason: {clean_reason}")
                return True
            else:
                print(f"❌ Failed to ban {ip_address}: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error banning {ip_address}: {e}")
            return False
    
    def parse_fail2ban_logs_minimal(self, days: int = 1) -> Dict[str, List[Dict]]:
        """Parse fail2ban logs with minimal memory usage"""
        if not isinstance(days, int) or days < 1 or days > 90:
            raise SecurityError("Invalid days parameter")
        
        log_data = {
            'bans': [],
            'unbans': [],
            'attempts': []
        }
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Limit to main log file only for performance
        log_files = [self.FAIL2BAN_LOG]
        
        # Add only recent rotated logs (limit to 2 files)
        for i in range(1, min(3, days + 1)):
            log_file = f"{self.FAIL2BAN_LOG}.{i}"
            if os.path.exists(log_file):
                log_files.append(log_file)
                break  # Only add first rotated file
        
        for log_file in log_files:
            try:
                if log_file.endswith('.gz'):
                    with gzip.open(log_file, 'rt', encoding='utf-8', errors='ignore') as f:
                        self._parse_log_content_minimal(f, log_data, cutoff_date)
                else:
                    try:
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            self._parse_log_content_minimal(f, log_data, cutoff_date)
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
                            self._parse_log_content_minimal(StringIO(result.stdout), log_data, cutoff_date)
                        except:
                            continue
            except Exception:
                continue
        
        return log_data
    
    def _parse_log_content_minimal(self, file_handle, log_data: Dict, cutoff_date: datetime):
        """Parse log content with minimal processing and no individual line logging"""
        ban_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).*\[(\w+)\].*Ban (\d+\.\d+\.\d+\.\d+)')
        unban_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).*\[(\w+)\].*Unban (\d+\.\d+\.\d+\.\d+)')
        attempt_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).*\[(\w+)\].*Found (\d+\.\d+\.\d+\.\d+)')
        
        line_count = 0
        processed_events = 0
        
        for line in file_handle:
            line_count += 1
            
            # Aggressive limit to prevent memory issues
            if line_count > 50000:  # Reduced from 100000
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
                        processed_events += 1
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
                        processed_events += 1
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
                        processed_events += 1
                        
            except Exception:
                continue
        
        # No individual line logging - only summary if it's significant
        # (This dramatically reduces log volume)
    
    def get_lightweight_email_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get email statistics with minimal logging and batch processing"""
        if not isinstance(days, int) or days < 1 or days > 30:  # Reduced max from 90
            raise SecurityError("Invalid days parameter for email statistics")
        
        email_jails = [
            'postfix-sasl', 'postfix-rbl', 'postfix-relay', 'postfix-spam',
            'dovecot', 'courier-smtp', 'courier-auth', 'cyrus-imap',
            'exim', 'exim-spam'
        ]
        
        # Process logs in memory without extensive logging
        log_data = self.parse_fail2ban_logs_minimal(days)
        
        email_stats = {
            'total_email_attacks': 0,
            'email_bans_by_service': defaultdict(int),
            'top_email_attackers': Counter(),
            'smtp_auth_failures': 0,
            'imap_pop_failures': 0,
            'relay_abuse_attempts': 0,
            'spam_injection_attempts': 0
        }
        
        # Batch process bans for email services (no individual logging)
        for ban in log_data['bans']:
            if ban['jail'] in email_jails:
                email_stats['total_email_attacks'] += 1
                email_stats['email_bans_by_service'][ban['jail']] += 1
                email_stats['top_email_attackers'][ban['ip']] += 1
                
                # Categorize by attack type
                if 'sasl' in ban['jail'] or 'auth' in ban['jail']:
                    email_stats['smtp_auth_failures'] += 1
                elif 'dovecot' in ban['jail'] or 'courier' in ban['jail'] or 'imap' in ban['jail']:
                    email_stats['imap_pop_failures'] += 1
                elif 'relay' in ban['jail']:
                    email_stats['relay_abuse_attempts'] += 1
                elif 'spam' in ban['jail']:
                    email_stats['spam_injection_attempts'] += 1
        
        return email_stats
    
    def show_lightweight_email_security_report(self):
        """Display simplified email security report with minimal logging"""
        print("\n📧 Lightweight Email Security Report\n")
        print("=" * 60)
        
        try:
            # Get email statistics with minimal processing
            email_stats = self.get_lightweight_email_statistics(7)
            
            print(f"📊 WEEKLY EMAIL SECURITY SUMMARY:")
            print(f"  🚫 Total Email-Related Attacks: {email_stats['total_email_attacks']}")
            print(f"  🔐 SMTP Authentication Failures: {email_stats['smtp_auth_failures']}")
            print(f"  📬 IMAP/POP3 Attack Attempts: {email_stats['imap_pop_failures']}")
            print(f"  🔄 Mail Relay Abuse Attempts: {email_stats['relay_abuse_attempts']}")
            print(f"  🗑️ Spam Injection Attempts: {email_stats['spam_injection_attempts']}")
            
            if email_stats['email_bans_by_service']:
                print(f"\n🏛️ Email Service Protection Summary:")
                for service, count in email_stats['email_bans_by_service'].items():
                    print(f"  • {service}: {count} bans")
            
            if email_stats['top_email_attackers']:
                print(f"\n🎯 Top Email Attackers:")
                for ip, count in email_stats['top_email_attackers'].most_common(5):
                    print(f"  • {ip}: {count} attacks")
            
            print(f"\n✅ Email Security Report Complete")
            
        except Exception as e:
            print(f"❌ Error generating email security report: {e}")
        
        print()
    
    def show_jail_status_overview(self):
        """Display jail status overview"""
        print("\n📊 Jail Status Overview\n")
        print("=" * 60)
        
        jails = self.get_active_jails()
        if not jails:
            print("❌ No active jails found or fail2ban not accessible.")
            return
        
        print(f"{'Jail':<20} {'Status':<10} {'Failed':<8} {'Banned':<8} {'Total Bans':<12}")
        print("=" * 60)
        
        total_banned = 0
        total_failed = 0
        email_jails = 0
        
        for jail in jails:
            status = self.get_jail_status(jail)
            if status:
                currently_failed = status.get('currently_failed', 0)
                currently_banned = status.get('currently_banned', 0)
                total_banned_jail = status.get('total_banned', 0)
                
                # Categorize jail type
                jail_type = "🌐"
                if any(email_keyword in jail.lower() for email_keyword in ['mail', 'smtp', 'imap', 'pop', 'postfix', 'dovecot']):
                    jail_type = "📧"
                    email_jails += 1
                elif 'ssh' in jail.lower():
                    jail_type = "🔑"
                elif 'ftp' in jail.lower():
                    jail_type = "📁"
                
                status_icon = "🟢" if currently_banned == 0 else "🔴"
                
                print(f"{jail_type} {jail:<17} {status_icon:<10} {currently_failed:<8} {currently_banned:<8} {total_banned_jail:<12}")
                
                total_banned += currently_banned
                total_failed += currently_failed
            else:
                print(f"❌ {jail:<17} {'Error':<10} {'-':<8} {'-':<8} {'-':<12}")
        
        print("=" * 60)
        print(f"{'TOTALS':<20} {'':<10} {total_failed:<8} {total_banned:<8}")
        print(f"📧 Email Services Protected: {email_jails}")
        print(f"🛡️ Total Services Protected: {len(jails)}")
        
        if total_banned == 0:
            print(f"\n✅ Security Status: No current active bans")
        else:
            print(f"\n⚠️ Security Alert: {total_banned} IPs currently banned")
        
        print()
    
    def show_banned_ips_detailed(self):
        """Show detailed list of banned IPs"""
        print("\n🚫 Currently Banned IPs\n")
        print("=" * 60)
        
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
                    print(f"  {i:2d}. {ip}")
                print()
                total_banned += len(ips)
        
        print(f"📊 Ban Summary:")
        print(f"  🚫 Total Banned IPs: {total_banned}")
        print(f"  📧 Email-Related Bans: {email_related_bans}")
        print(f"  🌐 Other Service Bans: {total_banned - email_related_bans}")
        print()
    
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
        """Interactive IP unbanning"""
        print("\n✅ IP Unbanning\n")
        print("=" * 40)
        
        banned_info = self.get_banned_ips()
        if not any(banned_info.values()):
            print("✅ No IPs are currently banned.")
            return
        
        all_banned = []
        for jail, ips in banned_info.items():
            for ip in ips:
                all_banned.append((jail, ip))
        
        if not all_banned:
            print("✅ No IPs are currently banned.")
            return
        
        print("Currently banned IPs:")
        for i, (jail, ip) in enumerate(all_banned, 1):
            print(f"  {i:2d}. {ip:<15} (in {jail})")
        
        print("\nUnban Options:")
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
            print(f"❌ Error during unban operation: {e}")
    
    def ban_ip_interactive(self):
        """Interactive IP banning"""
        print("\n⚠️ IP Banning\n")
        print("=" * 40)
        
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
                        self.ban_ip(jail, ip, reason)
                    except SecurityError as e:
                        print(f"❌ Security restriction: {e}")
                else:
                    print("❌ Ban cancelled.")
            else:
                print("❌ Invalid jail number.")
        except ValueError:
            print("❌ Invalid input.")
        except Exception as e:
            print(f"❌ Error during ban operation: {e}")
    
    def show_daily_report(self):
        """Show simplified daily activity report"""
        print("\n📈 Daily Security Activity Report\n")
        print("=" * 60)
        
        try:
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
                    print(f"    • {ip}: {count} bans")
            
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
        
        except Exception as e:
            print(f"❌ Error generating daily report: {e}")
        
        print()
    
    def get_daily_statistics(self, days: int) -> Dict[str, Any]:
        """Get daily statistics with minimal processing"""
        days = self.validator.validate_time_period(str(days))
        log_data = self.parse_fail2ban_logs_minimal(days)
        
        stats = {
            'total_bans': len(log_data['bans']),
            'total_unbans': len(log_data['unbans']),
            'total_attempts': len(log_data['attempts']),
            'bans_by_jail': Counter(),
            'top_attackers': Counter()
        }
        
        # Process bans
        for ban in log_data['bans']:
            stats['bans_by_jail'][ban['jail']] += 1
            stats['top_attackers'][ban['ip']] += 1
        
        return stats
    
    def search_ip_interactive(self):
        """Interactive IP search"""
        print("\n🔍 IP Address Search\n")
        print("=" * 40)
        
        ip = input("Enter IP address to search: ").strip()
        if not self.validator.validate_ip(ip):
            print("❌ Invalid IP address format.")
            return
        
        days_input = input("Search last how many days? (default: 30, max: 30): ").strip()
        try:
            days = self.validator.validate_time_period(days_input if days_input else "30")
            if days > 30:
                days = 30
                print("⚠️ Limited search to 30 days for performance.")
        except ValueError:
            print("❌ Invalid time period. Using 30 days.")
            days = 30
        
        print(f"\n🔍 Searching for {ip} in last {days} days...")
        
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
            
            # Security assessment
            if len(events['bans']) > 5:
                print(f"\n⚠️ Security Assessment: High-risk IP (multiple bans)")
            elif len(events['attempts']) > 20:
                print(f"\n⚠️ Security Assessment: Persistent attacker (many attempts)")
            elif any('ssh' in ban['jail'].lower() for ban in events['bans']):
                print(f"\n⚠️ Security Assessment: SSH attack source")
        
        except Exception as e:
            print(f"❌ Error searching for IP: {e}")
        
        print()
    
    def search_ip_in_logs(self, ip_address: str, days: int = 30) -> Dict[str, List[Dict]]:
        """Search for a specific IP in logs"""
        if not self.validator.validate_ip(ip_address):
            raise SecurityError(f"Invalid IP address: {ip_address}")
        
        days = self.validator.validate_time_period(str(days))
        log_data = self.parse_fail2ban_logs_minimal(days)
        
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
        """Interactive data export"""
        print("\n📤 Data Export\n")
        print("=" * 40)
        
        days_input = input("Export data for last how many days? (default: 30, max: 30): ").strip()
        try:
            days = self.validator.validate_time_period(days_input if days_input else "30")
            if days > 30:
                days = 30
                print("⚠️ Limited export to 30 days for performance.")
        except ValueError:
            print("❌ Invalid time period. Using 30 days.")
            days = 30
        
        filename = input(f"Enter filename (default: fail2ban_export_{datetime.now().strftime('%Y%m%d')}.csv): ").strip()
        if not filename:
            filename = f"fail2ban_export_{datetime.now().strftime('%Y%m%d')}.csv"
        
        if not self.validator.validate_filename(filename):
            print("❌ Invalid filename. Using default.")
            filename = f"fail2ban_export_{datetime.now().strftime('%Y%m%d')}.csv"
        
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
        except Exception as e:
            print(f"❌ Export failed: {e}")
        
        print()
    
    def export_ban_data_csv(self, filename: str, days: int = 30) -> bool:
        """Export ban data to CSV file"""
        if not self.validator.validate_filename(filename):
            raise SecurityError(f"Invalid filename: {filename}")
        
        days = self.validator.validate_time_period(str(days))
        log_data = self.parse_fail2ban_logs_minimal(days)
        
        try:
            safe_filename = os.path.join(os.getcwd(), filename)
            
            with open(safe_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Timestamp', 'Event Type', 'Jail', 'IP Address'])
                
                # Write ban events
                for ban in log_data['bans']:
                    writer.writerow([
                        self.format_timestamp(ban['timestamp']),
                        'BAN',
                        ban['jail'],
                        ban['ip']
                    ])
                
                # Write unban events
                for unban in log_data['unbans']:
                    writer.writerow([
                        self.format_timestamp(unban['timestamp']),
                        'UNBAN',
                        unban['jail'],
                        unban['ip']
                    ])
                
                # Write attempt events
                for attempt in log_data['attempts']:
                    writer.writerow([
                        self.format_timestamp(attempt['timestamp']),
                        'ATTEMPT',
                        attempt['jail'],
                        attempt['ip']
                    ])
            
            # Set secure permissions
            os.chmod(safe_filename, 0o640)
            print(f"✅ Ban data exported to {safe_filename}")
            return True
        except Exception as e:
            raise SecurityError(f"Error exporting data: {e}")
    
    def format_timestamp(self, timestamp: datetime) -> str:
        """Format timestamp for display"""
        return timestamp.strftime('%Y-%m-%d %H:%M:%S')
    
    def show_menu(self):
        """Display the simplified main menu"""
        title = pyfiglet.figlet_format("SimplifiedF2B", font="small")
        print(title)
        print("🛡️ Simplified Secure Fail2Ban Manager v3.0 - Production Safe")
        print("=" * 60)
        print()
        print("  1.  Show jail status overview")
        print("  2.  List all banned IPs")
        print("  3.  Unban specific IP")
        print("  4.  Ban specific IP manually")
        print("  5.  Daily/Weekly security activity report")
        print("  6.  Search IP across logs")
        print("  7.  📧 Lightweight Email Security Report")
        print("  8.  Export ban data to CSV")
        print("  s.  Show security audit log")
        print("  d.  Debug jail status")
        print("")
        print("  x.  Exit and cleanup session")
        print()
        print("🔒 Security: Minimal logging, aggressive cleanup")
        print()
    
    def show_security_audit_log(self):
        """Display recent security audit log entries"""
        print("\n🔒 Security Audit Log (Recent Critical Events)\n")
        print("=" * 60)
        
        try:
            if self.auditor.log_file and self.auditor.log_file.exists():
                # Read last 20 lines of audit log (reduced from 50)
                result = subprocess.run(
                    ['tail', '-20', str(self.auditor.log_file)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if line.strip():
                            print(f"📝 {line}")
                else:
                    print("❌ Unable to read audit log")
            elif self.auditor.log_file is None:
                print("📝 No persistent audit log (console-only mode)")
            else:
                print("📝 No audit log found")
        except Exception as e:
            print(f"❌ Error reading audit log: {e}")
        
        print()
    
    def run(self):
        """Main program loop with aggressive cleanup"""
        try:
            print("🛡️ Initializing Simplified Fail2Ban Manager...")
            print("✅ Simplified Fail2Ban Manager ready!")
            print(f"🔐 Session ID: {self.auditor.session_id}")
        except Exception as e:
            print(f"❌ Failed to initialize: {e}")
            return
        
        while True:
            try:
                self.show_menu()
                choice = input("Choose an option (1-8, s, d, x): ").strip().lower()
                
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
                    self.search_ip_interactive()
                
                elif choice == '7':
                    self.show_lightweight_email_security_report()
                
                elif choice == '8':
                    try:
                        self.export_data_interactive()
                    except SecurityError as e:
                        print(f"🔒 Security restriction: {e}")
                
                elif choice == 's':
                    self.show_security_audit_log()
                
                elif choice == 'd':
                    self.debug_jail_status()
                
                elif choice == 'x':
                    print("🔒 Closing session and cleaning up...")
                    self.auditor.cleanup_session()
                    print("👋 Goodbye!")
                    break
                
                else:
                    print("❌ Invalid choice. Please enter 1-8, s, d, or x.")
                    
            except KeyboardInterrupt:
                print("\n\n🔒 Closing session and cleaning up...")
                self.auditor.cleanup_session()
                print("👋 Goodbye!")
                break
            except SecurityError as e:
                print(f"🔒 Security Error: {e}")
                self.auditor.log_critical_event("SECURITY_VIOLATION", str(e))
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                
        # Final cleanup
        self._final_cleanup()
    
    def _final_cleanup(self):
        """Final aggressive cleanup"""
        try:
            # Clear any temporary variables
            if hasattr(self, 'temp_data'):
                delattr(self, 'temp_data')
            
            # Final audit log cleanup
            if hasattr(self, 'auditor'):
                self.auditor.cleanup_session()
        except Exception:
            pass  # Ignore cleanup errors
    
    def debug_jail_status(self):
        """Debug function with minimal logging"""
        print("\n🔧 Debug: Jail Status Information\n")
        print("=" * 60)
        
        try:
            result = self._run_fail2ban_command(['status'])
            print("📋 Fail2ban Status Output:")
            print("=" * 40)
            print(result.stdout)
            print("=" * 40)
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
                print("=" * 40)
                print(result.stdout)
                print("=" * 40)
                print(f"Return code: {result.returncode}")
                if result.stderr:
                    print(f"Stderr: {result.stderr}")
            except Exception as e:
                print(f"❌ Error getting jail status: {e}")
        
        print()


def main():
    """Main entry point with cleanup"""
    parser = argparse.ArgumentParser(
        description="Simplified Secure Fail2Ban Manager - Production Safe",
        epilog="Example: python simplified_fail2ban_manager.py"
    )
    parser.add_argument(
        '--version', 
        action='version', 
        version='Simplified Fail2Ban Manager v3.0.0'
    )
    
    args = parser.parse_args()
    
    try:
        # Security check: Don't run as root
        if os.getuid() == 0:
            print("❌ Security Error: Do not run this script as root.")
            print("💡 Run as a regular user with sudo privileges.")
            sys.exit(1)
        
        # Initialize and run manager
        manager = SimplifiedFail2BanManager()
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

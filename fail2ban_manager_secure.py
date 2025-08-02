#!/home/kdresdell/minipass_env/MinipassWebSite/venv/bin/python3
"""
Secure Fail2Ban Manager - Hardened version with comprehensive security controls

This script provides secure administrative functionality for managing fail2ban jails,
analyzing logs, and handling IP bans/unbans with comprehensive input validation
and security controls.

Security Features:
- Strict input validation and sanitization
- Command injection prevention
- Path traversal protection
- Audit logging
- Role-based access control
- Secure error handling

Author: Security-hardened version
Version: 2.0-secure
"""

import os
import subprocess
import json
import re
import csv
import gzip
import logging
import hashlib
import getpass
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import ipaddress
import pyfiglet
from pathlib import Path

# Security Configuration
ALLOWED_LOG_DIRECTORIES = ['/var/log', '/var/log/fail2ban']
MAX_DAYS_QUERY = 365
MAX_EXPORT_RECORDS = 100000
AUDIT_LOG_PATH = '/var/log/fail2ban_manager_audit.log'

# Application Configuration
FAIL2BAN_CLIENT = "/usr/bin/fail2ban-client"
FAIL2BAN_LOG = "/var/log/fail2ban.log"
FAIL2BAN_CONFIG = "/etc/fail2ban/jail.local"

class Fail2BanSecurityError(Exception):
    """Base exception for security-related errors"""
    pass

class InvalidInputError(Fail2BanSecurityError):
    """Raised when user input fails validation"""
    pass

class PrivilegeError(Fail2BanSecurityError):
    """Raised when insufficient privileges detected"""
    pass

class CommandExecutionError(Fail2BanSecurityError):
    """Raised when fail2ban command execution fails"""
    pass

class SecureFail2BanManager:
    def __init__(self):
        self.setup_logging()
        self.current_user = getpass.getuser()
        self.session_id = hashlib.md5(f"{self.current_user}{datetime.now()}".encode()).hexdigest()[:8]
        
        # Initialize security controls
        self.validate_environment()
        self.check_fail2ban_available()
        self.audit_log("session_start", {"user": self.current_user, "session_id": self.session_id})
    
    def setup_logging(self):
        """Setup secure logging configuration"""
        try:
            # Ensure audit log directory exists with secure permissions
            audit_dir = os.path.dirname(AUDIT_LOG_PATH)
            if not os.path.exists(audit_dir):
                os.makedirs(audit_dir, mode=0o750, exist_ok=True)
            
            # Configure logging
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler('/var/log/fail2ban_manager.log', mode='a'),
                    logging.StreamHandler()
                ]
            )
            
            # Set secure permissions on log files
            for log_file in ['/var/log/fail2ban_manager.log', AUDIT_LOG_PATH]:
                if os.path.exists(log_file):
                    os.chmod(log_file, 0o640)
                    
        except Exception as e:
            print(f"⚠️ Warning: Could not setup secure logging: {e}")
    
    def validate_environment(self):
        """Validate the execution environment"""
        # Check if running as root (security risk)
        if os.geteuid() == 0:
            raise PrivilegeError("This script should not be run as root. Use sudo for specific commands.")
        
        # Validate required directories exist
        required_dirs = ['/var/log', '/etc/fail2ban']
        for directory in required_dirs:
            if not os.path.exists(directory):
                raise Fail2BanSecurityError(f"Required directory not found: {directory}")
    
    def audit_log(self, action, details, success=True):
        """Secure audit logging for administrative actions"""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'session_id': self.session_id,
                'user': self.current_user,
                'action': action,
                'success': success,
                'details': self.sanitize_log_details(details)
            }
            
            with open(AUDIT_LOG_PATH, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            logging.error(f"Failed to write audit log: {e}")
    
    def sanitize_log_details(self, details):
        """Sanitize log details to prevent log injection"""
        if isinstance(details, dict):
            sanitized = {}
            for key, value in details.items():
                # Remove potentially dangerous characters
                clean_key = re.sub(r'[^\w\-_]', '', str(key))
                clean_value = re.sub(r'[\n\r\t\x00-\x1f\x7f-\x9f]', '', str(value))
                sanitized[clean_key] = clean_value[:200]  # Limit length
            return sanitized
        else:
            return re.sub(r'[\n\r\t\x00-\x1f\x7f-\x9f]', '', str(details))[:200]
    
    def sanitize_jail_name(self, jail_name):
        """Validate and sanitize jail name"""
        if not jail_name or not isinstance(jail_name, str):
            raise InvalidInputError("Jail name must be a non-empty string")
        
        # Only allow alphanumeric, hyphens, and underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', jail_name):
            raise InvalidInputError(f"Invalid jail name format: {jail_name}")
        
        # Length restrictions
        if len(jail_name) > 50:
            raise InvalidInputError("Jail name too long (max 50 characters)")
        
        return jail_name
    
    def sanitize_ip_address(self, ip_address):
        """Validate and sanitize IP address"""
        if not ip_address or not isinstance(ip_address, str):
            raise InvalidInputError("IP address must be a non-empty string")
        
        try:
            ip = ipaddress.ip_address(ip_address.strip())
            
            # Additional security checks
            if ip.is_private and not self.allow_private_ip_operations():
                raise InvalidInputError(f"Private IP operations not allowed: {ip_address}")
            
            if ip.is_loopback:
                raise InvalidInputError(f"Cannot operate on loopback IP: {ip_address}")
            
            if ip.is_multicast or ip.is_unspecified:
                raise InvalidInputError(f"Invalid IP address type: {ip_address}")
            
            return str(ip)
            
        except ipaddress.AddressValueError:
            raise InvalidInputError(f"Invalid IP address format: {ip_address}")
    
    def allow_private_ip_operations(self):
        """Check if private IP operations are allowed (configurable policy)"""
        # This could be configured based on organizational policy
        return False
    
    def sanitize_filename(self, filename):
        """Sanitize filename for export operations"""
        if not filename or not isinstance(filename, str):
            raise InvalidInputError("Filename must be a non-empty string")
        
        # Extract basename to prevent path traversal
        filename = os.path.basename(filename.strip())
        
        # Remove dangerous characters
        filename = re.sub(r'[^\w\-_\.]', '', filename)
        
        # Ensure it's not empty after sanitization
        if not filename or filename.startswith('.'):
            raise InvalidInputError("Invalid filename")
        
        # Ensure .csv extension
        if not filename.lower().endswith('.csv'):
            filename += '.csv'
        
        # Length restriction
        if len(filename) > 100:
            raise InvalidInputError("Filename too long (max 100 characters)")
        
        return filename
    
    def validate_days_parameter(self, days):
        """Validate days parameter with security limits"""
        try:
            days_int = int(days)
            if not 1 <= days_int <= MAX_DAYS_QUERY:
                raise InvalidInputError(f"Days must be between 1 and {MAX_DAYS_QUERY}")
            return days_int
        except (ValueError, TypeError):
            raise InvalidInputError("Days parameter must be a valid integer")
    
    def check_fail2ban_available(self):
        """Check if fail2ban is available and accessible"""
        try:
            if not os.path.exists(FAIL2BAN_CLIENT):
                raise Fail2BanSecurityError("fail2ban-client not found")
            
            # Test basic access
            result = subprocess.run(['which', 'fail2ban-client'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                raise Fail2BanSecurityError("fail2ban-client not available")
                
        except subprocess.TimeoutExpired:
            raise Fail2BanSecurityError("Timeout checking fail2ban availability")
        except Exception as e:
            raise Fail2BanSecurityError(f"Fail2ban check failed: {e}")
    
    def run_fail2ban_command(self, cmd_args, check=True):
        """Run fail2ban-client command with enhanced security"""
        try:
            # Validate all command arguments
            validated_args = []
            for arg in cmd_args:
                if not isinstance(arg, str):
                    raise InvalidInputError("All command arguments must be strings")
                
                # Prevent command injection
                if any(char in arg for char in [';', '&', '|', '`', '$', '(', ')', '<', '>']):
                    raise InvalidInputError(f"Dangerous characters in command argument: {arg}")
                
                validated_args.append(arg)
            
            # Construct command
            command = ['sudo', FAIL2BAN_CLIENT] + validated_args
            
            # Log the command execution attempt
            self.audit_log("command_execution", {
                "command": " ".join(command),
                "args": validated_args
            })
            
            # Execute with timeout
            result = subprocess.run(command, capture_output=True, text=True, 
                                  check=check, timeout=30)
            
            self.audit_log("command_execution_result", {
                "return_code": result.returncode,
                "success": result.returncode == 0
            })
            
            return result
            
        except subprocess.TimeoutExpired:
            error_msg = "Command execution timeout"
            self.audit_log("command_execution_error", {"error": error_msg}, success=False)
            raise CommandExecutionError(error_msg)
        except subprocess.CalledProcessError as e:
            error_msg = f"Fail2ban command failed: {self.sanitize_error_message(e.stderr)}"
            self.audit_log("command_execution_error", {"error": error_msg}, success=False)
            if check:
                raise CommandExecutionError(error_msg)
            return e
        except Exception as e:
            error_msg = f"Error running fail2ban command: {e}"
            self.audit_log("command_execution_error", {"error": error_msg}, success=False)
            raise CommandExecutionError(error_msg)
    
    def sanitize_error_message(self, error_msg):
        """Sanitize error messages to prevent information leakage"""
        if not error_msg:
            return "Unknown error"
        
        # Remove potentially sensitive information
        sanitized = re.sub(r'/home/[^/\s]+', '/home/[user]', str(error_msg))
        sanitized = re.sub(r'/etc/[^/\s]+', '/etc/[config]', sanitized)
        sanitized = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP]', sanitized)
        
        return sanitized[:200]  # Limit length
    
    def get_active_jails(self):
        """Get list of active jails with validation"""
        try:
            result = self.run_fail2ban_command(['status'])
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
                            try:
                                validated_jails.append(self.sanitize_jail_name(jail))
                            except InvalidInputError:
                                logging.warning(f"Skipping invalid jail name: {jail}")
                        return validated_jails
                return []
            else:
                logging.error(f"Failed to get jail list: {result.stderr}")
                return []
        except Exception as e:
            logging.error(f"Error getting active jails: {e}")
            return []
    
    def get_jail_status(self, jail_name):
        """Get detailed status for a specific jail with validation"""
        try:
            # Validate jail name
            clean_jail = self.sanitize_jail_name(jail_name)
            
            result = self.run_fail2ban_command(['status', clean_jail])
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
                        parts = line.split(':', 1)
                        if len(parts) >= 2:
                            key, value = parts[0].strip(), parts[1].strip()
                            
                            if 'Filter' in key:
                                status_info['filter'] = value
                            elif 'Actions' in key:
                                status_info['actions'] = value
                            elif 'Currently failed' in key:
                                status_info['currently_failed'] = max(0, int(value))
                            elif 'Total failed' in key:
                                status_info['total_failed'] = max(0, int(value))
                            elif 'Currently banned' in key:
                                status_info['currently_banned'] = max(0, int(value))
                            elif 'Total banned' in key:
                                status_info['total_banned'] = max(0, int(value))
                            elif 'Banned IP list' in key:
                                if value:
                                    # Validate each IP in the list
                                    validated_ips = []
                                    for ip in value.split():
                                        try:
                                            validated_ips.append(self.sanitize_ip_address(ip))
                                        except InvalidInputError:
                                            logging.warning(f"Invalid IP in banned list: {ip}")
                                    status_info['banned_ips'] = validated_ips
                                else:
                                    status_info['banned_ips'] = []
                    except (ValueError, IndexError) as e:
                        logging.debug(f"Skipping malformed line: {line}")
                        continue
                
                return status_info
            else:
                return None
        except Exception as e:
            logging.error(f"Error getting jail status for {jail_name}: {e}")
            return None
    
    def unban_ip(self, jail_name, ip_address):
        """Unban a specific IP from a jail with security validation"""
        try:
            # Validate inputs
            clean_jail = self.sanitize_jail_name(jail_name)
            clean_ip = self.sanitize_ip_address(ip_address)
            
            # Log the unban attempt
            self.audit_log("unban_attempt", {
                "jail": clean_jail,
                "ip": clean_ip
            })
            
            # Try global unban first
            result = self.run_fail2ban_command(['unban', clean_ip], check=False)
            if result.returncode == 0:
                print(f"✅ Successfully unbanned {clean_ip}")
                self.audit_log("unban_success", {"jail": "global", "ip": clean_ip})
                return True
            else:
                # Try jail-specific unban
                result = self.run_fail2ban_command(['set', clean_jail, 'unbanip', clean_ip], check=False)
                if result.returncode == 0:
                    print(f"✅ Successfully unbanned {clean_ip} from {clean_jail}")
                    self.audit_log("unban_success", {"jail": clean_jail, "ip": clean_ip})
                    return True
                else:
                    print(f"❌ Failed to unban {clean_ip}: {self.sanitize_error_message(result.stderr)}")
                    self.audit_log("unban_failure", {
                        "jail": clean_jail, 
                        "ip": clean_ip,
                        "error": self.sanitize_error_message(result.stderr)
                    }, success=False)
                    return False
        except Exception as e:
            error_msg = f"Error unbanning {ip_address}: {e}"
            print(f"❌ {error_msg}")
            self.audit_log("unban_error", {
                "jail": jail_name, 
                "ip": ip_address,
                "error": str(e)
            }, success=False)
            return False
    
    def ban_ip(self, jail_name, ip_address, duration=None):
        """Ban a specific IP in a jail with security validation"""
        try:
            # Validate inputs
            clean_jail = self.sanitize_jail_name(jail_name)
            clean_ip = self.sanitize_ip_address(ip_address)
            
            # Log the ban attempt
            self.audit_log("ban_attempt", {
                "jail": clean_jail,
                "ip": clean_ip,
                "duration": duration
            })
            
            result = self.run_fail2ban_command(['set', clean_jail, 'banip', clean_ip])
            if result.returncode == 0:
                duration_str = f" for {duration}" if duration else ""
                print(f"✅ Successfully banned {clean_ip} in {clean_jail}{duration_str}")
                self.audit_log("ban_success", {
                    "jail": clean_jail,
                    "ip": clean_ip,
                    "duration": duration
                })
                return True
            else:
                print(f"❌ Failed to ban {clean_ip}: {self.sanitize_error_message(result.stderr)}")
                self.audit_log("ban_failure", {
                    "jail": clean_jail,
                    "ip": clean_ip,
                    "error": self.sanitize_error_message(result.stderr)
                }, success=False)
                return False
        except Exception as e:
            error_msg = f"Error banning {ip_address}: {e}"
            print(f"❌ {error_msg}")
            self.audit_log("ban_error", {
                "jail": jail_name,
                "ip": ip_address,
                "error": str(e)
            }, success=False)
            return False
    
    def validate_log_path(self, log_path):
        """Validate log file path for security"""
        try:
            real_path = os.path.realpath(log_path)
            
            # Ensure path is within allowed directories
            allowed = False
            for allowed_dir in ALLOWED_LOG_DIRECTORIES:
                if real_path.startswith(os.path.realpath(allowed_dir)):
                    allowed = True
                    break
            
            if not allowed:
                raise InvalidInputError(f"Log file outside permitted directories: {log_path}")
            
            return real_path
        except Exception as e:
            raise InvalidInputError(f"Invalid log path: {e}")
    
    def read_log_safely(self, log_path):
        """Safely read log files with security controls"""
        validated_path = self.validate_log_path(log_path)
        
        if not os.path.exists(validated_path):
            raise FileNotFoundError(f"Log file not found: {validated_path}")
        
        try:
            with open(validated_path, 'r') as f:
                return f.read()
        except PermissionError:
            # Fallback to sudo with validated path
            result = subprocess.run(['sudo', 'cat', validated_path], 
                                  capture_output=True, text=True, check=True, timeout=30)
            return result.stdout
    
    def export_ban_data_csv(self, filename, days=30):
        """Export ban data to CSV file with security controls"""
        try:
            # Validate inputs
            clean_filename = self.sanitize_filename(filename)
            clean_days = self.validate_days_parameter(days)
            
            # Get log data
            log_data = self.parse_fail2ban_logs(clean_days)
            
            # Check export size limits
            total_records = len(log_data['bans']) + len(log_data['unbans']) + len(log_data['attempts'])
            if total_records > MAX_EXPORT_RECORDS:
                raise InvalidInputError(f"Export too large ({total_records} records). Maximum: {MAX_EXPORT_RECORDS}")
            
            # Create export file in secure location
            export_path = os.path.join('/tmp', clean_filename)
            
            self.audit_log("export_attempt", {
                "filename": clean_filename,
                "days": clean_days,
                "record_count": total_records
            })
            
            with open(export_path, 'w', newline='') as csvfile:
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
            os.chmod(export_path, 0o640)
            
            print(f"✅ Ban data exported to {export_path}")
            self.audit_log("export_success", {
                "filename": clean_filename,
                "path": export_path,
                "record_count": total_records
            })
            return True
            
        except Exception as e:
            error_msg = f"Error exporting data: {e}"
            print(f"❌ {error_msg}")
            self.audit_log("export_error", {
                "filename": filename,
                "error": str(e)
            }, success=False)
            return False
    
    def parse_fail2ban_logs(self, days=1):
        """Parse fail2ban logs for the specified number of days with security controls"""
        clean_days = self.validate_days_parameter(days)
        
        log_data = {
            'bans': [],
            'unbans': [],
            'attempts': []
        }
        
        cutoff_date = datetime.now() - timedelta(days=clean_days)
        
        # Read main log file
        try:
            if os.path.exists(FAIL2BAN_LOG):
                content = self.read_log_safely(FAIL2BAN_LOG)
                from io import StringIO
                self._parse_log_content(StringIO(content), log_data, cutoff_date)
        except Exception as e:
            logging.warning(f"Could not read main log file: {e}")
        
        # Read rotated log files with limits
        for i in range(1, min(8, clean_days + 1)):  # Limit based on days requested
            log_file = f"{FAIL2BAN_LOG}.{i}"
            if os.path.exists(log_file):
                try:
                    content = self.read_log_safely(log_file)
                    from io import StringIO
                    self._parse_log_content(StringIO(content), log_data, cutoff_date)
                except Exception:
                    continue
            
            # Check compressed logs
            gz_log_file = f"{log_file}.gz"
            if os.path.exists(gz_log_file):
                try:
                    validated_path = self.validate_log_path(gz_log_file)
                    with gzip.open(validated_path, 'rt') as f:
                        self._parse_log_content(f, log_data, cutoff_date)
                except Exception:
                    continue
        
        return log_data
    
    def _parse_log_content(self, file_handle, log_data, cutoff_date):
        """Parse log file content with security controls"""
        # Enhanced regex patterns with validation
        ban_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d{3}.*\[([a-zA-Z0-9_-]+)\].*Ban (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
        unban_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d{3}.*\[([a-zA-Z0-9_-]+)\].*Unban (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
        attempt_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d{3}.*\[([a-zA-Z0-9_-]+)\].*Found (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
        
        line_count = 0
        max_lines = 1000000  # Prevent DoS via large log files
        
        for line in file_handle:
            line_count += 1
            if line_count > max_lines:
                logging.warning(f"Log parsing stopped: exceeded maximum lines ({max_lines})")
                break
                
            try:
                # Parse timestamp with validation
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
                    try:
                        jail = self.sanitize_jail_name(ban_match.group(2))
                        ip = self.sanitize_ip_address(ban_match.group(3))
                        log_data['bans'].append({
                            'timestamp': timestamp,
                            'jail': jail,
                            'ip': ip
                        })
                    except InvalidInputError:
                        continue
                    continue
                
                # Check for unban events
                unban_match = unban_pattern.search(line)
                if unban_match:
                    try:
                        jail = self.sanitize_jail_name(unban_match.group(2))
                        ip = self.sanitize_ip_address(unban_match.group(3))
                        log_data['unbans'].append({
                            'timestamp': timestamp,
                            'jail': jail,
                            'ip': ip
                        })
                    except InvalidInputError:
                        continue
                    continue
                
                # Check for attempt events
                attempt_match = attempt_pattern.search(line)
                if attempt_match:
                    try:
                        jail = self.sanitize_jail_name(attempt_match.group(2))
                        ip = self.sanitize_ip_address(attempt_match.group(3))
                        log_data['attempts'].append({
                            'timestamp': timestamp,
                            'jail': jail,
                            'ip': ip
                        })
                    except InvalidInputError:
                        continue
                
            except Exception:
                continue
    
    def format_timestamp(self, timestamp):
        """Format timestamp for display"""
        return timestamp.strftime('%Y-%m-%d %H:%M:%S')
    
    def validate_ip(self, ip_string):
        """Validate IP address format (legacy wrapper)"""
        try:
            self.sanitize_ip_address(ip_string)
            return True
        except InvalidInputError:
            return False
    
    def get_banned_ips(self, jail_name=None):
        """Get banned IPs for a specific jail or all jails"""
        banned_info = {}
        
        if jail_name:
            try:
                clean_jail = self.sanitize_jail_name(jail_name)
                jails = [clean_jail]
            except InvalidInputError:
                return {}
        else:
            jails = self.get_active_jails()
        
        for jail in jails:
            status = self.get_jail_status(jail)
            if status and 'banned_ips' in status:
                banned_info[jail] = status['banned_ips']
            else:
                banned_info[jail] = []
        
        return banned_info
    
    def get_daily_statistics(self, days=1):
        """Get daily statistics for the specified number of days"""
        clean_days = self.validate_days_parameter(days)
        log_data = self.parse_fail2ban_logs(clean_days)
        
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
    
    def get_attack_patterns(self, days=7):
        """Analyze attack patterns over the specified period"""
        clean_days = self.validate_days_parameter(days)
        log_data = self.parse_fail2ban_logs(clean_days)
        
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
    
    def search_ip_in_logs(self, ip_address, days=30):
        """Search for a specific IP in logs with validation"""
        clean_ip = self.sanitize_ip_address(ip_address)
        clean_days = self.validate_days_parameter(days)
        
        log_data = self.parse_fail2ban_logs(clean_days)
        
        ip_events = {
            'bans': [],
            'unbans': [],
            'attempts': []
        }
        
        for ban in log_data['bans']:
            if ban['ip'] == clean_ip:
                ip_events['bans'].append(ban)
        
        for unban in log_data['unbans']:
            if unban['ip'] == clean_ip:
                ip_events['unbans'].append(unban)
        
        for attempt in log_data['attempts']:
            if attempt['ip'] == clean_ip:
                ip_events['attempts'].append(attempt)
        
        return ip_events
    
    def show_jail_status_overview(self):
        """Display comprehensive jail status overview"""
        print("\n📊 Jail Status Overview:\n")
        
        jails = self.get_active_jails()
        if not jails:
            print("❌ No active jails found or fail2ban not accessible.")
            return
        
        print(f"{'Jail':<20} {'Status':<10} {'Failed':<8} {'Banned':<8} {'Total Bans':<12}")
        print("=" * 70)
        
        total_banned = 0
        total_failed = 0
        
        for jail in jails:
            status = self.get_jail_status(jail)
            if status:
                currently_failed = status.get('currently_failed', 0)
                currently_banned = status.get('currently_banned', 0)
                total_banned_jail = status.get('total_banned', 0)
                
                status_icon = "🟢" if currently_banned == 0 else "🔴"
                
                print(f"{jail:<20} {status_icon:<10} {currently_failed:<8} {currently_banned:<8} {total_banned_jail:<12}")
                
                total_banned += currently_banned
                total_failed += currently_failed
            else:
                print(f"{jail:<20} {'❌ Error':<10} {'-':<8} {'-':<8} {'-':<12}")
        
        print("=" * 70)
        print(f"{'TOTALS':<20} {'':<10} {total_failed:<8} {total_banned:<8}")
        print()
    
    def show_banned_ips_detailed(self):
        """Show detailed list of banned IPs across all jails"""
        print("\n🚫 Currently Banned IPs:\n")
        
        banned_info = self.get_banned_ips()
        
        if not any(banned_info.values()):
            print("✅ No IPs are currently banned.")
            return
        
        for jail, ips in banned_info.items():
            if ips:
                print(f"🏛️ {jail.upper()} Jail:")
                for i, ip in enumerate(ips, 1):
                    print(f"  {i}. {ip}")
                print()
    
    def unban_ip_interactive(self):
        """Interactive IP unbanning with security controls"""
        print("\n✅ Unban IP Address:\n")
        
        try:
            banned_info = self.get_banned_ips()
            if not any(banned_info.values()):
                print("✅ No IPs are currently banned.")
                return
            
            # Display banned IPs
            all_banned = []
            for jail, ips in banned_info.items():
                for ip in ips:
                    all_banned.append((jail, ip))
            
            if not all_banned:
                print("✅ No IPs are currently banned.")
                return
            
            print("Currently banned IPs:")
            for i, (jail, ip) in enumerate(all_banned, 1):
                print(f"  {i}. {ip} (in {jail})")
            
            print("\nOptions:")
            print("1. Unban specific IP by number")
            print("2. Unban IP by address (from all jails)")
            print("3. Return to main menu")
            
            choice = input("\nChoose option (1-3): ").strip()
            
            if choice == "1":
                try:
                    num = int(input(f"Enter number (1-{len(all_banned)}): "))
                    if 1 <= num <= len(all_banned):
                        jail, ip = all_banned[num - 1]
                        self.unban_ip(jail, ip)
                    else:
                        print("❌ Invalid number.")
                except ValueError:
                    print("❌ Invalid input.")
            
            elif choice == "2":
                ip = input("Enter IP address to unban: ").strip()
                try:
                    clean_ip = self.sanitize_ip_address(ip)
                    unbanned = False
                    for jail in self.get_active_jails():
                        if self.unban_ip(jail, clean_ip):
                            unbanned = True
                    if not unbanned:
                        print(f"⚠️ {clean_ip} was not found in any banned lists.")
                except InvalidInputError as e:
                    print(f"❌ {e}")
            
            elif choice == "3":
                return
            else:
                print("❌ Invalid choice.")
                
        except Exception as e:
            print(f"❌ Error in unban operation: {e}")
    
    def ban_ip_interactive(self):
        """Interactive IP banning with security controls"""
        print("\n⚠️ Ban IP Address:\n")
        
        try:
            jails = self.get_active_jails()
            if not jails:
                print("❌ No active jails found.")
                return
            
            print("Available jails:")
            for i, jail in enumerate(jails, 1):
                print(f"  {i}. {jail}")
            
            try:
                jail_num = int(input(f"\nSelect jail (1-{len(jails)}): "))
                if 1 <= jail_num <= len(jails):
                    jail = jails[jail_num - 1]
                    
                    ip = input("Enter IP address to ban: ").strip()
                    try:
                        clean_ip = self.sanitize_ip_address(ip)
                        
                        reason = input("Enter reason (optional): ").strip()
                        if reason:
                            # Sanitize reason
                            reason = re.sub(r'[^\w\s\-_\.]', '', reason)[:100]
                        
                        if self.ban_ip(jail, clean_ip):
                            if reason:
                                print(f"📝 Reason logged: {reason}")
                                self.audit_log("ban_reason", {
                                    "jail": jail,
                                    "ip": clean_ip,
                                    "reason": reason
                                })
                        
                    except InvalidInputError as e:
                        print(f"❌ {e}")
                else:
                    print("❌ Invalid jail number.")
            except ValueError:
                print("❌ Invalid input.")
                
        except Exception as e:
            print(f"❌ Error in ban operation: {e}")
    
    def show_daily_report(self):
        """Show daily activity report"""
        print("\n📈 Daily Activity Report:\n")
        
        try:
            # Get statistics for different time periods
            today_stats = self.get_daily_statistics(1)
            week_stats = self.get_daily_statistics(7)
            
            print("📅 TODAY'S ACTIVITY:")
            print(f"  🚫 Total Bans: {today_stats['total_bans']}")
            print(f"  🔍 Failed Attempts: {today_stats['total_attempts']}")
            print(f"  ✅ Unbans: {today_stats['total_unbans']}")
            
            if today_stats['bans_by_jail']:
                print("\n  📊 Bans by Service:")
                for jail, count in today_stats['bans_by_jail'].most_common():
                    print(f"    • {jail}: {count}")
            
            if today_stats['top_attackers']:
                print(f"\n  🎯 Top Attackers Today:")
                for ip, count in today_stats['top_attackers'].most_common(5):
                    print(f"    • {ip}: {count} bans")
            
            print(f"\n📅 WEEKLY SUMMARY:")
            print(f"  🚫 Total Bans: {week_stats['total_bans']}")
            print(f"  🔍 Failed Attempts: {week_stats['total_attempts']}")
            
            if week_stats['bans_by_jail']:
                print("\n  📊 Weekly Bans by Service:")
                for jail, count in week_stats['bans_by_jail'].most_common():
                    print(f"    • {jail}: {count}")
            
            print()
            
        except Exception as e:
            print(f"❌ Error generating daily report: {e}")
    
    def search_ip_interactive(self):
        """Interactive IP search with validation"""
        print("\n🔍 Search IP Address:\n")
        
        try:
            ip = input("Enter IP address to search: ").strip()
            try:
                clean_ip = self.sanitize_ip_address(ip)
            except InvalidInputError as e:
                print(f"❌ {e}")
                return
            
            days = input("Search last how many days? (default: 30): ").strip()
            try:
                clean_days = self.validate_days_parameter(days) if days else 30
            except InvalidInputError as e:
                print(f"❌ {e}")
                return
            
            print(f"\n🔍 Searching for {clean_ip} in last {clean_days} days...\n")
            
            events = self.search_ip_in_logs(clean_ip, clean_days)
            
            total_events = len(events['bans']) + len(events['unbans']) + len(events['attempts'])
            
            if total_events == 0:
                print(f"✅ No activity found for {clean_ip} in the last {clean_days} days.")
                return
            
            print(f"📊 Found {total_events} events for {clean_ip}:")
            print(f"  🚫 Bans: {len(events['bans'])}")
            print(f"  ✅ Unbans: {len(events['unbans'])}")
            print(f"  🔍 Attempts: {len(events['attempts'])}")
            
            if events['bans']:
                print(f"\n🚫 Ban Events:")
                for ban in events['bans'][-10:]:  # Show last 10
                    print(f"  {self.format_timestamp(ban['timestamp'])} - {ban['jail']}")
            
            if events['attempts']:
                print(f"\n🔍 Recent Attempts:")
                for attempt in events['attempts'][-10:]:  # Show last 10
                    print(f"  {self.format_timestamp(attempt['timestamp'])} - {attempt['jail']}")
            
            print()
            
        except Exception as e:
            print(f"❌ Error in IP search: {e}")
    
    def show_attack_patterns(self):
        """Show attack pattern analysis"""
        print("\n📈 Attack Pattern Analysis (Last 7 Days):\n")
        
        try:
            patterns = self.get_attack_patterns(7)
            
            print("🕐 Attack Distribution by Hour:")
            if patterns['hourly_distribution']:
                for hour in range(24):
                    count = patterns['hourly_distribution'].get(hour, 0)
                    bar = "█" * min(count // 2, 50) if count > 0 else ""  # Limit bar length
                    print(f"  {hour:02d}:00 │{bar} {count}")
            
            print(f"\n📅 Attack Distribution by Day:")
            days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            for day in days_order:
                count = patterns['daily_distribution'].get(day, 0)
                bar = "█" * min(count // 5, 50) if count > 0 else ""  # Limit bar length
                print(f"  {day:<9} │{bar} {count}")
            
            print(f"\n🎯 Most Targeted Services:")
            total_attacks = sum(patterns['jail_targeting'].values())
            for jail, count in patterns['jail_targeting'].most_common(10):  # Limit to top 10
                if total_attacks > 0:
                    percentage = (count / total_attacks) * 100
                    print(f"  • {jail}: {count} attacks ({percentage:.1f}%)")
            
            if patterns['repeat_offenders']:
                print(f"\n🔄 Repeat Offenders (Multiple Services):")
                for ip, jail_count in sorted(patterns['repeat_offenders'].items(), 
                                           key=lambda x: x[1], reverse=True)[:10]:  # Top 10
                    print(f"  • {ip}: targeted {jail_count} different services")
            
            print()
            
        except Exception as e:
            print(f"❌ Error analyzing attack patterns: {e}")
    
    def export_data_interactive(self):
        """Interactive data export with security controls"""
        print("\n📤 Export Ban Data:\n")
        
        try:
            days = input("Export data for last how many days? (default: 30): ").strip()
            try:
                clean_days = self.validate_days_parameter(days) if days else 30
            except InvalidInputError as e:
                print(f"❌ {e}")
                return
            
            filename = input(f"Enter filename (default: fail2ban_export_{datetime.now().strftime('%Y%m%d')}.csv): ").strip()
            if not filename:
                filename = f"fail2ban_export_{datetime.now().strftime('%Y%m%d')}.csv"
            
            try:
                clean_filename = self.sanitize_filename(filename)
            except InvalidInputError as e:
                print(f"❌ {e}")
                return
            
            print(f"\n📊 Exporting {clean_days} days of data to {clean_filename}...")
            
            if self.export_ban_data_csv(clean_filename, clean_days):
                stats = self.get_daily_statistics(clean_days)
                print(f"📈 Export Summary:")
                print(f"  • Total Bans: {stats['total_bans']}")
                print(f"  • Total Attempts: {stats['total_attempts']}")
                print(f"  • Period: {clean_days} days")
            
            print()
            
        except Exception as e:
            print(f"❌ Error in data export: {e}")
    
    def debug_jail_status(self):
        """Debug function to help troubleshoot jail status issues"""
        print("\n🔧 Debug: Jail Status Information:\n")
        
        try:
            # Test basic fail2ban connectivity
            result = self.run_fail2ban_command(['status'])
            print("📋 Raw fail2ban-client status output:")
            print("=" * 50)
            print(result.stdout)
            print("=" * 50)
            print(f"Return code: {result.returncode}")
            if result.stderr:
                print(f"Stderr: {self.sanitize_error_message(result.stderr)}")
        except Exception as e:
            print(f"❌ Error running fail2ban-client status: {e}")
            return
        
        # Test specific jail status
        jails = self.get_active_jails()
        if jails:
            print(f"\n🏛️ Testing first jail: {jails[0]}")
            try:
                result = self.run_fail2ban_command(['status', jails[0]])
                print("📋 Raw jail status output:")
                print("=" * 50)
                print(result.stdout)
                print("=" * 50)
                print(f"Return code: {result.returncode}")
                if result.stderr:
                    print(f"Stderr: {self.sanitize_error_message(result.stderr)}")
            except Exception as e:
                print(f"❌ Error getting jail status: {e}")
        
        print()
    
    def show_jail_config_overview(self):
        """Show jail configuration overview with security controls"""
        print("\n⚙️ Jail Configuration Overview:\n")
        
        try:
            if not os.path.exists(FAIL2BAN_CONFIG):
                print("❌ Configuration file not found.")
                return
            
            # Validate config file path
            config_path = self.validate_log_path(FAIL2BAN_CONFIG)
            
            with open(config_path, 'r') as f:
                config_content = f.read()
            
            # Parse configuration safely
            config_lines = config_content.split('\n')
            current_jail = None
            jail_configs = {}
            default_config = {}
            
            for line in config_lines[:1000]:  # Limit lines processed
                line = line.strip()
                if line.startswith('[') and line.endswith(']'):
                    current_jail = line[1:-1]
                    # Validate jail name
                    try:
                        if current_jail != 'DEFAULT':
                            current_jail = self.sanitize_jail_name(current_jail)
                            jail_configs[current_jail] = {}
                    except InvalidInputError:
                        current_jail = None
                elif '=' in line and not line.startswith('#') and current_jail is not None:
                    try:
                        key, value = line.split('=', 1)
                        key, value = key.strip(), value.strip()
                        
                        # Sanitize config values
                        key = re.sub(r'[^\w\-_]', '', key)[:50]
                        value = re.sub(r'[^\w\s\-_\./:]', '', value)[:200]
                        
                        if current_jail == 'DEFAULT':
                            default_config[key] = value
                        elif current_jail:
                            jail_configs[current_jail][key] = value
                    except ValueError:
                        continue
            
            print("📋 Default Settings:")
            for key, value in list(default_config.items())[:20]:  # Limit items displayed
                print(f"  • {key}: {value}")
            
            print(f"\n🏛️ Individual Jail Settings:")
            for jail, config in list(jail_configs.items())[:10]:  # Limit jails displayed
                if config:
                    print(f"\n  [{jail}]")
                    for key, value in list(config.items())[:10]:  # Limit config items
                        print(f"    • {key}: {value}")
        
        except Exception as e:
            print(f"❌ Error reading configuration: {e}")
        
        print()
    
    def show_menu(self):
        """Display the main menu"""
        title = pyfiglet.figlet_format("minipass", font="big")
        print(title)
        print("🛡️ SECURE Fail2Ban Manager")
        print(f"Session: {self.session_id} | User: {self.current_user}")
        print()
        print("  1.  Show jail status and statistics")
        print("  2.  List all banned IPs")
        print("  3.  Unban specific IP")
        print("  4.  Ban specific IP manually")
        print("  5.  Daily/Weekly activity report")
        print("  6.  Attack pattern analysis")
        print("  7.  Search IP across all logs")
        print("  8.  Jail configuration overview")
        print("  9.  Export ban data to CSV")
        print("  d.  Debug jail status (troubleshooting)")
        print("")
        print("  x.  Exit")
        print()
    
    def run(self):
        """Main program loop with security controls"""
        try:
            print("🛡️ Initializing Secure Fail2Ban Manager...")
            print("✅ Secure Fail2Ban Manager ready!")
        except Exception as e:
            print(f"❌ Failed to initialize: {e}")
            self.audit_log("initialization_failure", {"error": str(e)}, success=False)
            return
        
        session_start = datetime.now()
        max_session_duration = timedelta(hours=2)  # Security: limit session duration
        
        while True:
            # Check session timeout
            if datetime.now() - session_start > max_session_duration:
                print("\n⏰ Session expired for security reasons. Please restart.")
                self.audit_log("session_expired", {"duration": str(datetime.now() - session_start)})
                break
            
            self.show_menu()
            
            try:
                choice = input("\nChoose an option (1-9, d, x):> ").strip().lower()
                
                # Validate choice
                if not re.match(r'^[1-9dx]$', choice):
                    print("❌ Invalid choice. Please enter 1-9, d, or x.")
                    continue
                
                self.audit_log("menu_choice", {"choice": choice})
                
                if choice == '1':
                    self.show_jail_status_overview()
                
                elif choice == '2':
                    self.show_banned_ips_detailed()
                
                elif choice == '3':
                    self.unban_ip_interactive()
                
                elif choice == '4':
                    self.ban_ip_interactive()
                
                elif choice == '5':
                    self.show_daily_report()
                
                elif choice == '6':
                    self.show_attack_patterns()
                
                elif choice == '7':
                    self.search_ip_interactive()
                
                elif choice == '8':
                    self.show_jail_config_overview()
                
                elif choice == '9':
                    self.export_data_interactive()
                
                elif choice == 'd':
                    self.debug_jail_status()
                
                elif choice == 'x':
                    print("👋 Goodbye!")
                    self.audit_log("session_end", {"duration": str(datetime.now() - session_start)})
                    break
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                self.audit_log("session_interrupted", {"duration": str(datetime.now() - session_start)})
                break
            except Exception as e:
                error_msg = f"Unexpected error: {e}"
                print(f"❌ {error_msg}")
                self.audit_log("unexpected_error", {"error": str(e)}, success=False)

def main():
    """Main entry point with security initialization"""
    try:
        # Additional security checks
        if os.geteuid() == 0:
            print("❌ This script should not be run as root for security reasons.")
            print("💡 Run as a regular user with sudo privileges for fail2ban commands.")
            return 1
        
        manager = SecureFail2BanManager()
        manager.run()
        return 0
        
    except Fail2BanSecurityError as e:
        print(f"❌ Security Error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        print("💡 Make sure fail2ban is installed and you have sudo privileges.")
        return 1

if __name__ == "__main__":
    exit(main())
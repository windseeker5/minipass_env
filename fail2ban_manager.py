#!/usr/bin/env python3

import os
import subprocess
import json
import re
import csv
import gzip
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import ipaddress

# Configuration
FAIL2BAN_CLIENT = "/usr/bin/fail2ban-client"
FAIL2BAN_LOG = "/var/log/fail2ban.log"
FAIL2BAN_CONFIG = "/etc/fail2ban/jail.local"

class Fail2BanManager:
    def __init__(self):
        self.check_fail2ban_available()
    
    def check_fail2ban_available(self):
        """Check if fail2ban is available and accessible"""
        try:
            if not os.path.exists(FAIL2BAN_CLIENT):
                raise Exception("fail2ban-client not found")
            
            # Test basic access (will require sudo for actual commands)
            result = subprocess.run(['which', 'fail2ban-client'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception("fail2ban-client not available")
                
        except Exception as e:
            raise Exception(f"Fail2ban check failed: {e}")
    
    def run_fail2ban_command(self, cmd_args, check=True):
        """Run fail2ban-client command with sudo"""
        try:
            command = ['sudo', FAIL2BAN_CLIENT] + cmd_args
            result = subprocess.run(command, capture_output=True, text=True, check=check)
            return result
        except subprocess.CalledProcessError as e:
            if check:
                raise Exception(f"Fail2ban command failed: {e.stderr}")
            return e
        except Exception as e:
            raise Exception(f"Error running fail2ban command: {e}")
    
    def get_active_jails(self):
        """Get list of active jails"""
        try:
            result = self.run_fail2ban_command(['status'])
            if result.returncode == 0:
                # Parse output to extract jail names
                output = result.stdout
                jail_line = None
                for line in output.split('\n'):
                    if 'Jail list:' in line:
                        jail_line = line
                        break
                
                if jail_line:
                    # Extract jails from "Jail list: jail1, jail2, jail3"
                    jails_part = jail_line.split('Jail list:')[1].strip()
                    if jails_part:
                        return [jail.strip() for jail in jails_part.split(',')]
                return []
            else:
                print(f"❌ Failed to get jail list: {result.stderr}")
                return []
        except Exception as e:
            print(f"❌ Error getting active jails: {e}")
            return []
    
    def get_jail_status(self, jail_name):
        """Get detailed status for a specific jail"""
        try:
            result = self.run_fail2ban_command(['status', jail_name])
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
                    if not line or not ':' in line:
                        continue
                        
                    try:
                        if 'Filter' in line:
                            parts = line.split(':', 1)
                            if len(parts) >= 2:
                                status_info['filter'] = parts[1].strip()
                        elif 'Actions' in line:
                            parts = line.split(':', 1)
                            if len(parts) >= 2:
                                status_info['actions'] = parts[1].strip()
                        elif 'Currently failed' in line:
                            parts = line.split(':', 1)
                            if len(parts) >= 2:
                                status_info['currently_failed'] = int(parts[1].strip())
                        elif 'Total failed' in line:
                            parts = line.split(':', 1)
                            if len(parts) >= 2:
                                status_info['total_failed'] = int(parts[1].strip())
                        elif 'Currently banned' in line:
                            parts = line.split(':', 1)
                            if len(parts) >= 2:
                                status_info['currently_banned'] = int(parts[1].strip())
                        elif 'Total banned' in line:
                            parts = line.split(':', 1)
                            if len(parts) >= 2:
                                status_info['total_banned'] = int(parts[1].strip())
                        elif 'Banned IP list' in line:
                            parts = line.split(':', 1)
                            if len(parts) >= 2:
                                ip_list = parts[1].strip()
                                status_info['banned_ips'] = [ip.strip() for ip in ip_list.split()] if ip_list else []
                    except (ValueError, IndexError) as e:
                        # Skip malformed lines
                        continue
                
                return status_info
            else:
                return None
        except Exception as e:
            print(f"❌ Error getting jail status for {jail_name}: {e}")
            return None
    
    def get_banned_ips(self, jail_name=None):
        """Get banned IPs for a specific jail or all jails"""
        banned_info = {}
        
        jails = [jail_name] if jail_name else self.get_active_jails()
        
        for jail in jails:
            status = self.get_jail_status(jail)
            if status and 'banned_ips' in status:
                banned_info[jail] = status['banned_ips']
            else:
                banned_info[jail] = []
        
        return banned_info
    
    def unban_ip(self, jail_name, ip_address):
        """Unban a specific IP from a jail"""
        try:
            result = self.run_fail2ban_command(['unban', ip_address], check=False)
            if result.returncode == 0:
                print(f"✅ Successfully unbanned {ip_address}")
                return True
            else:
                # Try jail-specific unban
                result = self.run_fail2ban_command(['set', jail_name, 'unbanip', ip_address], check=False)
                if result.returncode == 0:
                    print(f"✅ Successfully unbanned {ip_address} from {jail_name}")
                    return True
                else:
                    print(f"❌ Failed to unban {ip_address}: {result.stderr}")
                    return False
        except Exception as e:
            print(f"❌ Error unbanning {ip_address}: {e}")
            return False
    
    def ban_ip(self, jail_name, ip_address, duration=None):
        """Ban a specific IP in a jail"""
        try:
            result = self.run_fail2ban_command(['set', jail_name, 'banip', ip_address])
            if result.returncode == 0:
                duration_str = f" for {duration}" if duration else ""
                print(f"✅ Successfully banned {ip_address} in {jail_name}{duration_str}")
                return True
            else:
                print(f"❌ Failed to ban {ip_address}: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error banning {ip_address}: {e}")
            return False
    
    def parse_fail2ban_logs(self, days=1):
        """Parse fail2ban logs for the specified number of days"""
        log_data = {
            'bans': [],
            'unbans': [],
            'attempts': []
        }
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Read main log file
        try:
            if os.path.exists(FAIL2BAN_LOG):
                with open(FAIL2BAN_LOG, 'r') as f:
                    self._parse_log_content(f, log_data, cutoff_date)
        except PermissionError:
            # Try to read with sudo if direct access fails
            try:
                result = subprocess.run(['sudo', 'cat', FAIL2BAN_LOG], 
                                      capture_output=True, text=True, check=True)
                from io import StringIO
                self._parse_log_content(StringIO(result.stdout), log_data, cutoff_date)
            except:
                print("⚠️ Cannot read fail2ban log file. You may need to add your user to the 'adm' group.")
                print("Run: sudo usermod -a -G adm $(whoami)")
                print("Then log out and back in for changes to take effect.")
                return log_data
        except Exception as e:
            print(f"❌ Error reading log file: {e}")
        
        # Read rotated log files
        for i in range(1, 8):  # Check up to 7 rotated logs
            log_file = f"{FAIL2BAN_LOG}.{i}"
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        self._parse_log_content(f, log_data, cutoff_date)
                except:
                    continue
            
            # Check compressed logs
            gz_log_file = f"{log_file}.gz"
            if os.path.exists(gz_log_file):
                try:
                    with gzip.open(gz_log_file, 'rt') as f:
                        self._parse_log_content(f, log_data, cutoff_date)
                except:
                    continue
        
        return log_data
    
    def _parse_log_content(self, file_handle, log_data, cutoff_date):
        """Parse log file content and extract relevant information"""
        ban_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).*\[(\w+)\].*Ban (\d+\.\d+\.\d+\.\d+)')
        unban_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).*\[(\w+)\].*Unban (\d+\.\d+\.\d+\.\d+)')
        attempt_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).*\[(\w+)\].*Found (\d+\.\d+\.\d+\.\d+)')
        
        for line in file_handle:
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
                    log_data['bans'].append({
                        'timestamp': timestamp,
                        'jail': ban_match.group(2),
                        'ip': ban_match.group(3)
                    })
                    continue
                
                # Check for unban events
                unban_match = unban_pattern.search(line)
                if unban_match:
                    log_data['unbans'].append({
                        'timestamp': timestamp,
                        'jail': unban_match.group(2),
                        'ip': unban_match.group(3)
                    })
                    continue
                
                # Check for attempt events
                attempt_match = attempt_pattern.search(line)
                if attempt_match:
                    log_data['attempts'].append({
                        'timestamp': timestamp,
                        'jail': attempt_match.group(2),
                        'ip': attempt_match.group(3)
                    })
                
            except Exception:
                continue
    
    def get_daily_statistics(self, days=1):
        """Get daily statistics for the specified number of days"""
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
    
    def get_attack_patterns(self, days=7):
        """Analyze attack patterns over the specified period"""
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
    
    def search_ip_in_logs(self, ip_address, days=30):
        """Search for a specific IP in logs"""
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
    
    def format_timestamp(self, timestamp):
        """Format timestamp for display"""
        return timestamp.strftime('%Y-%m-%d %H:%M:%S')
    
    def validate_ip(self, ip_string):
        """Validate IP address format"""
        try:
            ipaddress.ip_address(ip_string)
            return True
        except ValueError:
            return False
    
    def export_ban_data_csv(self, filename, days=30):
        """Export ban data to CSV file"""
        log_data = self.parse_fail2ban_logs(days)
        
        try:
            with open(filename, 'w', newline='') as csvfile:
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
            
            print(f"✅ Ban data exported to {filename}")
            return True
        except Exception as e:
            print(f"❌ Error exporting data: {e}")
            return False

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
        """Interactive IP unbanning"""
        print("\n✅ Unban IP Address:\n")
        
        # Show current banned IPs
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
            if self.validate_ip(ip):
                # Unban from all jails
                unbanned = False
                for jail in self.get_active_jails():
                    if self.unban_ip(jail, ip):
                        unbanned = True
                if not unbanned:
                    print(f"⚠️ {ip} was not found in any banned lists.")
            else:
                print("❌ Invalid IP address format.")
        
        elif choice == "3":
            return
        else:
            print("❌ Invalid choice.")
    
    def ban_ip_interactive(self):
        """Interactive IP banning"""
        print("\n⚠️ Ban IP Address:\n")
        
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
                if not self.validate_ip(ip):
                    print("❌ Invalid IP address format.")
                    return
                
                reason = input("Enter reason (optional): ").strip()
                
                if self.ban_ip(jail, ip):
                    if reason:
                        print(f"📝 Reason logged: {reason}")
                
            else:
                print("❌ Invalid jail number.")
        except ValueError:
            print("❌ Invalid input.")
    
    def show_daily_report(self):
        """Show daily activity report"""
        print("\n📈 Daily Activity Report:\n")
        
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
    
    def search_ip_interactive(self):
        """Interactive IP search"""
        print("\n🔍 Search IP Address:\n")
        
        ip = input("Enter IP address to search: ").strip()
        if not self.validate_ip(ip):
            print("❌ Invalid IP address format.")
            return
        
        days = input("Search last how many days? (default: 30): ").strip()
        try:
            days = int(days) if days else 30
        except ValueError:
            days = 30
        
        print(f"\n🔍 Searching for {ip} in last {days} days...\n")
        
        events = self.search_ip_in_logs(ip, days)
        
        total_events = len(events['bans']) + len(events['unbans']) + len(events['attempts'])
        
        if total_events == 0:
            print(f"✅ No activity found for {ip} in the last {days} days.")
            return
        
        print(f"📊 Found {total_events} events for {ip}:")
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
    
    def show_attack_patterns(self):
        """Show attack pattern analysis"""
        print("\n📈 Attack Pattern Analysis (Last 7 Days):\n")
        
        patterns = self.get_attack_patterns(7)
        
        print("🕐 Attack Distribution by Hour:")
        if patterns['hourly_distribution']:
            for hour in range(24):
                count = patterns['hourly_distribution'].get(hour, 0)
                bar = "█" * (count // 2) if count > 0 else ""
                print(f"  {hour:02d}:00 │{bar} {count}")
        
        print(f"\n📅 Attack Distribution by Day:")
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for day in days_order:
            count = patterns['daily_distribution'].get(day, 0)
            bar = "█" * (count // 5) if count > 0 else ""
            print(f"  {day:<9} │{bar} {count}")
        
        print(f"\n🎯 Most Targeted Services:")
        for jail, count in patterns['jail_targeting'].most_common():
            percentage = (count / sum(patterns['jail_targeting'].values())) * 100
            print(f"  • {jail}: {count} attacks ({percentage:.1f}%)")
        
        if patterns['repeat_offenders']:
            print(f"\n🔄 Repeat Offenders (Multiple Services):")
            for ip, jail_count in sorted(patterns['repeat_offenders'].items(), 
                                       key=lambda x: x[1], reverse=True)[:10]:
                print(f"  • {ip}: targeted {jail_count} different services")
        
        print()
    
    def export_data_interactive(self):
        """Interactive data export"""
        print("\n📤 Export Ban Data:\n")
        
        days = input("Export data for last how many days? (default: 30): ").strip()
        try:
            days = int(days) if days else 30
        except ValueError:
            days = 30
        
        filename = input(f"Enter filename (default: fail2ban_export_{datetime.now().strftime('%Y%m%d')}.csv): ").strip()
        if not filename:
            filename = f"fail2ban_export_{datetime.now().strftime('%Y%m%d')}.csv"
        
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        print(f"\n📊 Exporting {days} days of data to {filename}...")
        
        if self.export_ban_data_csv(filename, days):
            stats = self.get_daily_statistics(days)
            print(f"📈 Export Summary:")
            print(f"  • Total Bans: {stats['total_bans']}")
            print(f"  • Total Attempts: {stats['total_attempts']}")
            print(f"  • Period: {days} days")
        
        print()
    
    def debug_jail_status(self):
        """Debug function to help troubleshoot jail status issues"""
        print("\n🔧 Debug: Jail Status Information:\n")
        
        # Test basic fail2ban connectivity
        try:
            result = self.run_fail2ban_command(['status'])
            print("📋 Raw fail2ban-client status output:")
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
                result = self.run_fail2ban_command(['status', jails[0]])
                print("📋 Raw jail status output:")
                print("=" * 50)
                print(result.stdout)
                print("=" * 50)
                print(f"Return code: {result.returncode}")
                if result.stderr:
                    print(f"Stderr: {result.stderr}")
            except Exception as e:
                print(f"❌ Error getting jail status: {e}")
        
        print()
    
    def show_jail_config_overview(self):
        """Show jail configuration overview"""
        print("\n⚙️ Jail Configuration Overview:\n")
        
        try:
            if os.path.exists(FAIL2BAN_CONFIG):
                with open(FAIL2BAN_CONFIG, 'r') as f:
                    config_content = f.read()
                
                # Extract key configuration values
                config_lines = config_content.split('\n')
                current_jail = None
                jail_configs = {}
                default_config = {}
                
                for line in config_lines:
                    line = line.strip()
                    if line.startswith('[') and line.endswith(']'):
                        current_jail = line[1:-1]
                        if current_jail != 'DEFAULT':
                            jail_configs[current_jail] = {}
                    elif '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        key, value = key.strip(), value.strip()
                        
                        if current_jail == 'DEFAULT':
                            default_config[key] = value
                        elif current_jail:
                            jail_configs[current_jail][key] = value
                
                print("📋 Default Settings:")
                for key, value in default_config.items():
                    print(f"  • {key}: {value}")
                
                print(f"\n🏛️ Individual Jail Settings:")
                for jail, config in jail_configs.items():
                    if config:  # Only show jails with custom settings
                        print(f"\n  [{jail}]")
                        for key, value in config.items():
                            print(f"    • {key}: {value}")
            else:
                print("❌ Configuration file not found.")
        
        except Exception as e:
            print(f"❌ Error reading configuration: {e}")
        
        print()
    
    def show_menu(self):
        """Display the main menu"""
        print("\n" + "="*60)
        print("   🛡️ FAIL2BAN MANAGEMENT TOOL")
        print("="*60)
        print("1. 📊 Show jail status and statistics")
        print("2. 🚫 List all banned IPs")
        print("3. ✅ Unban specific IP")
        print("4. ⚠️ Ban specific IP manually")
        print("5. 📋 Daily/Weekly activity report")
        print("6. 📈 Attack pattern analysis")
        print("7. 🔍 Search IP across all logs")
        print("8. ⚙️ Jail configuration overview")
        print("9. 📤 Export ban data to CSV")
        print("d. 🔧 Debug jail status (troubleshooting)")
        print("x. ❌ Exit")
        print("="*60)
    
    def run(self):
        """Main program loop"""
        try:
            print("🛡️ Initializing Fail2Ban Manager...")
            print("✅ Fail2Ban Manager ready!")
        except Exception as e:
            print(f"❌ Failed to initialize: {e}")
            return
        
        while True:
            self.show_menu()
            
            try:
                choice = input("\nChoose an option (1-9, d, x): ").strip().lower()
                
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
                    break
                
                else:
                    print("❌ Invalid choice. Please enter 1-9, d, or x.")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")

def main():
    """Main entry point"""
    try:
        manager = Fail2BanManager()
        manager.run()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        print("💡 Make sure fail2ban is installed and you have sudo privileges.")

if __name__ == "__main__":
    main()
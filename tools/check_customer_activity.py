#!/usr/bin/env python3
"""
Customer Activity Checker

A tool for checking if customers have recent activity before performing upgrades.
Analyzes docker containers, nginx logs, and database activity to determine if
it's safe to upgrade a customer's container.

Usage:
    python3 check_customer_activity.py lhgi
    python3 check_customer_activity.py --all
    python3 check_customer_activity.py lhgi --debug
    python3 check_customer_activity.py --timeout 15 lhgi
"""

import argparse
import os
import sqlite3
import subprocess
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
MINIPASS_ENV_PATH = "/home/kdresdell/minipass_env"
DEPLOYED_PATH = f"{MINIPASS_ENV_PATH}/deployed"
NGINX_LOG_PATH = "/var/log/nginx/access.log"

# Known customers and their container names
CUSTOMERS = {
    "lhgi": {
        "container_name": "minipass_lhgi",
        "domain": "lhgi.minipass.me",
        "db_path": f"{DEPLOYED_PATH}/lhgi/app/instance/minipass.db"
    },
    "heq": {
        "container_name": "minipass_heq",
        "domain": "heq.minipass.me",
        "db_path": f"{DEPLOYED_PATH}/heq/app/instance/minipass.db"
    }
}

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def log(message: str, level: str = "INFO", color: str = "") -> None:
    """Print timestamped log message with optional color."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if color:
        print(f"{color}[{timestamp}] [{level}] {message}{Colors.END}")
    else:
        print(f"[{timestamp}] [{level}] {message}")

def run_command(command: str, capture_output: bool = True, timeout: int = 30) -> tuple[bool, str]:
    """Run a shell command and return success status and output."""
    try:
        if capture_output:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            output = result.stdout + result.stderr
            return result.returncode == 0, output.strip()
        else:
            result = subprocess.run(command, shell=True, timeout=timeout)
            return result.returncode == 0, ""
    except subprocess.TimeoutExpired:
        return False, f"Command timed out after {timeout} seconds"
    except Exception as e:
        return False, str(e)

class ActivityChecker:
    """Main class for checking customer activity."""

    def __init__(self, debug: bool = False, timeout_minutes: int = 10):
        self.debug = debug
        self.timeout_minutes = timeout_minutes
        self.cutoff_time = datetime.now() - timedelta(minutes=timeout_minutes)

    def debug_log(self, message: str) -> None:
        """Log debug message if debug mode is enabled."""
        if self.debug:
            log(message, "DEBUG", Colors.BLUE)

    def check_docker_activity(self, customer: str) -> dict:
        """Check Docker container resource usage and connections."""
        self.debug_log(f"Checking Docker activity for {customer}")

        customer_config = CUSTOMERS.get(customer)
        if not customer_config:
            return {"error": f"Unknown customer: {customer}"}

        container_name = customer_config["container_name"]

        # Check if container is running
        success, output = run_command(f"docker ps --filter name={container_name} --format '{{{{.Names}}}}'")
        if not success or container_name not in output:
            return {"status": "stopped", "message": "Container not running"}

        # Get container stats
        success, stats = run_command(f"docker stats {container_name} --no-stream --format 'table {{{{.CPUPerc}}}},{{{{.MemUsage}}}}'")
        if not success:
            return {"error": "Could not get container stats"}

        # Parse stats (skip header line)
        lines = stats.split('\n')
        if len(lines) < 2:
            return {"error": "Unexpected stats format"}

        stats_line = lines[1]
        cpu_mem = stats_line.split(',')
        if len(cpu_mem) >= 2:
            cpu_percent = cpu_mem[0].replace('%', '').strip()
            memory_usage = cpu_mem[1].strip()
        else:
            cpu_percent = "0.00"
            memory_usage = "unknown"

        # Check active connections
        success, conn_output = run_command(f"docker exec {container_name} netstat -an 2>/dev/null | grep ESTABLISHED | wc -l")
        active_connections = int(conn_output) if success and conn_output.isdigit() else 0

        self.debug_log(f"Docker stats - CPU: {cpu_percent}%, Memory: {memory_usage}, Connections: {active_connections}")

        # Determine activity level
        try:
            cpu_float = float(cpu_percent)
            high_activity = cpu_float > 5.0 or active_connections > 2
        except ValueError:
            high_activity = active_connections > 2

        return {
            "status": "active" if high_activity else "idle",
            "cpu_percent": cpu_percent,
            "memory_usage": memory_usage,
            "active_connections": active_connections,
            "high_activity": high_activity
        }

    def check_nginx_activity(self, customer: str) -> dict:
        """Check nginx access logs for recent activity."""
        self.debug_log(f"Checking nginx activity for {customer}")

        customer_config = CUSTOMERS.get(customer)
        if not customer_config:
            return {"error": f"Unknown customer: {customer}"}

        domain = customer_config["domain"]

        if not os.path.exists(NGINX_LOG_PATH):
            self.debug_log(f"Nginx log not found: {NGINX_LOG_PATH}")
            return {"status": "unknown", "message": "Nginx log not accessible"}

        # Check for recent requests in the last N minutes
        cutoff_str = self.cutoff_time.strftime("%d/%b/%Y:%H:%M")

        # Use grep to find recent requests for this domain
        success, output = run_command(
            f"grep '{domain}' {NGINX_LOG_PATH} 2>/dev/null | tail -n 100 | grep '{cutoff_str}' | wc -l"
        )

        if not success:
            return {"status": "unknown", "message": "Could not check nginx logs"}

        recent_requests = int(output) if output.isdigit() else 0

        # Get the last request timestamp if any
        success, last_request = run_command(
            f"grep '{domain}' {NGINX_LOG_PATH} 2>/dev/null | tail -n 1"
        )

        last_activity = "None found"
        if success and last_request:
            # Extract timestamp from nginx log format
            try:
                # Nginx log format: IP - - [timestamp] "request" status size
                timestamp_start = last_request.find('[') + 1
                timestamp_end = last_request.find(']')
                if timestamp_start > 0 and timestamp_end > timestamp_start:
                    last_activity = last_request[timestamp_start:timestamp_end]
            except:
                last_activity = "Could not parse"

        self.debug_log(f"Nginx activity - Recent requests ({self.timeout_minutes}min): {recent_requests}, Last: {last_activity}")

        return {
            "status": "active" if recent_requests > 0 else "idle",
            "recent_requests": recent_requests,
            "last_activity": last_activity,
            "timeout_minutes": self.timeout_minutes
        }

    def check_database_activity(self, customer: str) -> dict:
        """Check database for recent admin actions and user activity."""
        self.debug_log(f"Checking database activity for {customer}")

        customer_config = CUSTOMERS.get(customer)
        if not customer_config:
            return {"error": f"Unknown customer: {customer}"}

        db_path = customer_config["db_path"]

        if not os.path.exists(db_path):
            return {"status": "unknown", "message": f"Database not found: {db_path}"}

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check for recent admin actions
            cutoff_str = self.cutoff_time.strftime("%Y-%m-%d %H:%M:%S")

            recent_activity = {}

            # Check admin action logs (correct table name)
            try:
                cursor.execute("""
                    SELECT COUNT(*) FROM admin_action_log
                    WHERE timestamp > ?
                """, (cutoff_str,))
                recent_activity['admin_actions'] = cursor.fetchone()[0]
            except sqlite3.OperationalError:
                recent_activity['admin_actions'] = 0

            # Check recent signups (correct table name and column)
            try:
                cursor.execute("""
                    SELECT COUNT(*) FROM signup
                    WHERE signed_up_at > ?
                """, (cutoff_str,))
                recent_activity['signups'] = cursor.fetchone()[0]
            except sqlite3.OperationalError:
                recent_activity['signups'] = 0

            # Check recent redemptions (correct table name and column)
            try:
                cursor.execute("""
                    SELECT COUNT(*) FROM redemption
                    WHERE date_used > ?
                """, (cutoff_str,))
                recent_activity['redemptions'] = cursor.fetchone()[0]
            except sqlite3.OperationalError:
                recent_activity['redemptions'] = 0

            # Get most recent activity timestamps
            try:
                cursor.execute("""
                    SELECT MAX(timestamp) FROM admin_action_log
                """)
                last_admin = cursor.fetchone()[0] or "Never"

                cursor.execute("""
                    SELECT MAX(signed_up_at) FROM signup
                """)
                last_signup = cursor.fetchone()[0] or "Never"

                cursor.execute("""
                    SELECT MAX(date_used) FROM redemption
                """)
                last_redemption = cursor.fetchone()[0] or "Never"

                recent_activity['last_admin_action'] = last_admin
                recent_activity['last_signup'] = last_signup
                recent_activity['last_redemption'] = last_redemption

                # Get the most recent admin action details for context
                cursor.execute("""
                    SELECT timestamp, admin_email, action FROM admin_action_log
                    ORDER BY timestamp DESC LIMIT 1
                """)
                last_action_row = cursor.fetchone()
                if last_action_row:
                    recent_activity['last_action_details'] = {
                        'timestamp': last_action_row[0],
                        'admin': last_action_row[1],
                        'action': last_action_row[2][:100] + '...' if len(last_action_row[2]) > 100 else last_action_row[2]
                    }

            except sqlite3.OperationalError as e:
                self.debug_log(f"Error getting timestamps: {e}")
                recent_activity['last_admin_action'] = "Error"
                recent_activity['last_signup'] = "Error"
                recent_activity['last_redemption'] = "Error"

            conn.close()

            total_activity = (
                recent_activity.get('admin_actions', 0) +
                recent_activity.get('signups', 0) +
                recent_activity.get('redemptions', 0)
            )

            self.debug_log(f"Database activity - Total recent: {total_activity}, Details: {recent_activity}")

            return {
                "status": "active" if total_activity > 0 else "idle",
                "total_recent_activity": total_activity,
                **recent_activity
            }

        except sqlite3.Error as e:
            return {"error": f"Database error: {e}"}

    def check_container_health(self, customer: str) -> dict:
        """Check container health and responsiveness."""
        self.debug_log(f"Checking container health for {customer}")

        customer_config = CUSTOMERS.get(customer)
        if not customer_config:
            return {"error": f"Unknown customer: {customer}"}

        domain = customer_config["domain"]

        # Try to get a quick HTTP response
        success, output = run_command(
            f"curl -s -I -m 5 https://{domain} | head -n 1",
            timeout=10
        )

        if success and "200 OK" in output:
            health_status = "healthy"
            response_info = "HTTP 200 OK"
        elif success:
            health_status = "responding"
            response_info = output
        else:
            health_status = "unreachable"
            response_info = "No response"

        self.debug_log(f"Container health - Status: {health_status}, Response: {response_info}")

        return {
            "status": health_status,
            "response": response_info
        }

    def check_customer_activity(self, customer: str) -> dict:
        """Perform comprehensive activity check for a customer."""
        if customer not in CUSTOMERS:
            return {
                "customer": customer,
                "error": f"Unknown customer: {customer}. Available: {', '.join(CUSTOMERS.keys())}"
            }

        log(f"🔍 Checking activity for {customer.upper()}...", color=Colors.BOLD)

        result = {
            "customer": customer,
            "timestamp": datetime.now().isoformat(),
            "timeout_minutes": self.timeout_minutes,
            "checks": {}
        }

        # Run all checks
        result["checks"]["docker"] = self.check_docker_activity(customer)
        result["checks"]["nginx"] = self.check_nginx_activity(customer)
        result["checks"]["database"] = self.check_database_activity(customer)
        result["checks"]["health"] = self.check_container_health(customer)

        # Analyze overall activity
        activity_detected = False
        activity_sources = []

        for check_name, check_result in result["checks"].items():
            if check_result.get("status") == "active" or check_result.get("high_activity"):
                activity_detected = True
                activity_sources.append(check_name)

        result["overall_status"] = "active" if activity_detected else "idle"
        result["activity_sources"] = activity_sources
        result["safe_to_upgrade"] = not activity_detected

        return result

def format_result(result: dict, debug: bool = False) -> None:
    """Format and display the activity check result."""
    customer = result.get("customer", "unknown")

    print("\n" + "="*60)
    print(f"  ACTIVITY CHECK RESULT: {customer.upper()}")
    print("="*60)

    if "error" in result:
        log(f"❌ ERROR: {result['error']}", "ERROR", Colors.RED)
        return

    # Overall status
    safe = result.get("safe_to_upgrade", False)
    overall_status = result.get("overall_status", "unknown")

    if safe:
        log("✅ SAFE TO UPGRADE", "RESULT", Colors.GREEN)
        status_msg = f"No recent activity detected (last {result.get('timeout_minutes', 10)} minutes)"
    else:
        log("⚠️  WAIT - ACTIVITY DETECTED", "RESULT", Colors.YELLOW)
        sources = result.get("activity_sources", [])
        status_msg = f"Activity detected in: {', '.join(sources)}"

    print(f"   {status_msg}")

    # Check details
    checks = result.get("checks", {})

    print(f"\n📊 DETAILED RESULTS:")

    # Docker check
    docker = checks.get("docker", {})
    if docker.get("status") == "active":
        print(f"   🐳 Docker: {Colors.YELLOW}ACTIVE{Colors.END} - CPU: {docker.get('cpu_percent', 'N/A')}%, Connections: {docker.get('active_connections', 0)}")
    elif docker.get("status") == "idle":
        print(f"   🐳 Docker: {Colors.GREEN}IDLE{Colors.END} - CPU: {docker.get('cpu_percent', 'N/A')}%, Connections: {docker.get('active_connections', 0)}")
    elif "error" in docker:
        print(f"   🐳 Docker: {Colors.RED}ERROR{Colors.END} - {docker['error']}")
    else:
        print(f"   🐳 Docker: STOPPED")

    # Nginx check
    nginx = checks.get("nginx", {})
    if nginx.get("status") == "active":
        print(f"   🌐 Nginx: {Colors.YELLOW}ACTIVE{Colors.END} - {nginx.get('recent_requests', 0)} requests in last {nginx.get('timeout_minutes', 10)}min")
    elif nginx.get("status") == "idle":
        print(f"   🌐 Nginx: {Colors.GREEN}IDLE{Colors.END} - No recent requests")
    else:
        print(f"   🌐 Nginx: UNKNOWN - {nginx.get('message', 'Could not check')}")

    # Database check
    database = checks.get("database", {})
    if database.get("status") == "active":
        total = database.get("total_recent_activity", 0)
        admin_count = database.get("admin_actions", 0)
        signup_count = database.get("signups", 0)
        redemption_count = database.get("redemptions", 0)
        print(f"   📄 Database: {Colors.YELLOW}ACTIVE{Colors.END} - {total} recent actions (Admin: {admin_count}, Signups: {signup_count}, Redemptions: {redemption_count})")

        # Show last action details if available
        last_action = database.get("last_action_details")
        if last_action:
            print(f"      Last action: {last_action['admin']} at {last_action['timestamp']} - {last_action['action']}")
    elif database.get("status") == "idle":
        print(f"   📄 Database: {Colors.GREEN}IDLE{Colors.END} - No recent activity")

        # Still show when last activity was, even if not recent
        last_admin = database.get("last_admin_action")
        if last_admin and last_admin != "Never" and last_admin != "Error":
            print(f"      Last admin action: {last_admin}")
    else:
        print(f"   📄 Database: UNKNOWN - {database.get('message', 'Could not check')}")

    # Health check
    health = checks.get("health", {})
    health_status = health.get("status", "unknown")
    if health_status == "healthy":
        print(f"   ❤️  Health: {Colors.GREEN}HEALTHY{Colors.END} - {health.get('response', '')}")
    elif health_status == "responding":
        print(f"   ❤️  Health: {Colors.YELLOW}RESPONDING{Colors.END} - {health.get('response', '')}")
    else:
        print(f"   ❤️  Health: {Colors.RED}UNREACHABLE{Colors.END}")

    # Debug output
    if debug:
        print(f"\n🐛 DEBUG INFO:")
        print(f"   Timeout: {result.get('timeout_minutes', 10)} minutes")
        print(f"   Timestamp: {result.get('timestamp', 'unknown')}")
        if nginx.get('last_activity'):
            print(f"   Last nginx request: {nginx['last_activity']}")
        if database.get('last_admin_action'):
            print(f"   Last admin action: {database['last_admin_action']}")

    print("\n" + "="*60 + "\n")

def main():
    parser = argparse.ArgumentParser(
        description="Check customer activity before upgrades",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s lhgi                    # Check LHGI customer
  %(prog)s --all                   # Check all customers
  %(prog)s lhgi --debug            # Debug mode
  %(prog)s --timeout 15 lhgi       # Custom timeout
"""
    )

    parser.add_argument(
        "customer",
        nargs="?",
        help="Customer to check (lhgi, heq)"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Check all customers"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output"
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Activity timeout in minutes (default: 10)"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format"
    )

    args = parser.parse_args()

    # Validation
    if not args.all and not args.customer:
        parser.error("Must specify a customer or use --all")

    if args.customer and args.customer not in CUSTOMERS:
        available = ", ".join(CUSTOMERS.keys())
        parser.error(f"Unknown customer: {args.customer}. Available: {available}")

    # Initialize checker
    checker = ActivityChecker(debug=args.debug, timeout_minutes=args.timeout)

    # Header
    if not args.json:
        print("\n" + "🔍 CUSTOMER ACTIVITY CHECKER" + "\n")
        if args.debug:
            print(f"Debug mode enabled | Timeout: {args.timeout} minutes\n")

    # Check customers
    customers_to_check = [args.customer] if args.customer else list(CUSTOMERS.keys())
    results = []

    all_safe = True

    for customer in customers_to_check:
        result = checker.check_customer_activity(customer)
        results.append(result)

        if not result.get("safe_to_upgrade", False):
            all_safe = False

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            format_result(result, debug=args.debug)

    # Summary for multiple customers
    if len(customers_to_check) > 1 and not args.json:
        print("📋 SUMMARY:")
        for result in results:
            customer = result["customer"].upper()
            if result.get("safe_to_upgrade", False):
                print(f"   ✅ {customer}: Safe to upgrade")
            else:
                print(f"   ⚠️  {customer}: Activity detected")
        print()

    # Exit code: 0 if all safe, 1 if any have activity
    sys.exit(0 if all_safe else 1)

if __name__ == "__main__":
    main()
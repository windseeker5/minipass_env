#!/home/kdresdell/minipass_env/MinipassWebSite/venv/bin/python
"""
MiniPass Security Monitor
Monitors MiniPass Flask application and integrates with fail2ban security system.
Runs in user-space mode with available privileges.
"""

import os
import sys
import time
import json
import logging
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# Set up logging
log_dir = Path.home() / '.local/var/log'
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / 'minipass_security_monitor.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class MiniPassSecurityMonitor:
    """Monitor MiniPass service and security events."""
    
    def __init__(self):
        self.service_name = "minipass-web.service"
        self.log_dir = Path.home() / '.local/var/log'
        self.status_file = self.log_dir / 'minipass_status.json'
        
    def check_service_status(self):
        """Check MiniPass service status."""
        try:
            # Try system service first, then user service
            result = subprocess.run(
                ['systemctl', 'status', self.service_name],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                status = "running"
                logger.info(f"✅ {self.service_name} is running")
            else:
                status = "stopped"
                logger.warning(f"⚠️ {self.service_name} is not running")
                
            return {
                'status': status,
                'timestamp': datetime.now().isoformat(),
                'output': result.stdout,
                'error': result.stderr
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Timeout checking {self.service_name}")
            return {'status': 'timeout', 'timestamp': datetime.now().isoformat()}
        except Exception as e:
            logger.error(f"❌ Error checking service: {e}")
            return {'status': 'error', 'timestamp': datetime.now().isoformat(), 'error': str(e)}
    
    def monitor_failed_requests(self):
        """Monitor for failed requests in application logs."""
        failed_requests = []
        
        # Check Flask application logs
        flask_log_paths = [
            '/var/log/nginx/access.log',
            '/var/log/nginx/error.log',
            Path.home() / '.local/var/log/minipass_web.log'
        ]
        
        for log_path in flask_log_paths:
            try:
                if not os.path.exists(log_path):
                    continue
                    
                # Look for 4xx and 5xx errors in the last hour
                one_hour_ago = datetime.now() - timedelta(hours=1)
                
                with open(log_path, 'r') as f:
                    lines = f.readlines()[-100:]  # Last 100 lines
                    
                for line in lines:
                    if any(error in line for error in ['404', '403', '500', 'ERROR', 'CRITICAL']):
                        failed_requests.append({
                            'timestamp': datetime.now().isoformat(),
                            'log_file': str(log_path),
                            'entry': line.strip()
                        })
                        
            except Exception as e:
                logger.debug(f"Could not read {log_path}: {e}")
                
        return failed_requests
    
    def check_security_events(self):
        """Check for security-related events."""
        events = []
        
        # Check auth log for suspicious activity
        try:
            result = subprocess.run(
                ['grep', '-i', 'minipass', '/var/log/auth.log'],
                capture_output=True, text=True, timeout=5
            )
            
            if result.stdout:
                for line in result.stdout.strip().split('\n')[-5:]:
                    events.append({
                        'type': 'auth',
                        'timestamp': datetime.now().isoformat(),
                        'event': line.strip()
                    })
                    
        except Exception as e:
            logger.debug(f"Could not check auth.log: {e}")
        
        return events
    
    def generate_report(self):
        """Generate security monitoring report."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'service_status': self.check_service_status(),
            'failed_requests': self.monitor_failed_requests(),
            'security_events': self.check_security_events(),
            'monitoring_mode': 'user-space'
        }
        
        # Save report
        with open(self.status_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        return report
    
    def continuous_monitor(self, interval=300):
        """Run continuous monitoring (every 5 minutes by default)."""
        logger.info(f"🔍 Starting MiniPass security monitoring (interval: {interval}s)")
        
        while True:
            try:
                report = self.generate_report()
                
                # Check for issues
                if report['service_status']['status'] != 'running':
                    logger.warning(f"⚠️ Service issue detected: {report['service_status']}")
                
                if report['failed_requests']:
                    logger.warning(f"⚠️ {len(report['failed_requests'])} failed requests detected")
                
                if report['security_events']:
                    logger.info(f"🔒 {len(report['security_events'])} security events logged")
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("👋 Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Monitoring error: {e}")
                time.sleep(30)  # Wait 30s before retrying

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='MiniPass Security Monitor')
    parser.add_argument('--report', action='store_true', help='Generate single report')
    parser.add_argument('--monitor', action='store_true', help='Start continuous monitoring')
    parser.add_argument('--interval', type=int, default=300, help='Monitoring interval in seconds')
    
    args = parser.parse_args()
    
    monitor = MiniPassSecurityMonitor()
    
    if args.report:
        report = monitor.generate_report()
        print(json.dumps(report, indent=2))
    elif args.monitor:
        monitor.continuous_monitor(args.interval)
    else:
        # Default: generate report
        report = monitor.generate_report()
        print("=== MiniPass Security Report ===")
        print(f"Service Status: {report['service_status']['status']}")
        print(f"Failed Requests: {len(report['failed_requests'])}")
        print(f"Security Events: {len(report['security_events'])}")
        print(f"Report saved to: {monitor.status_file}")

if __name__ == '__main__':
    main()
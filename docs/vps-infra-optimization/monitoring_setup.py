#!/usr/bin/env python3
"""
VPS Monitoring Setup Script
Creates comprehensive monitoring for resources, performance, and health
"""

import os
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path
import schedule

class VPSMonitor:
    def __init__(self):
        self.base_path = Path('/home/kdresdell/minipass_env')
        self.logs_path = self.base_path / 'monitoring_logs'
        self.logs_path.mkdir(exist_ok=True)

    def collect_system_metrics(self):
        """Collect system resource metrics"""
        timestamp = datetime.now().isoformat()

        # Memory usage
        mem_output = subprocess.run(['free', '-b'], capture_output=True, text=True).stdout.split('\n')[1].split()
        memory = {
            'total': int(mem_output[1]),
            'used': int(mem_output[2]),
            'free': int(mem_output[3]),
            'available': int(mem_output[6]),
            'usage_percent': round((int(mem_output[2]) / int(mem_output[1])) * 100, 2)
        }

        # Disk usage
        disk_output = subprocess.run(['df', '-B1', '/'], capture_output=True, text=True).stdout.split('\n')[1].split()
        disk = {
            'total': int(disk_output[1]),
            'used': int(disk_output[2]),
            'available': int(disk_output[3]),
            'usage_percent': round((int(disk_output[2]) / int(disk_output[1])) * 100, 2)
        }

        # CPU load
        load_output = subprocess.run(['cat', '/proc/loadavg'], capture_output=True, text=True).stdout.split()
        cpu = {
            'load_1min': float(load_output[0]),
            'load_5min': float(load_output[1]),
            'load_15min': float(load_output[2])
        }

        # Network stats
        network_stats = self.get_network_stats()

        return {
            'timestamp': timestamp,
            'memory': memory,
            'disk': disk,
            'cpu': cpu,
            'network': network_stats
        }

    def get_network_stats(self):
        """Get network interface statistics"""
        try:
            with open('/proc/net/dev', 'r') as f:
                lines = f.readlines()

            stats = {}
            for line in lines[2:]:  # Skip header lines
                parts = line.split()
                interface = parts[0].rstrip(':')
                if interface in ['eth0', 'ens3', 'ens18']:  # Common VPS interface names
                    stats[interface] = {
                        'rx_bytes': int(parts[1]),
                        'tx_bytes': int(parts[9])
                    }
            return stats
        except Exception as e:
            return {'error': str(e)}

    def collect_docker_metrics(self):
        """Collect Docker container metrics"""
        try:
            # Get container stats
            result = subprocess.run([
                'docker', 'stats', '--no-stream', '--format',
                'json'
            ], capture_output=True, text=True)

            containers = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    container_data = json.loads(line)
                    containers.append({
                        'name': container_data['Name'],
                        'cpu_percent': container_data['CPUPerc'].replace('%', ''),
                        'memory_usage': container_data['MemUsage'],
                        'memory_percent': container_data['MemPerc'].replace('%', ''),
                        'net_io': container_data['NetIO'],
                        'block_io': container_data['BlockIO'],
                        'pids': container_data['PIDs']
                    })

            return {
                'timestamp': datetime.now().isoformat(),
                'containers': containers,
                'total_containers': len(containers)
            }
        except Exception as e:
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

    def check_customer_health(self):
        """Check health of customer applications"""
        customers = [
            'lhgi.minipass.me',
            'kdc.minipass.me',
            'heq.minipass.me',
            'minipass.me'
        ]

        health_checks = []

        for customer in customers:
            try:
                import requests
                start_time = time.time()
                response = requests.get(f'https://{customer}', timeout=10, allow_redirects=True)
                response_time = time.time() - start_time

                health_checks.append({
                    'customer': customer,
                    'status_code': response.status_code,
                    'response_time': round(response_time, 3),
                    'healthy': response.status_code == 200,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                health_checks.append({
                    'customer': customer,
                    'status_code': 0,
                    'response_time': 10.0,
                    'healthy': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })

        return {
            'timestamp': datetime.now().isoformat(),
            'health_checks': health_checks,
            'healthy_count': len([h for h in health_checks if h['healthy']]),
            'total_customers': len(health_checks)
        }

    def check_disk_usage_by_customer(self):
        """Check disk usage breakdown by customer"""
        customers = ['lhgi', 'kdc', 'heq', 'testdelancementmf']
        usage = {}

        for customer in customers:
            customer_path = self.base_path / 'deployed' / customer
            if customer_path.exists():
                # Get directory size
                result = subprocess.run(['du', '-sb', str(customer_path)], capture_output=True, text=True)
                if result.returncode == 0:
                    size_bytes = int(result.stdout.split()[0])
                    usage[customer] = {
                        'bytes': size_bytes,
                        'mb': round(size_bytes / (1024**2), 2)
                    }

                    # Check uploads specifically
                    uploads_path = customer_path / 'app' / 'static' / 'uploads'
                    if uploads_path.exists():
                        upload_result = subprocess.run(['du', '-sb', str(uploads_path)], capture_output=True, text=True)
                        if upload_result.returncode == 0:
                            upload_size = int(upload_result.stdout.split()[0])
                            usage[customer]['uploads_bytes'] = upload_size
                            usage[customer]['uploads_mb'] = round(upload_size / (1024**2), 2)

        return {
            'timestamp': datetime.now().isoformat(),
            'customer_usage': usage,
            'total_customer_usage_mb': sum(c.get('mb', 0) for c in usage.values())
        }

    def generate_alert_conditions(self, system_metrics, docker_metrics, health_metrics):
        """Check for alert conditions"""
        alerts = []

        # Memory alerts
        if system_metrics['memory']['usage_percent'] > 85:
            alerts.append({
                'severity': 'HIGH',
                'type': 'MEMORY',
                'message': f"High memory usage: {system_metrics['memory']['usage_percent']:.1f}%",
                'threshold': 85,
                'current_value': system_metrics['memory']['usage_percent']
            })
        elif system_metrics['memory']['usage_percent'] > 75:
            alerts.append({
                'severity': 'MEDIUM',
                'type': 'MEMORY',
                'message': f"Moderate memory usage: {system_metrics['memory']['usage_percent']:.1f}%",
                'threshold': 75,
                'current_value': system_metrics['memory']['usage_percent']
            })

        # Disk alerts
        if system_metrics['disk']['usage_percent'] > 85:
            alerts.append({
                'severity': 'HIGH',
                'type': 'DISK',
                'message': f"High disk usage: {system_metrics['disk']['usage_percent']:.1f}%",
                'threshold': 85,
                'current_value': system_metrics['disk']['usage_percent']
            })

        # CPU load alerts (for 4-core system)
        if system_metrics['cpu']['load_5min'] > 3.5:
            alerts.append({
                'severity': 'HIGH',
                'type': 'CPU',
                'message': f"High CPU load: {system_metrics['cpu']['load_5min']}",
                'threshold': 3.5,
                'current_value': system_metrics['cpu']['load_5min']
            })

        # Customer health alerts
        unhealthy_customers = [h['customer'] for h in health_metrics['health_checks'] if not h['healthy']]
        if unhealthy_customers:
            alerts.append({
                'severity': 'HIGH',
                'type': 'CUSTOMER_HEALTH',
                'message': f"Unhealthy customers: {', '.join(unhealthy_customers)}",
                'affected_customers': unhealthy_customers
            })

        # Slow response time alerts
        slow_customers = [h['customer'] for h in health_metrics['health_checks'] if h['response_time'] > 5.0]
        if slow_customers:
            alerts.append({
                'severity': 'MEDIUM',
                'type': 'PERFORMANCE',
                'message': f"Slow response times: {', '.join(slow_customers)}",
                'affected_customers': slow_customers
            })

        return alerts

    def save_metrics(self, data, filename_prefix):
        """Save metrics to log file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.logs_path / f"{filename_prefix}_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

        return filename

    def cleanup_old_logs(self, days=7):
        """Remove log files older than specified days"""
        cutoff_time = time.time() - (days * 24 * 60 * 60)

        for log_file in self.logs_path.glob('*.json'):
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()

    def run_monitoring_cycle(self):
        """Run complete monitoring cycle"""
        print(f"🔍 Running monitoring cycle at {datetime.now()}")

        # Collect all metrics
        system_metrics = self.collect_system_metrics()
        docker_metrics = self.collect_docker_metrics()
        health_metrics = self.check_customer_health()
        disk_metrics = self.check_disk_usage_by_customer()

        # Generate alerts
        alerts = self.generate_alert_conditions(system_metrics, docker_metrics, health_metrics)

        # Combine all data
        monitoring_data = {
            'timestamp': datetime.now().isoformat(),
            'system': system_metrics,
            'docker': docker_metrics,
            'customer_health': health_metrics,
            'disk_usage': disk_metrics,
            'alerts': alerts
        }

        # Save to file
        log_file = self.save_metrics(monitoring_data, 'monitoring')

        # Print summary
        print(f"📊 System Memory: {system_metrics['memory']['usage_percent']:.1f}%")
        print(f"💽 Disk Usage: {system_metrics['disk']['usage_percent']:.1f}%")
        print(f"🏥 Healthy Customers: {health_metrics['healthy_count']}/{health_metrics['total_customers']}")

        if alerts:
            print(f"🚨 Active Alerts: {len(alerts)}")
            for alert in alerts:
                print(f"   {alert['severity']}: {alert['message']}")
        else:
            print("✅ No active alerts")

        # Cleanup old logs
        self.cleanup_old_logs()

        return monitoring_data

    def generate_dashboard_html(self, monitoring_data):
        """Generate simple HTML dashboard"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Minipass VPS Monitoring Dashboard</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .card {{ background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
                .metric-label {{ color: #7f8c8d; font-size: 14px; }}
                .alert-high {{ color: #e74c3c; background-color: #fdf2f2; padding: 10px; border-radius: 4px; margin: 5px 0; }}
                .alert-medium {{ color: #f39c12; background-color: #fef9f2; padding: 10px; border-radius: 4px; margin: 5px 0; }}
                .healthy {{ color: #27ae60; }}
                .unhealthy {{ color: #e74c3c; }}
                .timestamp {{ color: #95a5a6; font-size: 12px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
                th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f8f9fa; }}
            </style>
            <meta http-equiv="refresh" content="60">
        </head>
        <body>
            <div class="container">
                <h1>Minipass VPS Monitoring Dashboard</h1>
                <p class="timestamp">Last updated: {monitoring_data['timestamp']}</p>

                <div class="card">
                    <h2>System Resources</h2>
                    <div class="metric">
                        <div class="metric-value">{monitoring_data['system']['memory']['usage_percent']:.1f}%</div>
                        <div class="metric-label">Memory Usage</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{monitoring_data['system']['disk']['usage_percent']:.1f}%</div>
                        <div class="metric-label">Disk Usage</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{monitoring_data['system']['cpu']['load_5min']}</div>
                        <div class="metric-label">CPU Load (5min)</div>
                    </div>
                </div>

                <div class="card">
                    <h2>Customer Health</h2>
                    <div class="metric">
                        <div class="metric-value {'healthy' if monitoring_data['customer_health']['healthy_count'] == monitoring_data['customer_health']['total_customers'] else 'unhealthy'}">{monitoring_data['customer_health']['healthy_count']}/{monitoring_data['customer_health']['total_customers']}</div>
                        <div class="metric-label">Healthy Customers</div>
                    </div>

                    <table>
                        <tr><th>Customer</th><th>Status</th><th>Response Time</th></tr>
        """

        for health in monitoring_data['customer_health']['health_checks']:
            status_class = 'healthy' if health['healthy'] else 'unhealthy'
            status_text = '✅ Healthy' if health['healthy'] else '❌ Unhealthy'
            html_content += f"""
                        <tr>
                            <td>{health['customer']}</td>
                            <td class="{status_class}">{status_text}</td>
                            <td>{health['response_time']:.3f}s</td>
                        </tr>
            """

        html_content += """
                    </table>
                </div>
        """

        # Alerts section
        if monitoring_data['alerts']:
            html_content += """
                <div class="card">
                    <h2>Active Alerts</h2>
            """
            for alert in monitoring_data['alerts']:
                alert_class = 'alert-high' if alert['severity'] == 'HIGH' else 'alert-medium'
                html_content += f'<div class="{alert_class}"><strong>{alert["severity"]}:</strong> {alert["message"]}</div>'

            html_content += "</div>"

        html_content += """
            </div>
        </body>
        </html>
        """

        # Save dashboard
        dashboard_file = self.base_path / 'monitoring_dashboard.html'
        with open(dashboard_file, 'w') as f:
            f.write(html_content)

        return dashboard_file

    def setup_monitoring_service(self):
        """Set up monitoring as a service"""
        service_script = f"""#!/bin/bash
cd {self.base_path}
python3 monitoring_setup.py --run-cycle
"""

        script_path = self.base_path / 'run_monitoring.sh'
        with open(script_path, 'w') as f:
            f.write(service_script)
        os.chmod(script_path, 0o755)

        print(f"✅ Monitoring service script created: {script_path}")
        print("To set up automated monitoring, add this to your crontab:")
        print(f"*/5 * * * * {script_path} >> {self.base_path}/monitoring.log 2>&1")

def main():
    import argparse

    parser = argparse.ArgumentParser(description='VPS Monitoring Setup')
    parser.add_argument('--run-cycle', action='store_true', help='Run single monitoring cycle')
    parser.add_argument('--setup-service', action='store_true', help='Setup monitoring service')
    parser.add_argument('--daemon', action='store_true', help='Run in daemon mode')

    args = parser.parse_args()

    monitor = VPSMonitor()

    if args.setup_service:
        monitor.setup_monitoring_service()
    elif args.run_cycle:
        monitoring_data = monitor.run_monitoring_cycle()
        dashboard_file = monitor.generate_dashboard_html(monitoring_data)
        print(f"📊 Dashboard generated: {dashboard_file}")
    elif args.daemon:
        print("🔄 Starting monitoring daemon (runs every 5 minutes)...")
        while True:
            try:
                monitoring_data = monitor.run_monitoring_cycle()
                monitor.generate_dashboard_html(monitoring_data)
                time.sleep(300)  # 5 minutes
            except KeyboardInterrupt:
                print("\n👋 Monitoring daemon stopped")
                break
            except Exception as e:
                print(f"❌ Error in monitoring cycle: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    else:
        # Interactive mode - run once and show results
        print("🚀 Running VPS monitoring analysis...")
        monitoring_data = monitor.run_monitoring_cycle()
        dashboard_file = monitor.generate_dashboard_html(monitoring_data)
        print(f"\n📊 Monitoring dashboard created: {dashboard_file}")
        print("💡 Use --daemon to run continuously, --setup-service to configure automation")

if __name__ == '__main__':
    main()
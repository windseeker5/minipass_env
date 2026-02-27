#!/usr/bin/env python3
"""
VPS Resource Monitoring and Capacity Analysis Script
Generates comprehensive resource usage reports and scaling projections
"""

import subprocess
import json
import datetime
import os
import sys
from pathlib import Path

class VPSResourceMonitor:
    def __init__(self):
        self.timestamp = datetime.datetime.now().isoformat()
        self.report = {
            'timestamp': self.timestamp,
            'system_info': {},
            'containers': {},
            'resource_analysis': {},
            'scaling_analysis': {},
            'recommendations': []
        }

    def run_command(self, cmd, shell=True):
        """Execute shell command and return output"""
        try:
            result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception as e:
            print(f"Error running command '{cmd}': {e}")
            return None

    def get_system_info(self):
        """Collect system resource information"""
        print("📊 Collecting system information...")

        # Memory info
        mem_info = self.run_command("free -b | grep 'Mem:'").split()
        total_mem = int(mem_info[1])
        used_mem = int(mem_info[2])
        free_mem = int(mem_info[3])
        available_mem = int(mem_info[6])

        # CPU info
        cpu_count = int(self.run_command("nproc"))
        cpu_model = self.run_command("lscpu | grep 'Model name:' | cut -d: -f2").strip()

        # Disk info
        disk_info = self.run_command("df -B1 / | tail -1").split()
        disk_total = int(disk_info[1])
        disk_used = int(disk_info[2])
        disk_available = int(disk_info[3])

        # Load average
        load_avg = self.run_command("uptime | awk -F'load average:' '{print $2}'").strip()

        self.report['system_info'] = {
            'memory': {
                'total_bytes': total_mem,
                'used_bytes': used_mem,
                'free_bytes': free_mem,
                'available_bytes': available_mem,
                'usage_percentage': round((used_mem / total_mem) * 100, 2),
                'total_gb': round(total_mem / (1024**3), 2),
                'used_gb': round(used_mem / (1024**3), 2),
                'available_gb': round(available_mem / (1024**3), 2)
            },
            'cpu': {
                'count': cpu_count,
                'model': cpu_model,
                'load_average': load_avg
            },
            'disk': {
                'total_bytes': disk_total,
                'used_bytes': disk_used,
                'available_bytes': disk_available,
                'usage_percentage': round((disk_used / disk_total) * 100, 2),
                'total_gb': round(disk_total / (1024**3), 2),
                'used_gb': round(disk_used / (1024**3), 2),
                'available_gb': round(disk_available / (1024**3), 2)
            }
        }

    def get_container_stats(self):
        """Collect Docker container resource usage"""
        print("🐳 Analyzing container resource usage...")

        # Get container stats
        stats_output = self.run_command(
            'docker stats --no-stream --format "{{.Container}}|{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}|{{.NetIO}}|{{.BlockIO}}"'
        )

        if not stats_output:
            return

        containers = {}
        total_container_memory = 0

        for line in stats_output.split('\n'):
            parts = line.split('|')
            if len(parts) != 6:
                continue

            container_id, name, cpu_perc, mem_usage, net_io, block_io = parts

            # Parse memory usage (format: "263.1MiB / 7.57GiB")
            mem_parts = mem_usage.split(' / ')
            if len(mem_parts) == 2:
                used_mem_str = mem_parts[0].strip()

                # Convert to bytes
                if 'MiB' in used_mem_str:
                    used_mem_mb = float(used_mem_str.replace('MiB', ''))
                    used_mem_bytes = int(used_mem_mb * 1024 * 1024)
                elif 'GiB' in used_mem_str:
                    used_mem_gb = float(used_mem_str.replace('GiB', ''))
                    used_mem_bytes = int(used_mem_gb * 1024 * 1024 * 1024)
                else:
                    used_mem_bytes = 0

                total_container_memory += used_mem_bytes

                containers[name] = {
                    'container_id': container_id,
                    'cpu_percentage': cpu_perc,
                    'memory_usage_bytes': used_mem_bytes,
                    'memory_usage_mb': round(used_mem_bytes / (1024**2), 2),
                    'network_io': net_io,
                    'block_io': block_io
                }

        # Get customer upload sizes
        upload_sizes = {}
        deployed_path = Path('/home/kdresdell/minipass_env/deployed')
        if deployed_path.exists():
            for customer_dir in deployed_path.iterdir():
                if customer_dir.is_dir():
                    uploads_path = customer_dir / 'app' / 'static' / 'uploads'
                    if uploads_path.exists():
                        size_output = self.run_command(f"du -sb {uploads_path}")
                        if size_output:
                            size_bytes = int(size_output.split()[0])
                            upload_sizes[customer_dir.name] = {
                                'bytes': size_bytes,
                                'mb': round(size_bytes / (1024**2), 2)
                            }

        self.report['containers'] = {
            'individual_stats': containers,
            'total_container_memory_bytes': total_container_memory,
            'total_container_memory_mb': round(total_container_memory / (1024**2), 2),
            'upload_sizes': upload_sizes,
            'container_count': len(containers)
        }

    def analyze_customer_containers(self):
        """Analyze customer-specific containers"""
        print("👥 Analyzing customer containers...")

        customer_containers = {}
        customer_prefixes = ['minipass_', 'lhgi', 'kdc', 'heq', 'testdelancementmf']

        for container_name, stats in self.report['containers']['individual_stats'].items():
            is_customer = any(container_name.startswith(prefix) or prefix in container_name
                            for prefix in customer_prefixes)

            if is_customer:
                # Extract customer name
                if container_name.startswith('minipass_'):
                    customer_name = container_name.replace('minipass_', '')
                else:
                    customer_name = container_name

                # Get upload size if available
                upload_size = self.report['containers']['upload_sizes'].get(customer_name, {'bytes': 0, 'mb': 0})

                customer_containers[customer_name] = {
                    'container_name': container_name,
                    'memory_mb': stats['memory_usage_mb'],
                    'cpu_percentage': stats['cpu_percentage'],
                    'upload_size_mb': upload_size['mb'],
                    'network_io': stats['network_io'],
                    'block_io': stats['block_io']
                }

        # Calculate averages
        if customer_containers:
            avg_memory = sum(c['memory_mb'] for c in customer_containers.values()) / len(customer_containers)
            total_customer_memory = sum(c['memory_mb'] for c in customer_containers.values())

            self.report['resource_analysis']['customer_analysis'] = {
                'customer_count': len(customer_containers),
                'customers': customer_containers,
                'average_memory_per_customer_mb': round(avg_memory, 2),
                'total_customer_memory_mb': round(total_customer_memory, 2)
            }

    def calculate_scaling_capacity(self):
        """Calculate scaling capacity based on current usage"""
        print("📈 Calculating scaling capacity...")

        system_mem = self.report['system_info']['memory']
        customer_analysis = self.report['resource_analysis'].get('customer_analysis', {})

        if not customer_analysis:
            return

        avg_customer_memory = customer_analysis['average_memory_per_customer_mb']
        current_customers = customer_analysis['customer_count']

        # Infrastructure overhead (non-customer containers)
        total_container_memory = self.report['containers']['total_container_memory_mb']
        customer_memory = customer_analysis['total_customer_memory_mb']
        infrastructure_memory = total_container_memory - customer_memory

        # Available memory for new customers
        available_memory_mb = system_mem['available_bytes'] / (1024**2)

        # Conservative estimate (leave 1GB buffer)
        conservative_buffer_mb = 1024
        conservative_available = available_memory_mb - conservative_buffer_mb
        conservative_capacity = int(conservative_available / avg_customer_memory) if avg_customer_memory > 0 else 0

        # Aggressive estimate (leave 512MB buffer)
        aggressive_buffer_mb = 512
        aggressive_available = available_memory_mb - aggressive_buffer_mb
        aggressive_capacity = int(aggressive_available / avg_customer_memory) if avg_customer_memory > 0 else 0

        # Total capacity
        total_conservative = current_customers + conservative_capacity
        total_aggressive = current_customers + aggressive_capacity

        self.report['scaling_analysis'] = {
            'current_customers': current_customers,
            'avg_memory_per_customer_mb': avg_customer_memory,
            'infrastructure_memory_mb': round(infrastructure_memory, 2),
            'available_memory_mb': round(available_memory_mb, 2),
            'capacity_estimates': {
                'conservative': {
                    'buffer_mb': conservative_buffer_mb,
                    'additional_customers': conservative_capacity,
                    'total_capacity': total_conservative
                },
                'aggressive': {
                    'buffer_mb': aggressive_buffer_mb,
                    'additional_customers': aggressive_capacity,
                    'total_capacity': total_aggressive
                }
            },
            'memory_at_50_customers': {
                'customer_memory_mb': 50 * avg_customer_memory,
                'total_projected_mb': infrastructure_memory + (50 * avg_customer_memory),
                'percentage_of_system': round(((infrastructure_memory + (50 * avg_customer_memory)) / (system_mem['total_bytes'] / (1024**2))) * 100, 2)
            }
        }

    def generate_recommendations(self):
        """Generate optimization recommendations"""
        print("💡 Generating recommendations...")

        recommendations = []

        # Memory usage recommendations
        mem_usage = self.report['system_info']['memory']['usage_percentage']
        if mem_usage > 80:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Memory',
                'issue': f'High memory usage at {mem_usage}%',
                'recommendation': 'Consider upgrading RAM or optimizing container memory usage'
            })
        elif mem_usage > 60:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Memory',
                'issue': f'Moderate memory usage at {mem_usage}%',
                'recommendation': 'Monitor memory growth and plan for optimization'
            })

        # Disk usage recommendations
        disk_usage = self.report['system_info']['disk']['usage_percentage']
        if disk_usage > 80:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Disk',
                'issue': f'High disk usage at {disk_usage}%',
                'recommendation': 'Clean up old files, implement log rotation, or expand disk space'
            })

        # Customer-specific recommendations
        if 'customer_analysis' in self.report['resource_analysis']:
            customers = self.report['resource_analysis']['customer_analysis']['customers']
            for customer_name, customer_data in customers.items():
                if customer_data['upload_size_mb'] > 20:
                    recommendations.append({
                        'priority': 'HIGH',
                        'category': 'Performance',
                        'issue': f'Customer {customer_name} has large uploads ({customer_data["upload_size_mb"]}MB)',
                        'recommendation': 'Implement image compression and CDN caching for this customer'
                    })

        # Scaling recommendations
        if 'scaling_analysis' in self.report:
            conservative_capacity = self.report['scaling_analysis']['capacity_estimates']['conservative']['total_capacity']
            if conservative_capacity < 30:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Scaling',
                    'issue': f'Limited scaling capacity ({conservative_capacity} customers max)',
                    'recommendation': 'Plan RAM upgrade or architecture optimization before reaching 25 customers'
                })

        # Performance optimization recommendations
        recommendations.extend([
            {
                'priority': 'HIGH',
                'category': 'Performance',
                'issue': 'No caching layer detected',
                'recommendation': 'Implement nginx proxy caching for static assets and API responses'
            },
            {
                'priority': 'MEDIUM',
                'category': 'Architecture',
                'issue': 'Container-per-customer model has high memory overhead',
                'recommendation': 'Evaluate shared application architecture for better resource utilization'
            },
            {
                'priority': 'LOW',
                'category': 'Maintenance',
                'issue': 'Bloomcap container uses unnecessary resources',
                'recommendation': 'Remove bloomcap container or migrate to static file hosting'
            }
        ])

        self.report['recommendations'] = recommendations

    def save_report(self, filename=None):
        """Save the complete report to files"""
        if not filename:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'vps_resource_report_{timestamp}'

        # Save JSON report
        json_file = f'{filename}.json'
        with open(json_file, 'w') as f:
            json.dump(self.report, f, indent=2)

        # Save human-readable report
        txt_file = f'{filename}.txt'
        with open(txt_file, 'w') as f:
            f.write(self.generate_text_report())

        print(f"📄 Reports saved:")
        print(f"   JSON: {json_file}")
        print(f"   Text: {txt_file}")

        return json_file, txt_file

    def generate_text_report(self):
        """Generate human-readable text report"""
        report = []
        report.append("=" * 80)
        report.append("VPS RESOURCE ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {self.timestamp}")
        report.append("")

        # System Information
        report.append("SYSTEM OVERVIEW")
        report.append("-" * 40)
        sys_info = self.report['system_info']
        report.append(f"Memory: {sys_info['memory']['used_gb']:.1f}GB / {sys_info['memory']['total_gb']:.1f}GB ({sys_info['memory']['usage_percentage']:.1f}%)")
        report.append(f"Disk:   {sys_info['disk']['used_gb']:.1f}GB / {sys_info['disk']['total_gb']:.1f}GB ({sys_info['disk']['usage_percentage']:.1f}%)")
        report.append(f"CPU:    {sys_info['cpu']['count']} cores - {sys_info['cpu']['model']}")
        report.append(f"Load:   {sys_info['cpu']['load_average']}")
        report.append("")

        # Container Analysis
        if 'customer_analysis' in self.report['resource_analysis']:
            report.append("CUSTOMER CONTAINER ANALYSIS")
            report.append("-" * 40)
            customer_analysis = self.report['resource_analysis']['customer_analysis']
            report.append(f"Customer Count: {customer_analysis['customer_count']}")
            report.append(f"Average Memory per Customer: {customer_analysis['average_memory_per_customer_mb']:.1f}MB")
            report.append(f"Total Customer Memory: {customer_analysis['total_customer_memory_mb']:.1f}MB")
            report.append("")

            report.append("Individual Customer Stats:")
            for customer, stats in customer_analysis['customers'].items():
                report.append(f"  {customer:20} | {stats['memory_mb']:6.1f}MB | CPU: {stats['cpu_percentage']:>6} | Uploads: {stats['upload_size_mb']:6.1f}MB")
            report.append("")

        # Scaling Analysis
        if 'scaling_analysis' in self.report:
            report.append("SCALING CAPACITY ANALYSIS")
            report.append("-" * 40)
            scaling = self.report['scaling_analysis']
            conservative = scaling['capacity_estimates']['conservative']
            aggressive = scaling['capacity_estimates']['aggressive']

            report.append(f"Current Customers: {scaling['current_customers']}")
            report.append(f"Available Memory: {scaling['available_memory_mb']:.1f}MB")
            report.append("")
            report.append(f"Conservative Estimate (1GB buffer): {conservative['total_capacity']} customers total")
            report.append(f"Aggressive Estimate (512MB buffer): {aggressive['total_capacity']} customers total")
            report.append("")

            mem_50 = scaling['memory_at_50_customers']
            report.append(f"At 50 customers:")
            report.append(f"  Projected Memory Usage: {mem_50['total_projected_mb']:.1f}MB ({mem_50['percentage_of_system']:.1f}% of system)")
            report.append("")

        # Recommendations
        if self.report['recommendations']:
            report.append("RECOMMENDATIONS")
            report.append("-" * 40)
            for rec in self.report['recommendations']:
                report.append(f"[{rec['priority']}] {rec['category']}: {rec['issue']}")
                report.append(f"    → {rec['recommendation']}")
                report.append("")

        return '\n'.join(report)

    def run_analysis(self):
        """Run complete analysis"""
        print("🚀 Starting VPS Resource Analysis...")
        print()

        self.get_system_info()
        self.get_container_stats()
        self.analyze_customer_containers()
        self.calculate_scaling_capacity()
        self.generate_recommendations()

        json_file, txt_file = self.save_report()

        print()
        print("✅ Analysis complete!")
        print()
        print("Key Findings:")

        # Print key metrics
        if 'customer_analysis' in self.report['resource_analysis']:
            customer_analysis = self.report['resource_analysis']['customer_analysis']
            print(f"  • Current customers: {customer_analysis['customer_count']}")
            print(f"  • Average memory per customer: {customer_analysis['average_memory_per_customer_mb']:.1f}MB")

        if 'scaling_analysis' in self.report:
            conservative = self.report['scaling_analysis']['capacity_estimates']['conservative']
            print(f"  • Estimated capacity: {conservative['total_capacity']} customers (conservative)")

        print(f"  • System memory usage: {self.report['system_info']['memory']['usage_percentage']:.1f}%")

        # Print high priority recommendations
        high_priority = [r for r in self.report['recommendations'] if r['priority'] == 'HIGH']
        if high_priority:
            print(f"  • High priority issues: {len(high_priority)}")

        return json_file, txt_file

if __name__ == '__main__':
    monitor = VPSResourceMonitor()
    monitor.run_analysis()
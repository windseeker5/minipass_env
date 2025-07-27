#!/usr/bin/env python3

import os
import sqlite3
import subprocess
import shutil
import sys
import json
import re
from datetime import datetime
from typing import List, Dict, Tuple, Optional

CUSTOMERS_DB = "customers.db"
DEPLOYED_FOLDER = "../deployed"

class MiniPassAppManager:
    def __init__(self):
        self.check_docker_available()
    
    def check_docker_available(self):
        """Check if Docker is available"""
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception("Docker not available")
        except FileNotFoundError:
            raise Exception("Docker command not found")
        except Exception as e:
            raise Exception(f"Docker check failed: {e}")
    
    def run_docker_command(self, cmd: List[str], check=True):
        """Run a docker command and return result"""
        try:
            result = subprocess.run(['docker'] + cmd, capture_output=True, text=True, check=check)
            return result
        except subprocess.CalledProcessError as e:
            if check:
                raise Exception(f"Docker command failed: {e.stderr}")
            return e
        except Exception as e:
            raise Exception(f"Error running docker command: {e}")
        
    def get_customers_from_db(self) -> Dict[str, Dict]:
        """Get all customers from database"""
        customers = {}
        try:
            conn = sqlite3.connect(CUSTOMERS_DB)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT subdomain, email, port, plan, created_at, organization_name, 
                       email_address, email_status
                FROM customers
            """)
            rows = cursor.fetchall()
            conn.close()
            
            for row in rows:
                customers[row['subdomain']] = dict(row)
            
        except sqlite3.Error as e:
            print(f"❌ Database error: {e}")
        except FileNotFoundError:
            print(f"⚠️ Database file {CUSTOMERS_DB} not found")
            
        return customers
    
    def get_minipass_containers(self) -> List[Dict]:
        """Get all containers created by the website controller"""
        containers = []
        
        try:
            # Get all containers with format
            result = self.run_docker_command(['ps', '-a', '--format', 'json'])
            
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                    
                try:
                    container_data = json.loads(line)
                    container_name = container_data.get('Names', '')
                    
                    # Check if container name matches minipass pattern
                    if container_name.startswith("minipass_"):
                        subdomain = container_name.replace("minipass_", "")
                        
                        # Get memory usage
                        memory_usage = self.get_container_memory_usage(container_name)
                        
                        # Get deployed folder size
                        deployed_size = self.get_deployed_folder_size(subdomain)
                        
                        container_info = {
                            'name': container_name,
                            'subdomain': subdomain,
                            'status': container_data.get('State', 'unknown'),
                            'image': container_data.get('Image', 'unknown'),
                            'created': container_data.get('CreatedAt', ''),
                            'ports': container_data.get('Ports', ''),
                            'id': container_data.get('ID', '')[:12],
                            'memory_usage': memory_usage,
                            'deployed_size': deployed_size
                        }
                        containers.append(container_info)
                        
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            print(f"❌ Docker error: {e}")
            
        return containers
    
    def get_container_memory_usage(self, container_name: str) -> str:
        """Get memory usage for a specific container"""
        try:
            # Use docker stats to get memory usage
            result = self.run_docker_command(['stats', '--no-stream', '--format', 'json', container_name], check=False)
            
            if result.returncode == 0 and result.stdout.strip():
                stats_data = json.loads(result.stdout.strip())
                memory_usage = stats_data.get('MemUsage', 'N/A')
                return memory_usage
            else:
                return 'N/A'
                
        except Exception:
            return 'N/A'
    
    def get_deployed_folder_size(self, subdomain: str) -> int:
        """Get the size of the deployed folder for a subdomain"""
        folder_path = os.path.join(DEPLOYED_FOLDER, subdomain)
        return self.get_folder_size(folder_path)
    
    def get_minipass_images(self) -> List[Dict]:
        """Get all images created by the website controller"""
        images = []
        
        try:
            # Get all images with format
            result = self.run_docker_command(['images', '--format', 'json'])
            
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                    
                try:
                    image_data = json.loads(line)
                    repository = image_data.get('Repository', '')
                    tag = image_data.get('Tag', '')
                    full_tag = f"{repository}:{tag}" if tag != '<none>' else repository
                    
                    if repository.endswith("-flask-app"):
                        subdomain = repository.replace("-flask-app", "")
                        image_info = {
                            'tag': full_tag,
                            'subdomain': subdomain,
                            'id': image_data.get('ID', '')[:12],
                            'size': image_data.get('Size', '0B'),
                            'created': image_data.get('CreatedAt', '')
                        }
                        images.append(image_info)
                        
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            print(f"❌ Docker error getting images: {e}")
            
        return images
    
    def format_size(self, size_bytes: int) -> str:
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def format_datetime(self, datetime_str: str) -> str:
        """Format datetime string to readable format"""
        try:
            if 'T' in datetime_str:
                dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d %H:%M')
            return datetime_str[:16] if len(datetime_str) > 16 else datetime_str
        except:
            return datetime_str[:16] if datetime_str else 'unknown'
    
    def list_all_minipass_apps(self):
        """List all MiniPass apps with container and DB status"""
        print("\n🔍 Scanning for MiniPass applications...")
        
        customers = self.get_customers_from_db()
        containers = self.get_minipass_containers()
        images = self.get_minipass_images()
        
        # Create mapping of subdomains to their resources
        all_subdomains = set()
        all_subdomains.update(customers.keys())
        all_subdomains.update([c['subdomain'] for c in containers])
        all_subdomains.update([i['subdomain'] for i in images])
        
        if not all_subdomains:
            print("ℹ️ No MiniPass applications found.")
            return []
        
        print(f"\n📋 Found {len(all_subdomains)} MiniPass applications:\n")
        print(f"{'#':<3} {'Subdomain':<12} {'Status':<10} {'Memory':<12} {'Deployed':<10} {'DB Entry':<8} {'Email':<20}")
        print("=" * 80)
        
        app_list = []
        for idx, subdomain in enumerate(sorted(all_subdomains), 1):
            # Check container status
            container = next((c for c in containers if c['subdomain'] == subdomain), None)
            container_status = container['status'] if container else 'none'
            
            # Get memory usage
            memory_usage = container['memory_usage'] if container else 'N/A'
            
            # Get deployed folder size
            deployed_size = self.format_size(self.get_deployed_folder_size(subdomain))
            
            # Check image status  
            image = next((i for i in images if i['subdomain'] == subdomain), None)
            
            # Check DB status
            db_entry = customers.get(subdomain)
            db_status = '✅ Yes' if db_entry else '❌ No'
            email = db_entry['email'][:18] + '..' if db_entry and len(db_entry['email']) > 20 else (db_entry['email'] if db_entry else '-')
            
            print(f"{idx:<3} {subdomain:<12} {container_status:<10} {memory_usage:<12} {deployed_size:<10} {db_status:<8} {email:<20}")
            
            app_list.append({
                'subdomain': subdomain,
                'container': container,
                'image': image,
                'db_entry': db_entry
            })
        
        return app_list
    
    def comprehensive_app_cleanup(self, subdomain: str) -> bool:
        """Perform comprehensive cleanup of a MiniPass app"""
        print(f"\n🧹 Starting comprehensive cleanup for '{subdomain}'...")
        
        success = True
        space_freed = 0
        
        # 1. Remove Docker container
        try:
            container_name = f"minipass_{subdomain}"
            
            # Check if container exists
            result = self.run_docker_command(['ps', '-a', '--filter', f'name={container_name}', '--format', '{{.Names}}'], check=False)
            
            if container_name in result.stdout:
                print(f"🛑 Stopping and removing container '{container_name}'...")
                
                # Stop container if running
                self.run_docker_command(['stop', container_name], check=False)
                print("   ✅ Container stopped")
                
                # Remove container with volumes
                self.run_docker_command(['rm', '-f', '-v', container_name], check=False)
                print("   ✅ Container removed")
            else:
                print(f"   ℹ️ Container '{container_name}' not found")
                
        except Exception as e:
            print(f"   ❌ Error removing container: {e}")
            success = False
        
        # 2. Remove Docker image
        try:
            image_name = f"{subdomain}-flask-app"
            
            # Check if image exists
            result = self.run_docker_command(['images', image_name, '--format', '{{.Repository}}'], check=False)
            
            if image_name in result.stdout:
                print(f"🗑️ Removing image '{image_name}'...")
                
                # Remove image with force
                self.run_docker_command(['rmi', '-f', image_name], check=False)
                print("   ✅ Image removed")
            else:
                print(f"   ℹ️ Image '{image_name}' not found")
                
        except Exception as e:
            print(f"   ❌ Error removing image: {e}")
            success = False
        
        # 3. Remove ALL deployed files and folders
        try:
            folder_path = os.path.join(DEPLOYED_FOLDER, subdomain)
            if os.path.exists(folder_path):
                folder_size = self.get_folder_size(folder_path)
                print(f"📁 Removing ALL deployed files and folders for '{subdomain}' ({self.format_size(folder_size)})...")
                
                # Force remove with all permissions
                self.force_remove_folder(folder_path)
                space_freed += folder_size
                print("   ✅ All deployed files and folders removed")
            else:
                print(f"   ℹ️ Deployed folder '{folder_path}' not found")
                
            # Also check for any other files that might reference this subdomain
            self.cleanup_subdomain_references(subdomain)
            
        except Exception as e:
            print(f"   ❌ Error removing deployed files: {e}")
            success = False
        
        # 4. Remove from database
        try:
            conn = sqlite3.connect(CUSTOMERS_DB)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM customers WHERE subdomain = ?", (subdomain,))
            if cursor.fetchone()[0] > 0:
                print(f"🗄️ Removing database entry for '{subdomain}'...")
                cursor.execute("DELETE FROM customers WHERE subdomain = ?", (subdomain,))
                conn.commit()
                print("   ✅ Database entry removed")
            else:
                print(f"   ℹ️ No database entry found for '{subdomain}'")
            conn.close()
        except sqlite3.Error as e:
            print(f"   ❌ Database error: {e}")
            success = False
        
        # 5. Clean up dangling images
        try:
            print("🧽 Cleaning up dangling images...")
            result = self.run_docker_command(['image', 'prune', '-f'], check=False)
            if result.returncode == 0:
                print("   ✅ Dangling images cleaned")
            else:
                print("   ℹ️ No dangling images found")
        except Exception as e:
            print(f"   ⚠️ Warning cleaning dangling images: {e}")
        
        print(f"\n{'✅ Cleanup completed successfully!' if success else '⚠️ Cleanup completed with warnings'}")
        if space_freed > 0:
            print(f"💾 Space freed: {self.format_size(space_freed)}")
        
        return success
    
    def get_folder_size(self, folder_path: str) -> int:
        """Calculate total size of a folder"""
        total = 0
        try:
            for dirpath, dirnames, filenames in os.walk(folder_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total += os.path.getsize(filepath)
        except:
            pass
        return total
    
    def force_remove_folder(self, folder_path: str):
        """Force remove folder with all permissions"""
        try:
            # First try normal removal
            shutil.rmtree(folder_path)
        except PermissionError:
            # If permission error, try with chmod
            try:
                import stat
                for root, dirs, files in os.walk(folder_path):
                    for d in dirs:
                        os.chmod(os.path.join(root, d), stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                    for f in files:
                        os.chmod(os.path.join(root, f), stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                shutil.rmtree(folder_path)
            except:
                # Last resort: use system rm command
                subprocess.run(['rm', '-rf', folder_path], check=False)
        except Exception:
            # Last resort: use system rm command
            subprocess.run(['rm', '-rf', folder_path], check=False)
    
    def cleanup_subdomain_references(self, subdomain: str):
        """Clean up any other references to the subdomain"""
        try:
            # Check for any backup files or temp files that might contain the subdomain
            deployed_base = os.path.dirname(os.path.join(DEPLOYED_FOLDER, subdomain))
            
            if os.path.exists(deployed_base):
                for item in os.listdir(deployed_base):
                    if subdomain in item and item != subdomain:
                        item_path = os.path.join(deployed_base, item)
                        if os.path.isfile(item_path) or os.path.isdir(item_path):
                            print(f"   🧹 Removing related file/folder: {item}")
                            if os.path.isdir(item_path):
                                self.force_remove_folder(item_path)
                            else:
                                os.remove(item_path)
        except Exception as e:
            print(f"   ⚠️ Warning cleaning subdomain references: {e}")
    
    def cleanup_orphaned_containers(self):
        """Remove containers that don't have database entries"""
        print("\n🔍 Scanning for orphaned containers...")
        
        customers = self.get_customers_from_db()
        containers = self.get_minipass_containers()
        
        orphaned = [c for c in containers if c['subdomain'] not in customers]
        
        if not orphaned:
            print("✅ No orphaned containers found.")
            return
        
        print(f"\n⚠️ Found {len(orphaned)} orphaned containers:")
        for container in orphaned:
            print(f"  - {container['name']} ({container['status']})")
        
        confirm = input("\n❗ Remove all orphaned containers? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ Aborted.")
            return
        
        for container in orphaned:
            self.comprehensive_app_cleanup(container['subdomain'])
    
    def cleanup_orphaned_db_entries(self):
        """Remove database entries that don't have containers"""
        print("\n🔍 Scanning for orphaned database entries...")
        
        customers = self.get_customers_from_db()
        containers = self.get_minipass_containers()
        container_subdomains = [c['subdomain'] for c in containers]
        
        orphaned = {k: v for k, v in customers.items() if k not in container_subdomains}
        
        if not orphaned:
            print("✅ No orphaned database entries found.")
            return
        
        print(f"\n⚠️ Found {len(orphaned)} orphaned database entries:")
        for subdomain, info in orphaned.items():
            print(f"  - {subdomain} ({info['email']})")
        
        confirm = input("\n❗ Remove all orphaned database entries? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ Aborted.")
            return
        
        try:
            conn = sqlite3.connect(CUSTOMERS_DB)
            cursor = conn.cursor()
            for subdomain in orphaned.keys():
                cursor.execute("DELETE FROM customers WHERE subdomain = ?", (subdomain,))
                print(f"🗑️ Removed database entry for '{subdomain}'")
            conn.commit()
            conn.close()
            print(f"✅ Removed {len(orphaned)} orphaned database entries.")
        except sqlite3.Error as e:
            print(f"❌ Database error: {e}")
    
    def docker_system_cleanup(self):
        """Perform Docker system cleanup to free maximum space"""
        print("\n🧹 Performing Docker system cleanup...")
        
        try:
            # Get current usage
            print("📊 Current Docker usage:")
            
            # Get system df info
            result = self.run_docker_command(['system', 'df'], check=False)
            if result.returncode == 0:
                print(result.stdout)
            
            confirm = input("\n❗ Perform system cleanup (removes unused images, containers, networks, volumes)? (y/N): ").strip().lower()
            if confirm != 'y':
                print("❌ Aborted.")
                return
            
            # Prune containers
            print("🧹 Removing unused containers...")
            result = self.run_docker_command(['container', 'prune', '-f'], check=False)
            if result.returncode == 0:
                print("   ✅ Unused containers removed")
            
            # Prune images
            print("🧹 Removing unused images...")
            result = self.run_docker_command(['image', 'prune', '-a', '-f'], check=False)
            if result.returncode == 0:
                print("   ✅ Unused images removed")
            
            # Prune volumes
            print("🧹 Removing unused volumes...")
            result = self.run_docker_command(['volume', 'prune', '-f'], check=False)
            if result.returncode == 0:
                print("   ✅ Unused volumes removed")
            
            # Prune networks
            print("🧹 Removing unused networks...")
            result = self.run_docker_command(['network', 'prune', '-f'], check=False)
            if result.returncode == 0:
                print("   ✅ Unused networks removed")
            
            # Show final usage
            print("\n📊 Final Docker usage:")
            result = self.run_docker_command(['system', 'df'], check=False)
            if result.returncode == 0:
                print(result.stdout)
            
            print("✅ Docker system cleanup completed!")
            
        except Exception as e:
            print(f"❌ Docker cleanup error: {e}")
    
    def show_menu(self):
        """Display the main menu"""
        print("\n" + "="*60)
        print("   🚀 MINIPASS APP MANAGEMENT TOOL")
        print("="*60)
        print("1. 📋 List all MiniPass applications")
        print("2. 🗑️ Delete specific MiniPass application")
        print("3. 🧹 Cleanup orphaned containers")
        print("4. 🗄️ Cleanup orphaned database entries")
        print("5. 🧽 Docker system cleanup")
        print("6. ❌ Exit")
        print("="*60)
    
    def run(self):
        """Main program loop"""
        while True:
            self.show_menu()
            
            try:
                choice = input("\nChoose an option (1-6): ").strip()
                
                if choice == '1':
                    self.list_all_minipass_apps()
                
                elif choice == '2':
                    apps = self.list_all_minipass_apps()
                    if not apps:
                        continue
                    
                    try:
                        app_choice = int(input(f"\nEnter the number of the app to delete (1-{len(apps)}): "))
                        if 1 <= app_choice <= len(apps):
                            selected_app = apps[app_choice - 1]
                            subdomain = selected_app['subdomain']
                            
                            print(f"\n⚠️ You are about to delete '{subdomain}':")
                            if selected_app['container']:
                                print(f"  - Container: {selected_app['container']['name']} ({selected_app['container']['status']})")
                            if selected_app['image']:
                                print(f"  - Image: {selected_app['image']['tag']}")
                            if selected_app['db_entry']:
                                print(f"  - Database entry: {selected_app['db_entry']['email']}")
                            
                            confirm = input(f"\n❗ Type 'DELETE {subdomain}' to confirm: ")
                            if confirm == f"DELETE {subdomain}":
                                self.comprehensive_app_cleanup(subdomain)
                            else:
                                print("❌ Aborted.")
                        else:
                            print("❌ Invalid choice.")
                    except ValueError:
                        print("❌ Invalid number.")
                
                elif choice == '3':
                    self.cleanup_orphaned_containers()
                
                elif choice == '4':
                    self.cleanup_orphaned_db_entries()
                
                elif choice == '5':
                    self.docker_system_cleanup()
                
                elif choice == '6':
                    print("👋 Goodbye!")
                    break
                
                else:
                    print("❌ Invalid choice. Please enter 1-6.")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")

def main():
    """Main entry point"""
    try:
        manager = MiniPassAppManager()
        manager.run()
    except Exception as e:
        if "Docker" in str(e):
            print("❌ Error: Could not connect to Docker. Is Docker running?")
        else:
            print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
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
import pyfiglet





CUSTOMERS_DB = "MinipassWebSite/customers.db"
DEPLOYED_FOLDER = "deployed"

# Mail server constants (from mail_manager.py)
MAILSERVER = "mailserver"
DOMAIN = "minipass.me"
LOCAL_SIEVE_BASE = "./config/user-patches"
FORWARD_DIR = "./config/user-patches"




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
                
                # Force remove with all permissions using enhanced removal
                removal_success = self.force_remove_folder(folder_path)
                if removal_success:
                    space_freed += folder_size
                    print("   ✅ All deployed files and folders removed")
                else:
                    print("   ❌ Failed to remove all deployed files - some files may remain")
                    success = False
            else:
                print(f"   ℹ️ Deployed folder '{folder_path}' not found")
                
            # Also check for any other files that might reference this subdomain
            self.cleanup_subdomain_references(subdomain)
            
        except Exception as e:
            print(f"   ❌ Error removing deployed files: {e}")
            success = False
        
        # 4. Get email address before database deletion
        email_address = None
        try:
            conn = sqlite3.connect(CUSTOMERS_DB)
            cursor = conn.cursor()
            cursor.execute("SELECT email_address FROM customers WHERE subdomain = ?", (subdomain,))
            result = cursor.fetchone()
            if result:
                email_address = result[0]
            conn.close()
        except sqlite3.Error as e:
            print(f"   ⚠️ Warning getting email address: {e}")
        
        # 5. Delete associated email account
        if email_address:
            email_success = self.delete_associated_email(email_address)
            if not email_success:
                success = False
        else:
            print("   ℹ️ No email address associated with this app")
        
        # 6. Remove from database
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
        
        # 7. Clean up dangling images
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
        """
        Enhanced force removal with multiple escalation strategies
        Handles Python bytecode files, Docker container ownership, and special attributes
        """
        import stat
        import logging
        import pwd
        import grp
        from pathlib import Path
        
        if not os.path.exists(folder_path):
            print(f"   ℹ️ Path '{folder_path}' does not exist")
            return True
            
        print(f"   🗑️ Attempting to remove: {folder_path}")
        
        # Strategy 1: Standard removal
        print("   🔧 Strategy 1: Standard removal...", end=" ")
        if self._try_standard_removal(folder_path):
            print("✅ Success!")
            return True
        print("❌ Failed")
            
        # Strategy 2: Permission-based removal with detailed analysis
        print("   🔧 Strategy 2: Permission fixing...", end=" ")
        if self._try_permission_based_removal(folder_path):
            print("✅ Success!")
            return True
        print("❌ Failed (permission issues)")
            
        # Strategy 3: Attribute-based removal (handle immutable files)
        print("   🔧 Strategy 3: Attribute removal...", end=" ")
        if self._try_attribute_based_removal(folder_path):
            print("✅ Success!")
            return True
        print("❌ Failed (attribute issues)")
            
        # Strategy 4: Container-based removal (for Docker-created files)
        print("   🔧 Strategy 4: Container-based removal...", end=" ")
        if self._try_container_based_removal(folder_path):
            print("✅ Success!")
            return True
        print("❌ Failed (container issues)")
            
        # Strategy 5: Sudo-based removal (if available)
        print("   🔧 Strategy 5: Sudo-based removal...", end=" ")
        if self._try_sudo_removal(folder_path):
            print("✅ Success!")
            return True
        print("❌ Failed (no sudo access)")
            
        # Strategy 6: Process-based cleanup (handle busy files)
        print("   🔧 Strategy 6: Process-based removal...", end=" ")
        if self._try_process_based_removal(folder_path):
            print("✅ Success!")
            return True
        print("❌ Failed (busy files)")
            
        print(f"   ❌ All 6 removal strategies failed for: {folder_path}")
        return False
    
    def _try_standard_removal(self, folder_path: str) -> bool:
        """Strategy 1: Standard shutil.rmtree removal"""
        try:
            shutil.rmtree(folder_path)
            return True
        except Exception:
            return False
    
    def _try_permission_based_removal(self, folder_path: str) -> bool:
        """Strategy 2: Fix permissions and retry removal"""
        import stat
        import pwd
        import grp
        
        try:
            fixed_count = 0
            error_count = 0
            
            # Walk through all files and directories
            for root, dirs, files in os.walk(folder_path, topdown=False):
                # Process files first
                for filename in files:
                    filepath = os.path.join(root, filename)
                    if not os.path.exists(filepath):
                        continue
                        
                    try:
                        # Try to make file writable and removable
                        new_mode = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH
                        os.chmod(filepath, new_mode)
                        
                        # Try to remove the file immediately
                        os.unlink(filepath)
                        fixed_count += 1
                        
                    except OSError:
                        error_count += 1
                        continue
                
                # Process directories
                for dirname in dirs:
                    dirpath = os.path.join(root, dirname)
                    if not os.path.exists(dirpath):
                        continue
                        
                    try:
                        # Make directory writable and accessible
                        new_mode = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH
                        os.chmod(dirpath, new_mode)
                        
                        # Try to remove empty directory
                        try:
                            os.rmdir(dirpath)
                        except OSError:
                            pass  # Directory not empty, will be handled by parent removal
                            
                    except OSError:
                        error_count += 1
            
            # Try final removal
            shutil.rmtree(folder_path)
            return True
            
        except Exception:
            return False
    
    def _try_attribute_based_removal(self, folder_path: str) -> bool:
        """Strategy 3: Remove special attributes (immutable, append-only) and retry"""
        try:
            # Use chattr to remove immutable and append-only attributes
            result = subprocess.run(['chattr', '-R', '-i', '-a', folder_path], 
                                  capture_output=True, text=True, check=False)
            
            # Try removal after attribute changes
            shutil.rmtree(folder_path)
            return True
            
        except FileNotFoundError:
            return False
        except Exception:
            return False
    
    def _try_container_based_removal(self, folder_path: str) -> bool:
        """Strategy 4: Use Docker container to remove files with different ownership"""
        try:
            # Check if Docker is available
            if not hasattr(self, 'check_docker_available'):
                return False
                
            # Get absolute path
            abs_path = os.path.abspath(folder_path)
            parent_dir = os.path.dirname(abs_path)
            target_dir = os.path.basename(abs_path)
            
            # Use a lightweight container to remove files
            # Mount parent directory and remove the target folder
            result = subprocess.run([
                'docker', 'run', '--rm',
                '-v', f'{parent_dir}:/workspace',
                '--workdir', '/workspace',
                'alpine:latest',
                'rm', '-rf', target_dir
            ], capture_output=True, text=True, check=False)
            
            return result.returncode == 0
                
        except Exception:
            return False
    
    def _try_sudo_removal(self, folder_path: str) -> bool:
        """Strategy 5: Use sudo for removal if available"""
        try:
            # Check if sudo is available and user has privileges
            sudo_check = subprocess.run(['sudo', '-n', 'true'], 
                                      capture_output=True, check=False)
            
            if sudo_check.returncode != 0:
                return False
            
            # Use sudo rm with force
            result = subprocess.run(['sudo', 'rm', '-rf', folder_path], 
                                  capture_output=True, text=True, check=False)
            
            return result.returncode == 0
                
        except Exception:
            return False
    
    def _try_process_based_removal(self, folder_path: str) -> bool:
        """Strategy 6: Handle busy files by finding and killing processes"""
        try:
            # Use lsof to find processes using files in the directory
            result = subprocess.run(['lsof', '+D', folder_path], 
                                  capture_output=True, text=True, check=False)
            
            # If processes are using files, we can't remove them safely
            if result.returncode == 0 and result.stdout.strip():
                return False
            
            # If no processes found, try removal again
            shutil.rmtree(folder_path)
            return True
            
        except FileNotFoundError:
            # Try removal anyway if lsof not available
            try:
                shutil.rmtree(folder_path)
                return True
            except:
                return False
        except Exception:
            return False
    
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
    
    def delete_associated_email(self, email_address: str) -> bool:
        """Delete email user from mail server (based on mail_manager.py hard_delete_user)"""
        if not email_address:
            return True  # Nothing to delete
            
        print(f"📧 Deleting associated email account '{email_address}'...")
        success = True
        
        try:
            # 1. Delete user from mail server
            print("   🗑️ Removing user from mail server...")
            result = subprocess.run([
                "docker", "exec", MAILSERVER,
                "setup", "email", "del", email_address
            ], capture_output=True, text=True, check=False)
            
            if result.returncode != 0:
                print(f"   ⚠️ Warning deleting user from mail server: {result.stderr}")
            else:
                print("   ✅ User removed from mail server")
                
        except Exception as e:
            print(f"   ❌ Error deleting user from mail server: {e}")
            success = False

        try:
            # 2. Remove forward configuration directory
            local_forward_dir = os.path.join(FORWARD_DIR, email_address)
            if os.path.exists(local_forward_dir):
                print("   🧹 Removing forward configuration...")
                shutil.rmtree(local_forward_dir)
                print("   ✅ Forward configuration removed")
            else:
                print("   ℹ️ No forward configuration found")
                
        except Exception as e:
            print(f"   ❌ Error removing forward configuration: {e}")
            success = False

        try:
            # 3. Remove inbox data from container
            local_part = email_address.split("@")[0]
            inbox_path = f"/var/mail/{DOMAIN}/{local_part}"
            print("   📭 Removing inbox data...")
            
            result = subprocess.run([
                "docker", "exec", MAILSERVER,
                "rm", "-rf", inbox_path
            ], capture_output=True, text=True, check=False)
            
            if result.returncode != 0:
                print(f"   ⚠️ Warning removing inbox: {result.stderr}")
            else:
                print("   ✅ Inbox data removed")
                
        except Exception as e:
            print(f"   ❌ Error removing inbox data: {e}")
            success = False
        
        # 4. Validate deletion
        try:
            print("   🔍 Validating email deletion...")
            result = subprocess.run([
                "docker", "exec", MAILSERVER,
                "grep", "-i", email_address,
                "/tmp/docker-mailserver/postfix-accounts.cf"
            ], capture_output=True, text=True, check=False)
            
            if result.stdout.strip():
                print(f"   ⚠️ Warning: Email still exists in postfix-accounts.cf")
                success = False
            else:
                print("   ✅ Email successfully removed from mail server")
                
        except Exception as e:
            print(f"   ⚠️ Could not validate email deletion: {e}")
        
        return success
    
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
    
    def get_build_cache_info(self):
        """Get detailed build cache information"""
        try:
            result = self.run_docker_command(['system', 'df', '-v'], check=False)
            if result.returncode != 0:
                return None, None
                
            lines = result.stdout.strip().split('\n')
            build_cache_section = False
            total_size = 0
            reclaimable_size = 0
            
            for line in lines:
                if 'BUILD CACHE' in line.upper():
                    build_cache_section = True
                    continue
                elif build_cache_section and line.strip() and not line.startswith(' '):
                    # End of build cache section
                    break
                elif build_cache_section and 'Total:' in line:
                    # Parse total line for build cache
                    parts = line.split()
                    if len(parts) >= 4:
                        try:
                            total_size_str = parts[-2]
                            reclaimable_size_str = parts[-1]
                            total_size = self.parse_size_string(total_size_str)
                            reclaimable_size = self.parse_size_string(reclaimable_size_str)
                        except:
                            pass
                    break
                    
            return total_size, reclaimable_size
        except Exception:
            return None, None
    
    def parse_size_string(self, size_str):
        """Parse Docker size string (e.g., '2.989GB') to bytes"""
        try:
            size_str = size_str.upper().replace('B', '')
            multipliers = {'K': 1024, 'M': 1024**2, 'G': 1024**3, 'T': 1024**4}
            
            for suffix, multiplier in multipliers.items():
                if size_str.endswith(suffix):
                    return float(size_str[:-1]) * multiplier
            
            # No suffix, assume bytes
            return float(size_str)
        except:
            return 0

    def docker_system_cleanup(self):
        """Perform comprehensive Docker system cleanup to free maximum space including build cache"""
        print("\n🧹 Performing comprehensive Docker system cleanup...")
        
        try:
            # Get current usage with verbose info
            print("📊 Current Docker usage:")
            result = self.run_docker_command(['system', 'df', '-v'], check=False)
            if result.returncode == 0:
                print(result.stdout)
            
            # Get build cache info before cleanup
            build_cache_before, reclaimable_before = self.get_build_cache_info()
            if build_cache_before is not None:
                print(f"\n💾 Build cache before cleanup: {self.format_size(int(build_cache_before))} total, {self.format_size(int(reclaimable_before))} reclaimable")
            
            # Ask for cleanup type
            print("\nCleanup options:")
            print("1. Standard cleanup (containers, images, volumes, networks)")
            print("2. Comprehensive cleanup (includes build cache)")
            print("3. Build cache only")
            
            cleanup_choice = input("\nChoose cleanup type (1-3) or 'n' to cancel: ").strip().lower()
            
            if cleanup_choice == 'n':
                print("❌ Aborted.")
                return
            elif cleanup_choice not in ['1', '2', '3']:
                print("❌ Invalid choice.")
                return
            
            total_space_freed = 0
            
            if cleanup_choice in ['1', '2']:
                # Standard cleanup operations
                
                # Prune containers
                print("\n🧹 Removing unused containers...")
                result = self.run_docker_command(['container', 'prune', '-f'], check=False)
                if result.returncode == 0:
                    # Extract space freed from output
                    if "Total reclaimed space:" in result.stdout:
                        space_line = [line for line in result.stdout.split('\n') if 'Total reclaimed space:' in line]
                        if space_line:
                            space_str = space_line[0].split('Total reclaimed space:')[1].strip()
                            try:
                                space_freed = self.parse_size_string(space_str)
                                total_space_freed += space_freed
                            except:
                                pass
                    print("   ✅ Unused containers removed")
                else:
                    print(f"   ⚠️ Container cleanup warning: {result.stderr}")
                
                # Prune images (all unused)
                print("🧹 Removing ALL unused images...")
                result = self.run_docker_command(['image', 'prune', '-a', '-f'], check=False)
                if result.returncode == 0:
                    if "Total reclaimed space:" in result.stdout:
                        space_line = [line for line in result.stdout.split('\n') if 'Total reclaimed space:' in line]
                        if space_line:
                            space_str = space_line[0].split('Total reclaimed space:')[1].strip()
                            try:
                                space_freed = self.parse_size_string(space_str)
                                total_space_freed += space_freed
                            except:
                                pass
                    print("   ✅ All unused images removed")
                else:
                    print(f"   ⚠️ Image cleanup warning: {result.stderr}")
                
                # Prune volumes
                print("🧹 Removing unused volumes...")
                result = self.run_docker_command(['volume', 'prune', '-f'], check=False)
                if result.returncode == 0:
                    if "Total reclaimed space:" in result.stdout:
                        space_line = [line for line in result.stdout.split('\n') if 'Total reclaimed space:' in line]
                        if space_line:
                            space_str = space_line[0].split('Total reclaimed space:')[1].strip()
                            try:
                                space_freed = self.parse_size_string(space_str)
                                total_space_freed += space_freed
                            except:
                                pass
                    print("   ✅ Unused volumes removed")
                else:
                    print(f"   ⚠️ Volume cleanup warning: {result.stderr}")
                
                # Prune networks
                print("🧹 Removing unused networks...")
                result = self.run_docker_command(['network', 'prune', '-f'], check=False)
                if result.returncode == 0:
                    print("   ✅ Unused networks removed")
                else:
                    print(f"   ⚠️ Network cleanup warning: {result.stderr}")
            
            if cleanup_choice in ['2', '3']:
                # Build cache cleanup
                print("🧹 Removing build cache...")
                
                # Use docker builder prune for aggressive cache cleanup
                result = self.run_docker_command(['builder', 'prune', '-a', '-f'], check=False)
                if result.returncode == 0:
                    if "Total:" in result.stdout:
                        # Extract space information from builder prune output
                        lines = result.stdout.split('\n')
                        for line in lines:
                            if 'Total:' in line and 'reclaimed' in line.lower():
                                try:
                                    # Parse line like "Total: 2.989GB"
                                    total_part = line.split('Total:')[1].strip()
                                    space_str = total_part.split()[0]
                                    space_freed = self.parse_size_string(space_str)
                                    total_space_freed += space_freed
                                    print(f"   ✅ Build cache removed: {self.format_size(int(space_freed))}")
                                    break
                                except:
                                    pass
                    else:
                        print("   ✅ Build cache cleaned")
                else:
                    print(f"   ⚠️ Build cache cleanup warning: {result.stderr}")
                
                # Also run system prune for comprehensive cleanup
                if cleanup_choice == '2':
                    print("🧹 Running comprehensive system cleanup...")
                    result = self.run_docker_command(['system', 'prune', '-a', '-f'], check=False)
                    if result.returncode == 0:
                        print("   ✅ Comprehensive system cleanup completed")
                    else:
                        print(f"   ⚠️ System cleanup warning: {result.stderr}")
            
            # Get build cache info after cleanup
            build_cache_after, reclaimable_after = self.get_build_cache_info()
            
            # Show final usage
            print("\n📊 Final Docker usage:")
            result = self.run_docker_command(['system', 'df'], check=False)
            if result.returncode == 0:
                print(result.stdout)
            
            # Show cleanup summary
            print(f"\n📈 Cleanup Summary:")
            if total_space_freed > 0:
                print(f"   💾 Total space freed: {self.format_size(int(total_space_freed))}")
            
            if build_cache_before is not None and build_cache_after is not None:
                build_cache_freed = build_cache_before - build_cache_after
                if build_cache_freed > 0:
                    print(f"   🏗️ Build cache freed: {self.format_size(int(build_cache_freed))}")
                print(f"   🏗️ Build cache remaining: {self.format_size(int(build_cache_after))}")
            
            print("✅ Docker system cleanup completed!")
            
        except Exception as e:
            print(f"❌ Docker cleanup error: {e}")
    
    def list_customer_database_records(self):
        """List all customer database records with detailed information"""
        print("\n🗄️ Customer Database Records (All Columns):\n")
        
        try:
            conn = sqlite3.connect(CUSTOMERS_DB)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM customers
                ORDER BY created_at DESC
            """)
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                print("ℹ️ No customer records found in database.")
                return []
            
            # Print each record with all fields in a detailed format
            for idx, row in enumerate(rows, 1):
                print(f"{'='*80}")
                print(f"Record #{idx} (Database ID: {row['id']})")
                print(f"{'='*80}")
                
                # Basic info
                print(f"🌐 Subdomain:        {row['subdomain']}")
                print(f"📧 Customer Email:   {row['email']}")
                print(f"📱 App Name:         {row['app_name']}")
                print(f"📦 Plan:             {row['plan']}")
                print(f"🔌 Port:             {row['port']}")
                print(f"🏢 Organization:     {row['organization_name'] or 'N/A'}")
                
                # Dates
                created = self.format_datetime(row['created_at']) if row['created_at'] else 'unknown'
                email_created = self.format_datetime(row['email_created']) if row['email_created'] else 'N/A'
                print(f"📅 Created At:       {created}")
                print(f"📅 Email Created:    {email_created}")
                
                # Deployment info
                deployed_status = 'Yes' if row['deployed'] else 'No'
                print(f"🚀 Deployed:         {deployed_status}")
                
                # Email configuration
                print(f"📬 App Email:        {row['email_address'] or 'N/A'}")
                print(f"🔑 Email Password:   {'***SET***' if row['email_password'] else 'N/A'}")
                print(f"📤 Forwarding Email: {row['forwarding_email'] or 'N/A'}")
                print(f"✅ Email Status:     {row['email_status'] or 'pending'}")
                
                # Security info
                print(f"🔐 Admin Password:   {'***SET***' if row['admin_password'] else 'N/A'}")
                
                print()  # Empty line for readability
            
            print(f"📊 Total records: {len(rows)}")
            
            # Return structured data for other functions
            records = []
            for row in rows:
                records.append({
                    'id': row['id'],
                    'subdomain': row['subdomain'],
                    'email': row['email'],
                    'app_name': row['app_name'],
                    'plan': row['plan'],
                    'port': row['port'],
                    'created_at': row['created_at'],
                    'deployed': row['deployed'],
                    'organization_name': row['organization_name'],
                    'email_address': row['email_address'],
                    'email_password': row['email_password'],
                    'forwarding_email': row['forwarding_email'],
                    'email_created': row['email_created'],
                    'email_status': row['email_status'],
                    'admin_password': row['admin_password']
                })
            
            return records
            
        except sqlite3.Error as e:
            print(f"❌ Database error: {e}")
            return []
        except FileNotFoundError:
            print(f"⚠️ Database file {CUSTOMERS_DB} not found")
            return []

    def show_detailed_customer_record(self, record):
        """Show detailed information about a customer record"""
        print(f"\n📋 Detailed Record Information:")
        print(f"   🆔 Database ID: {record['id']}")
        print(f"   🌐 Subdomain: {record['subdomain']}")
        print(f"   📧 Customer Email: {record['email']}")
        print(f"   📦 Plan: {record['plan']}")
        print(f"   🔌 Port: {record['port']}")
        print(f"   🏢 Organization: {record['organization_name'] or 'N/A'}")
        print(f"   📬 App Email: {record['email_address'] or 'N/A'}")
        print(f"   📤 Forwarding Email: {record['forwarding_email'] or 'N/A'}")
        print(f"   ✅ Email Status: {record['email_status'] or 'unknown'}")
        print(f"   📅 Created: {self.format_datetime(record['created_at']) if record['created_at'] else 'unknown'}")

    def delete_customer_database_record(self):
        """Delete a specific customer database record"""
        records = self.list_customer_database_records()
        if not records:
            return
        
        try:
            choice = int(input(f"\nEnter the number of the record to delete (1-{len(records)}): "))
            if 1 <= choice <= len(records):
                selected_record = records[choice - 1]
                
                # Show detailed record information
                self.show_detailed_customer_record(selected_record)
                
                subdomain = selected_record['subdomain']
                customer_email = selected_record['email']
                
                print(f"\n⚠️ You are about to DELETE the database record for:")
                print(f"   🌐 Subdomain: {subdomain}")
                print(f"   📧 Customer: {customer_email}")
                print(f"   🆔 Database ID: {selected_record['id']}")
                
                confirm = input(f"\n❗ Type 'DELETE {subdomain}' to confirm deletion: ")
                if confirm == f"DELETE {subdomain}":
                    try:
                        conn = sqlite3.connect(CUSTOMERS_DB)
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM customers WHERE id = ?", (selected_record['id'],))
                        
                        if cursor.rowcount > 0:
                            conn.commit()
                            print(f"✅ Database record for '{subdomain}' (ID: {selected_record['id']}) deleted successfully")
                        else:
                            print(f"❌ No record found with ID {selected_record['id']}")
                        
                        conn.close()
                        
                    except sqlite3.Error as e:
                        print(f"❌ Database error: {e}")
                else:
                    print("❌ Deletion aborted.")
            else:
                print("❌ Invalid choice.")
        except ValueError:
            print("❌ Invalid number.")
        except Exception as e:
            print(f"❌ Error: {e}")

    def show_menu(self):
        """Display the main menu"""

        title = pyfiglet.figlet_format("minipass", font = "big" ) 
        print(title)

        print("  1.  List all MiniPass applications")
        print("  2.  Delete specific MiniPass application")
        print("  3.  Cleanup orphaned containers")
        print("  4.  Cleanup orphaned database entries")
        print("  5.  Docker system cleanup")
        print("  6.  View customer database records")
        print("  7.  Delete specific database record")
        print("")

        print("  x.  Exit")




    
    def run(self):
        """Main program loop"""
        while True:
            self.show_menu()
            
            try:
                choice = input("\nChoose an option (1-7):> ").strip()
                
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
                                if selected_app['db_entry'].get('email_address'):
                                    print(f"  - Email account: {selected_app['db_entry']['email_address']} (will be deleted from mail server)")
                                else:
                                    print(f"  - Email account: None associated")
                            
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
                    self.list_customer_database_records()
                
                elif choice == '7':
                    self.delete_customer_database_record()
                
                elif choice == 'x':
                    print("👋 Goodbye!")
                    break
                
                else:
                    print("❌ Invalid choice. Please enter 1-8.")
                    
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

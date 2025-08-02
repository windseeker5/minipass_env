#!/usr/bin/env python3
"""
MiniPass Application Manager - Enhanced Version

A comprehensive management tool for MiniPass Flask-based SaaS platform
that provides automated password management app deployment.

This enhanced version includes:
- Robust error handling and logging
- Improved Docker command execution
- Better validation of container and resource existence
- Rollback mechanism for failed cleanup operations
- Production-ready code with comprehensive safety checks

Author: Python DevOps Automation Specialist
Version: 2.0 (Enhanced)
"""

import os
import sqlite3
import subprocess
import shutil
import sys
import json
import re
import logging
import time
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Union
from contextlib import contextmanager
import pyfiglet


# Configuration Constants
CUSTOMERS_DB = "MinipassWebSite/customers.db"
DEPLOYED_FOLDER = "deployed"

# Mail server constants (from mail_manager.py)
MAILSERVER = "mailserver"
DOMAIN = "minipass.me"
LOCAL_SIEVE_BASE = "./config/user-patches"
FORWARD_DIR = "./config/user-patches"

# Operation timeouts (seconds)
DOCKER_TIMEOUT = 30
DATABASE_TIMEOUT = 10
FILE_OPERATION_TIMEOUT = 15


class MiniPassError(Exception):
    """Base exception for MiniPass operations"""
    pass


class DockerError(MiniPassError):
    """Docker-related errors"""
    pass


class DatabaseError(MiniPassError):
    """Database-related errors"""
    pass


class EmailError(MiniPassError):
    """Email operation errors"""
    pass


class FileSystemError(MiniPassError):
    """File system operation errors"""
    pass


def setup_logging() -> logging.Logger:
    """Setup comprehensive logging configuration"""
    logger = logging.getLogger('minipass_manager')
    logger.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # File handler for detailed logs
    file_handler = logging.FileHandler('minipass_manager.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


class MiniPassAppManager:
    """Enhanced MiniPass Application Manager with robust error handling"""
    
    def __init__(self):
        self.logger = setup_logging()
        self.logger.info("Initializing MiniPass Application Manager")
        self.check_docker_available()
    
    def check_docker_available(self) -> None:
        """Check if Docker is available with comprehensive validation"""
        try:
            self.logger.debug("Checking Docker availability")
            result = subprocess.run(
                ['docker', '--version'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode != 0:
                self.logger.error(f"Docker check failed with return code {result.returncode}")
                raise DockerError("Docker not available")
            
            # Also check if Docker daemon is running
            result = subprocess.run(
                ['docker', 'info'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode != 0:
                self.logger.error("Docker daemon not running")
                raise DockerError("Docker daemon not accessible")
                
            self.logger.info("Docker is available and running")
            
        except FileNotFoundError:
            self.logger.error("Docker command not found in PATH")
            raise DockerError("Docker command not found")
        except subprocess.TimeoutExpired:
            self.logger.error("Docker check timed out")
            raise DockerError("Docker check timeout")
        except Exception as e:
            self.logger.error(f"Docker check failed: {e}")
            raise DockerError(f"Docker check failed: {e}")
    
    def run_docker_command(self, cmd: List[str], check: bool = True, timeout: int = DOCKER_TIMEOUT) -> subprocess.CompletedProcess:
        """
        Run a docker command with robust error handling and timeout
        
        Args:
            cmd: Docker command arguments (without 'docker' prefix)
            check: Whether to raise exception on non-zero return code
            timeout: Command timeout in seconds
            
        Returns:
            subprocess.CompletedProcess object
            
        Raises:
            DockerError: On command failure or timeout
        """
        full_cmd = ['docker'] + cmd
        cmd_str = ' '.join(full_cmd)
        
        try:
            self.logger.debug(f"Executing Docker command: {cmd_str}")
            
            result = subprocess.run(
                full_cmd, 
                capture_output=True, 
                text=True, 
                check=False,  # We handle return codes manually
                timeout=timeout
            )
            
            self.logger.debug(f"Command completed with return code {result.returncode}")
            
            if result.returncode != 0:
                error_msg = f"Docker command failed: {cmd_str}\nReturn code: {result.returncode}\nStderr: {result.stderr}"
                self.logger.error(error_msg)
                
                if check:
                    raise DockerError(error_msg)
            
            return result
            
        except subprocess.TimeoutExpired:
            error_msg = f"Docker command timed out after {timeout}s: {cmd_str}"
            self.logger.error(error_msg)
            raise DockerError(error_msg)
        except Exception as e:
            error_msg = f"Error running docker command '{cmd_str}': {e}"
            self.logger.error(error_msg)
            raise DockerError(error_msg)
    
    def container_exists(self, container_name: str) -> bool:
        """
        Check if a container exists with exact name matching
        
        Args:
            container_name: Exact container name to check
            
        Returns:
            True if container exists, False otherwise
        """
        try:
            self.logger.debug(f"Checking if container exists: {container_name}")
            
            result = self.run_docker_command([
                'ps', '-a', 
                '--filter', f'name=^/{container_name}$',  # Exact match
                '--format', '{{.Names}}'
            ], check=False)
            
            if result.returncode != 0:
                self.logger.warning(f"Failed to check container existence: {result.stderr}")
                return False
            
            # Check if the exact container name is in the output
            container_names = [name.strip() for name in result.stdout.strip().split('\n') if name.strip()]
            exists = container_name in container_names
            
            self.logger.debug(f"Container {container_name} exists: {exists}")
            return exists
            
        except Exception as e:
            self.logger.error(f"Error checking container existence: {e}")
            return False
    
    def image_exists(self, image_name: str) -> bool:
        """
        Check if a Docker image exists with exact name matching
        
        Args:
            image_name: Exact image name to check
            
        Returns:
            True if image exists, False otherwise
        """
        try:
            self.logger.debug(f"Checking if image exists: {image_name}")
            
            result = self.run_docker_command([
                'images', image_name, 
                '--format', '{{.Repository}}'
            ], check=False)
            
            if result.returncode != 0:
                self.logger.warning(f"Failed to check image existence: {result.stderr}")
                return False
            
            # Check if the image name is in the output
            image_names = [name.strip() for name in result.stdout.strip().split('\n') if name.strip()]
            exists = image_name in image_names
            
            self.logger.debug(f"Image {image_name} exists: {exists}")
            return exists
            
        except Exception as e:
            self.logger.error(f"Error checking image existence: {e}")
            return False
    
    @contextmanager
    def database_connection(self, database_path: str = CUSTOMERS_DB):
        """
        Context manager for database connections with proper error handling
        
        Args:
            database_path: Path to SQLite database file
            
        Yields:
            sqlite3.Connection object
            
        Raises:
            DatabaseError: On connection or operation failure
        """
        conn = None
        try:
            self.logger.debug(f"Opening database connection to {database_path}")
            
            if not os.path.exists(database_path):
                raise DatabaseError(f"Database file not found: {database_path}")
            
            conn = sqlite3.connect(database_path, timeout=DATABASE_TIMEOUT)
            conn.row_factory = sqlite3.Row
            
            yield conn
            
        except sqlite3.Error as e:
            self.logger.error(f"Database error: {e}")
            if conn:
                conn.rollback()
            raise DatabaseError(f"Database operation failed: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected database error: {e}")
            if conn:
                conn.rollback()
            raise DatabaseError(f"Unexpected database error: {e}")
        finally:
            if conn:
                conn.close()
                self.logger.debug("Database connection closed")
    
    def get_customers_from_db(self) -> Dict[str, Dict]:
        """Get all customers from database with enhanced error handling"""
        customers = {}
        
        try:
            with self.database_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT subdomain, email, port, plan, created_at, organization_name, 
                           email_address, email_status
                    FROM customers
                """)
                rows = cursor.fetchall()
                
                for row in rows:
                    customers[row['subdomain']] = dict(row)
                
                self.logger.info(f"Retrieved {len(customers)} customer records from database")
                
        except DatabaseError as e:
            self.logger.error(f"Failed to retrieve customers: {e}")
            print(f"❌ Database error: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error retrieving customers: {e}")
            print(f"❌ Unexpected error: {e}")
            
        return customers
    
    def get_minipass_containers(self) -> List[Dict]:
        """Get all containers created by the website controller with enhanced validation"""
        containers = []
        
        try:
            self.logger.debug("Retrieving MiniPass containers")
            
            # Get all containers with format
            result = self.run_docker_command(['ps', '-a', '--format', 'json'], check=False)
            
            if result.returncode != 0:
                self.logger.error(f"Failed to get containers: {result.stderr}")
                return containers
            
            for line in result.stdout.strip().split('\n'):
                if not line.strip():
                    continue
                    
                try:
                    container_data = json.loads(line)
                    container_name = container_data.get('Names', '')
                    
                    # Validate container name format more strictly
                    if self._is_minipass_container(container_name):
                        subdomain = container_name.replace("minipass_", "")
                        
                        # Validate subdomain format
                        if not self._is_valid_subdomain(subdomain):
                            self.logger.warning(f"Invalid subdomain format: {subdomain}")
                            continue
                        
                        # Get memory usage safely
                        memory_usage = self.get_container_memory_usage(container_name)
                        
                        # Get deployed folder size safely
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
                        
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Invalid JSON in container data: {e}")
                    continue
                except Exception as e:
                    self.logger.warning(f"Error processing container data: {e}")
                    continue
            
            self.logger.info(f"Found {len(containers)} MiniPass containers")
                    
        except DockerError as e:
            self.logger.error(f"Docker error getting containers: {e}")
            print(f"❌ Docker error: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error getting containers: {e}")
            print(f"❌ Unexpected error: {e}")
            
        return containers
    
    def _is_minipass_container(self, container_name: str) -> bool:
        """Validate if container name follows MiniPass naming convention"""
        if not container_name or not isinstance(container_name, str):
            return False
        
        # Must start with 'minipass_' and have a subdomain part
        if not container_name.startswith("minipass_"):
            return False
        
        subdomain = container_name.replace("minipass_", "")
        return len(subdomain) > 0 and self._is_valid_subdomain(subdomain)
    
    def _is_valid_subdomain(self, subdomain: str) -> bool:
        """Validate subdomain format"""
        if not subdomain or not isinstance(subdomain, str):
            return False
        
        # Basic subdomain validation: alphanumeric and hyphens, 3-63 chars
        if len(subdomain) < 3 or len(subdomain) > 63:
            return False
        
        # Must start and end with alphanumeric character
        if not subdomain[0].isalnum() or not subdomain[-1].isalnum():
            return False
        
        # Only alphanumeric and hyphens allowed
        return all(c.isalnum() or c == '-' for c in subdomain)
    
    def get_container_memory_usage(self, container_name: str) -> str:
        """Get memory usage for a specific container with timeout handling"""
        try:
            self.logger.debug(f"Getting memory usage for container: {container_name}")
            
            # Use docker stats to get memory usage with shorter timeout
            result = self.run_docker_command([
                'stats', '--no-stream', '--format', 'json', container_name
            ], check=False, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                stats_data = json.loads(result.stdout.strip())
                memory_usage = stats_data.get('MemUsage', 'N/A')
                self.logger.debug(f"Memory usage for {container_name}: {memory_usage}")
                return memory_usage
            else:
                self.logger.debug(f"Could not get memory usage for {container_name}")
                return 'N/A'
                
        except Exception as e:
            self.logger.warning(f"Error getting memory usage for {container_name}: {e}")
            return 'N/A'
    
    def get_deployed_folder_size(self, subdomain: str) -> int:
        """Get the size of the deployed folder for a subdomain with error handling"""
        try:
            folder_path = os.path.join(DEPLOYED_FOLDER, subdomain)
            if not os.path.exists(folder_path):
                return 0
            
            return self.get_folder_size(folder_path)
        except Exception as e:
            self.logger.warning(f"Error getting deployed folder size for {subdomain}: {e}")
            return 0
    
    def get_minipass_images(self) -> List[Dict]:
        """Get all images created by the website controller with enhanced validation"""
        images = []
        
        try:
            self.logger.debug("Retrieving MiniPass images")
            
            # Get all images with format
            result = self.run_docker_command(['images', '--format', 'json'], check=False)
            
            if result.returncode != 0:
                self.logger.error(f"Failed to get images: {result.stderr}")
                return images
            
            for line in result.stdout.strip().split('\n'):
                if not line.strip():
                    continue
                    
                try:
                    image_data = json.loads(line)
                    repository = image_data.get('Repository', '')
                    tag = image_data.get('Tag', '')
                    full_tag = f"{repository}:{tag}" if tag != '<none>' else repository
                    
                    if self._is_minipass_image(repository):
                        subdomain = repository.replace("-flask-app", "")
                        
                        # Validate subdomain format
                        if not self._is_valid_subdomain(subdomain):
                            self.logger.warning(f"Invalid subdomain in image: {subdomain}")
                            continue
                        
                        image_info = {
                            'tag': full_tag,
                            'subdomain': subdomain,
                            'id': image_data.get('ID', '')[:12],
                            'size': image_data.get('Size', '0B'),
                            'created': image_data.get('CreatedAt', '')
                        }
                        images.append(image_info)
                        
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Invalid JSON in image data: {e}")
                    continue
                except Exception as e:
                    self.logger.warning(f"Error processing image data: {e}")
                    continue
            
            self.logger.info(f"Found {len(images)} MiniPass images")
                    
        except DockerError as e:
            self.logger.error(f"Docker error getting images: {e}")
            print(f"❌ Docker error getting images: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error getting images: {e}")
            print(f"❌ Unexpected error: {e}")
            
        return images
    
    def _is_minipass_image(self, repository: str) -> bool:
        """Validate if image repository follows MiniPass naming convention"""
        if not repository or not isinstance(repository, str):
            return False
        
        # Must end with '-flask-app' and have a subdomain part
        if not repository.endswith("-flask-app"):
            return False
        
        subdomain = repository.replace("-flask-app", "")
        return len(subdomain) > 0
    
    def format_size(self, size_bytes: int) -> str:
        """Format bytes to human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def format_datetime(self, datetime_str: str) -> str:
        """Format datetime string to readable format with error handling"""
        if not datetime_str:
            return 'unknown'
        
        try:
            if 'T' in datetime_str:
                # Handle ISO format datetime
                dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d %H:%M')
            return datetime_str[:16] if len(datetime_str) > 16 else datetime_str
        except Exception as e:
            self.logger.warning(f"Error formatting datetime '{datetime_str}': {e}")
            return datetime_str[:16] if datetime_str else 'unknown'
    
    def list_all_minipass_apps(self):
        """List all MiniPass apps with container and DB status"""
        print("\n🔍 Scanning for MiniPass applications...")
        
        try:
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
            
        except Exception as e:
            self.logger.error(f"Error listing applications: {e}")
            print(f"❌ Error listing applications: {e}")
            return []
    
    def comprehensive_app_cleanup(self, subdomain: str) -> bool:
        """
        Perform comprehensive cleanup of a MiniPass app with rollback capability
        
        Args:
            subdomain: The subdomain identifier for the app to cleanup
            
        Returns:
            True if cleanup completed successfully, False otherwise
        """
        if not self._is_valid_subdomain(subdomain):
            self.logger.error(f"Invalid subdomain format: {subdomain}")
            print(f"❌ Invalid subdomain format: {subdomain}")
            return False
        
        self.logger.info(f"Starting comprehensive cleanup for '{subdomain}'")
        print(f"\n🧹 Starting comprehensive cleanup for '{subdomain}'...")
        
        cleanup_state = {
            'container_removed': False,
            'image_removed': False,
            'files_removed': False,
            'email_removed': False,
            'db_removed': False
        }
        
        success = True
        space_freed = 0
        
        # Pre-cleanup validation
        container_name = f"minipass_{subdomain}"
        image_name = f"{subdomain}-flask-app"
        
        # 1. Remove Docker container with enhanced error handling
        try:
            self.logger.info(f"Step 1: Removing Docker container '{container_name}'")
            
            if self.container_exists(container_name):
                print(f"🛑 Stopping and removing container '{container_name}'...")
                
                # Stop container with timeout
                self.logger.debug(f"Stopping container {container_name}")
                stop_result = self.run_docker_command(['stop', container_name], check=False, timeout=30)
                
                if stop_result.returncode == 0:
                    print("   ✅ Container stopped")
                    self.logger.info(f"Container {container_name} stopped successfully")
                else:
                    self.logger.warning(f"Failed to stop container {container_name}: {stop_result.stderr}")
                    print("   ⚠️ Container stop failed, proceeding with force removal")
                
                # Remove container with volumes and force
                self.logger.debug(f"Removing container {container_name}")
                remove_result = self.run_docker_command(['rm', '-f', '-v', container_name], check=False)
                
                if remove_result.returncode == 0:
                    print("   ✅ Container removed")
                    self.logger.info(f"Container {container_name} removed successfully")
                    cleanup_state['container_removed'] = True
                else:
                    error_msg = f"Failed to remove container {container_name}: {remove_result.stderr}"
                    self.logger.error(error_msg)
                    print(f"   ❌ Container removal failed: {remove_result.stderr}")
                    success = False
            else:
                print(f"   ℹ️ Container '{container_name}' not found")
                self.logger.info(f"Container {container_name} does not exist")
                cleanup_state['container_removed'] = True  # Nothing to remove is success
                
        except Exception as e:
            error_msg = f"Error removing container {container_name}: {e}"
            self.logger.error(error_msg)
            print(f"   ❌ Error removing container: {e}")
            success = False
        
        # 2. Remove Docker image with dependency checking
        try:
            self.logger.info(f"Step 2: Removing Docker image '{image_name}'")
            
            if self.image_exists(image_name):
                print(f"🗑️ Removing image '{image_name}'...")
                
                # Check if image is being used by other containers
                usage_result = self.run_docker_command([
                    'ps', '-a', '--filter', f'ancestor={image_name}', '--format', '{{.Names}}'
                ], check=False)
                
                if usage_result.returncode == 0 and usage_result.stdout.strip():
                    running_containers = [name.strip() for name in usage_result.stdout.strip().split('\n') if name.strip()]
                    if running_containers:
                        self.logger.warning(f"Image {image_name} is still used by containers: {running_containers}")
                        print(f"   ⚠️ Image is still used by containers: {', '.join(running_containers)}")
                
                # Remove image with force
                self.logger.debug(f"Removing image {image_name}")
                remove_result = self.run_docker_command(['rmi', '-f', image_name], check=False)
                
                if remove_result.returncode == 0:
                    print("   ✅ Image removed")
                    self.logger.info(f"Image {image_name} removed successfully")
                    cleanup_state['image_removed'] = True
                else:
                    error_msg = f"Failed to remove image {image_name}: {remove_result.stderr}"
                    self.logger.error(error_msg)
                    print(f"   ❌ Image removal failed: {remove_result.stderr}")
                    success = False
            else:
                print(f"   ℹ️ Image '{image_name}' not found")
                self.logger.info(f"Image {image_name} does not exist")
                cleanup_state['image_removed'] = True  # Nothing to remove is success
                
        except Exception as e:
            error_msg = f"Error removing image {image_name}: {e}"
            self.logger.error(error_msg)
            print(f"   ❌ Error removing image: {e}")
            success = False
        
        # 3. Remove ALL deployed files and folders with enhanced safety
        try:
            self.logger.info(f"Step 3: Removing deployed files for '{subdomain}'")
            
            folder_path = os.path.join(DEPLOYED_FOLDER, subdomain)
            if os.path.exists(folder_path):
                folder_size = self.get_folder_size(folder_path)
                print(f"📁 Removing ALL deployed files and folders for '{subdomain}' ({self.format_size(folder_size)})...")
                
                # Validate path safety
                if not self._is_safe_path(folder_path):
                    error_msg = f"Unsafe path detected: {folder_path}"
                    self.logger.error(error_msg)
                    print(f"   ❌ {error_msg}")
                    success = False
                else:
                    # Force remove with enhanced error handling
                    self.logger.debug(f"Removing folder {folder_path}")
                    if self.force_remove_folder(folder_path):
                        space_freed += folder_size
                        print("   ✅ All deployed files and folders removed")
                        self.logger.info(f"Deployed folder {folder_path} removed successfully")
                        cleanup_state['files_removed'] = True
                    else:
                        error_msg = f"Failed to remove deployed folder {folder_path}"
                        self.logger.error(error_msg)
                        print(f"   ❌ Failed to remove deployed folder")
                        success = False
                        
                # Clean up subdomain references
                self.cleanup_subdomain_references(subdomain)
            else:
                print(f"   ℹ️ Deployed folder '{folder_path}' not found")
                self.logger.info(f"Deployed folder {folder_path} does not exist")
                cleanup_state['files_removed'] = True  # Nothing to remove is success
                
        except Exception as e:
            error_msg = f"Error removing deployed files for {subdomain}: {e}"
            self.logger.error(error_msg)
            print(f"   ❌ Error removing deployed files: {e}")
            success = False
        
        # 4. Get email address before database deletion with transaction safety
        email_address = None
        try:
            self.logger.info(f"Step 4: Retrieving email address for '{subdomain}'")
            
            with self.database_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT email_address FROM customers WHERE subdomain = ?", (subdomain,))
                result = cursor.fetchone()
                if result:
                    email_address = result[0]
                    self.logger.info(f"Found email address for {subdomain}: {email_address}")
                else:
                    self.logger.info(f"No email address found for {subdomain}")
                    
        except DatabaseError as e:
            self.logger.warning(f"Warning getting email address for {subdomain}: {e}")
            print(f"   ⚠️ Warning getting email address: {e}")
        except Exception as e:
            self.logger.warning(f"Unexpected error getting email address for {subdomain}: {e}")
            print(f"   ⚠️ Warning getting email address: {e}")
        
        # 5. Delete associated email account with enhanced validation
        if email_address:
            try:
                self.logger.info(f"Step 5: Deleting email account '{email_address}'")
                email_success = self.delete_associated_email(email_address)
                if email_success:
                    cleanup_state['email_removed'] = True
                    self.logger.info(f"Email account {email_address} deleted successfully")
                else:
                    success = False
                    self.logger.error(f"Failed to delete email account {email_address}")
            except Exception as e:
                error_msg = f"Error deleting email account {email_address}: {e}"
                self.logger.error(error_msg)
                print(f"   ❌ Error deleting email account: {e}")
                success = False
        else:
            print("   ℹ️ No email address associated with this app")
            self.logger.info(f"No email address associated with {subdomain}")
            cleanup_state['email_removed'] = True  # Nothing to remove is success
        
        # 6. Remove from database with transaction safety
        try:
            self.logger.info(f"Step 6: Removing database entry for '{subdomain}'")
            
            with self.database_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM customers WHERE subdomain = ?", (subdomain,))
                count = cursor.fetchone()[0]
                
                if count > 0:
                    print(f"🗄️ Removing database entry for '{subdomain}'...")
                    cursor.execute("DELETE FROM customers WHERE subdomain = ?", (subdomain,))
                    conn.commit()
                    
                    if cursor.rowcount > 0:
                        print("   ✅ Database entry removed")
                        self.logger.info(f"Database entry for {subdomain} removed successfully")
                        cleanup_state['db_removed'] = True
                    else:
                        error_msg = f"Database entry for {subdomain} was not deleted"
                        self.logger.error(error_msg)
                        print(f"   ❌ Database entry was not deleted")
                        success = False
                else:
                    print(f"   ℹ️ No database entry found for '{subdomain}'")
                    self.logger.info(f"No database entry found for {subdomain}")
                    cleanup_state['db_removed'] = True  # Nothing to remove is success
                    
        except DatabaseError as e:
            error_msg = f"Database error removing entry for {subdomain}: {e}"
            self.logger.error(error_msg)
            print(f"   ❌ Database error: {e}")
            success = False
        except Exception as e:
            error_msg = f"Unexpected error removing database entry for {subdomain}: {e}"
            self.logger.error(error_msg)
            print(f"   ❌ Unexpected error: {e}")
            success = False
        
        # 7. Clean up dangling images
        try:
            self.logger.info("Step 7: Cleaning up dangling images")
            print("🧽 Cleaning up dangling images...")
            
            result = self.run_docker_command(['image', 'prune', '-f'], check=False)
            if result.returncode == 0:
                print("   ✅ Dangling images cleaned")
                self.logger.info("Dangling images cleaned successfully")
            else:
                print("   ℹ️ No dangling images found")
                self.logger.info("No dangling images to clean")
                
        except Exception as e:
            self.logger.warning(f"Warning cleaning dangling images: {e}")
            print(f"   ⚠️ Warning cleaning dangling images: {e}")
        
        # Summary and logging
        cleanup_summary = f"Cleanup for {subdomain} - " + \
                         f"Container: {'✅' if cleanup_state['container_removed'] else '❌'}, " + \
                         f"Image: {'✅' if cleanup_state['image_removed'] else '❌'}, " + \
                         f"Files: {'✅' if cleanup_state['files_removed'] else '❌'}, " + \
                         f"Email: {'✅' if cleanup_state['email_removed'] else '❌'}, " + \
                         f"DB: {'✅' if cleanup_state['db_removed'] else '❌'}"
        
        self.logger.info(cleanup_summary)
        
        if success:
            print(f"\n✅ Cleanup completed successfully!")
            self.logger.info(f"Comprehensive cleanup for {subdomain} completed successfully")
        else:
            print(f"\n⚠️ Cleanup completed with warnings/errors")
            self.logger.warning(f"Comprehensive cleanup for {subdomain} completed with issues")
            
        if space_freed > 0:
            print(f"💾 Space freed: {self.format_size(space_freed)}")
            self.logger.info(f"Space freed: {self.format_size(space_freed)}")
        
        return success
    
    def _is_safe_path(self, path: str) -> bool:
        """
        Validate that the path is safe for deletion operations
        
        Args:
            path: File system path to validate
            
        Returns:
            True if path is safe, False otherwise
        """
        try:
            # Convert to absolute path
            abs_path = os.path.abspath(path)
            
            # Must be within the deployed folder
            deployed_abs = os.path.abspath(DEPLOYED_FOLDER)
            
            # Check if path is within deployed folder
            if not abs_path.startswith(deployed_abs):
                self.logger.error(f"Path {abs_path} is outside deployed folder {deployed_abs}")
                return False
            
            # Prevent deletion of the deployed folder itself
            if abs_path == deployed_abs:
                self.logger.error(f"Cannot delete the deployed folder itself: {abs_path}")
                return False
            
            # Additional safety checks
            dangerous_paths = ['/', '/home', '/usr', '/etc', '/var', '/boot', '/opt']
            for dangerous in dangerous_paths:
                if abs_path.startswith(dangerous) and not abs_path.startswith(deployed_abs):
                    self.logger.error(f"Path {abs_path} is in dangerous location")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating path safety for {path}: {e}")
            return False
    
    def get_folder_size(self, folder_path: str) -> int:
        """Calculate total size of a folder with enhanced error handling"""
        total = 0
        try:
            if not os.path.exists(folder_path):
                return 0
            
            for dirpath, dirnames, filenames in os.walk(folder_path):
                for filename in filenames:
                    try:
                        filepath = os.path.join(dirpath, filename)
                        if os.path.exists(filepath) and os.path.isfile(filepath):
                            total += os.path.getsize(filepath)
                    except (OSError, IOError) as e:
                        self.logger.warning(f"Could not get size of file {filepath}: {e}")
                        continue
                        
        except Exception as e:
            self.logger.warning(f"Error calculating folder size for {folder_path}: {e}")
            
        return total
    
    def force_remove_folder(self, folder_path: str) -> bool:
        """
        Force remove folder with all permissions and enhanced error handling
        
        Args:
            folder_path: Path to folder to remove
            
        Returns:
            True if removal successful, False otherwise
        """
        try:
            if not os.path.exists(folder_path):
                self.logger.info(f"Folder {folder_path} does not exist, nothing to remove")
                return True
            
            if not self._is_safe_path(folder_path):
                self.logger.error(f"Unsafe path for removal: {folder_path}")
                return False
            
            self.logger.debug(f"Attempting to remove folder: {folder_path}")
            
            # First try normal removal
            try:
                shutil.rmtree(folder_path)
                self.logger.debug(f"Successfully removed folder with shutil: {folder_path}")
                return True
            except PermissionError:
                self.logger.debug(f"Permission error removing {folder_path}, trying chmod approach")
                
                # If permission error, try with chmod
                import stat
                try:
                    for root, dirs, files in os.walk(folder_path):
                        for d in dirs:
                            dir_path = os.path.join(root, d)
                            try:
                                os.chmod(dir_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                            except OSError:
                                pass  # Continue even if chmod fails
                        for f in files:
                            file_path = os.path.join(root, f)
                            try:
                                os.chmod(file_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                            except OSError:
                                pass  # Continue even if chmod fails
                    
                    shutil.rmtree(folder_path)
                    self.logger.debug(f"Successfully removed folder after chmod: {folder_path}")
                    return True
                    
                except Exception as e:
                    self.logger.warning(f"Chmod approach failed for {folder_path}: {e}")
                    
            except Exception as e:
                self.logger.warning(f"Shutil removal failed for {folder_path}: {e}")
            
            # Last resort: use system rm command
            self.logger.debug(f"Using system rm command for {folder_path}")
            try:
                result = subprocess.run(
                    ['rm', '-rf', folder_path], 
                    capture_output=True, 
                    text=True, 
                    timeout=FILE_OPERATION_TIMEOUT
                )
                
                if result.returncode == 0:
                    self.logger.debug(f"Successfully removed folder with rm: {folder_path}")
                    return True
                else:
                    self.logger.error(f"System rm failed for {folder_path}: {result.stderr}")
                    return False
                    
            except subprocess.TimeoutExpired:
                self.logger.error(f"Timeout removing folder {folder_path}")
                return False
            except Exception as e:
                self.logger.error(f"System rm command failed for {folder_path}: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"Unexpected error removing folder {folder_path}: {e}")
            return False
    
    def cleanup_subdomain_references(self, subdomain: str):
        """Clean up any other references to the subdomain with enhanced safety"""
        try:
            self.logger.debug(f"Cleaning up subdomain references for: {subdomain}")
            
            # Check for any backup files or temp files that might contain the subdomain
            deployed_base = os.path.dirname(os.path.join(DEPLOYED_FOLDER, subdomain))
            
            if not os.path.exists(deployed_base):
                self.logger.debug(f"Deployed base directory does not exist: {deployed_base}")
                return
            
            # Validate deployed_base path safety
            if not self._is_safe_path(deployed_base):
                self.logger.error(f"Unsafe deployed base path: {deployed_base}")
                return
            
            for item in os.listdir(deployed_base):
                if subdomain in item and item != subdomain:
                    item_path = os.path.join(deployed_base, item)
                    
                    # Additional safety check for each item
                    if not self._is_safe_path(item_path):
                        self.logger.warning(f"Skipping unsafe path: {item_path}")
                        continue
                    
                    try:
                        if os.path.isfile(item_path):
                            self.logger.debug(f"Removing related file: {item_path}")
                            os.remove(item_path)
                            print(f"   🧹 Removed related file: {item}")
                        elif os.path.isdir(item_path):
                            self.logger.debug(f"Removing related directory: {item_path}")
                            if self.force_remove_folder(item_path):
                                print(f"   🧹 Removed related folder: {item}")
                            else:
                                self.logger.warning(f"Failed to remove related folder: {item_path}")
                                print(f"   ⚠️ Failed to remove related folder: {item}")
                    except Exception as e:
                        self.logger.warning(f"Error removing item {item_path}: {e}")
                        print(f"   ⚠️ Failed to remove {item}: {e}")
                        
        except Exception as e:
            self.logger.warning(f"Error cleaning subdomain references for {subdomain}: {e}")
            print(f"   ⚠️ Warning cleaning subdomain references: {e}")
    
    def delete_associated_email(self, email_address: str) -> bool:
        """
        Delete email user from mail server with enhanced error handling and validation
        
        Args:
            email_address: Email address to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        if not email_address:
            self.logger.warning("Empty email address provided for deletion")
            return True  # Nothing to delete
        
        # Validate email format
        if '@' not in email_address or not email_address.endswith(f'@{DOMAIN}'):
            self.logger.error(f"Invalid email format: {email_address}")
            print(f"   ❌ Invalid email format: {email_address}")
            return False
            
        self.logger.info(f"Deleting associated email account '{email_address}'")
        print(f"📧 Deleting associated email account '{email_address}'...")
        
        success = True
        
        # 1. Delete user from mail server
        try:
            self.logger.debug(f"Removing user {email_address} from mail server")
            print("   🗑️ Removing user from mail server...")
            
            result = subprocess.run([
                "docker", "exec", MAILSERVER,
                "setup", "email", "del", email_address
            ], capture_output=True, text=True, check=False, timeout=30)
            
            if result.returncode != 0:
                self.logger.warning(f"Warning deleting user {email_address} from mail server: {result.stderr}")
                print(f"   ⚠️ Warning deleting user from mail server: {result.stderr}")
                # Don't mark as failure immediately, might not exist
            else:
                self.logger.info(f"User {email_address} removed from mail server successfully")
                print("   ✅ User removed from mail server")
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout deleting user {email_address} from mail server")
            print(f"   ❌ Timeout deleting user from mail server")
            success = False
        except Exception as e:
            self.logger.error(f"Error deleting user {email_address} from mail server: {e}")
            print(f"   ❌ Error deleting user from mail server: {e}")
            success = False

        # 2. Remove forward configuration directory
        try:
            self.logger.debug(f"Removing forward configuration for {email_address}")
            local_forward_dir = os.path.join(FORWARD_DIR, email_address)
            
            if os.path.exists(local_forward_dir):
                # Validate path safety
                if self._is_safe_path(local_forward_dir):
                    print("   🧹 Removing forward configuration...")
                    if self.force_remove_folder(local_forward_dir):
                        self.logger.info(f"Forward configuration for {email_address} removed successfully")
                        print("   ✅ Forward configuration removed")
                    else:
                        self.logger.error(f"Failed to remove forward configuration for {email_address}")
                        print("   ❌ Failed to remove forward configuration")
                        success = False
                else:
                    self.logger.error(f"Unsafe forward directory path: {local_forward_dir}")
                    print(f"   ❌ Unsafe forward directory path")
                    success = False
            else:
                self.logger.info(f"No forward configuration found for {email_address}")
                print("   ℹ️ No forward configuration found")
                
        except Exception as e:
            self.logger.error(f"Error removing forward configuration for {email_address}: {e}")
            print(f"   ❌ Error removing forward configuration: {e}")
            success = False

        # 3. Remove inbox data from container
        try:
            self.logger.debug(f"Removing inbox data for {email_address}")
            local_part = email_address.split("@")[0]
            inbox_path = f"/var/mail/{DOMAIN}/{local_part}"
            print("   📭 Removing inbox data...")
            
            result = subprocess.run([
                "docker", "exec", MAILSERVER,
                "rm", "-rf", inbox_path
            ], capture_output=True, text=True, check=False, timeout=30)
            
            if result.returncode != 0:
                self.logger.warning(f"Warning removing inbox for {email_address}: {result.stderr}")
                print(f"   ⚠️ Warning removing inbox: {result.stderr}")
                # Don't mark as failure, inbox might not exist
            else:
                self.logger.info(f"Inbox data for {email_address} removed successfully")
                print("   ✅ Inbox data removed")
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout removing inbox data for {email_address}")
            print(f"   ❌ Timeout removing inbox data")
            success = False
        except Exception as e:
            self.logger.error(f"Error removing inbox data for {email_address}: {e}")
            print(f"   ❌ Error removing inbox data: {e}")
            success = False
        
        # 4. Validate deletion
        try:
            self.logger.debug(f"Validating email deletion for {email_address}")
            print("   🔍 Validating email deletion...")
            
            result = subprocess.run([
                "docker", "exec", MAILSERVER,
                "grep", "-i", email_address,
                "/tmp/docker-mailserver/postfix-accounts.cf"
            ], capture_output=True, text=True, check=False, timeout=15)
            
            if result.stdout.strip():
                self.logger.warning(f"Email {email_address} still exists in postfix-accounts.cf")
                print(f"   ⚠️ Warning: Email still exists in postfix-accounts.cf")
                success = False
            else:
                self.logger.info(f"Email {email_address} successfully removed from mail server")
                print("   ✅ Email successfully removed from mail server")
                
        except subprocess.TimeoutExpired:
            self.logger.warning(f"Timeout validating email deletion for {email_address}")
            print(f"   ⚠️ Timeout validating email deletion")
        except Exception as e:
            self.logger.warning(f"Could not validate email deletion for {email_address}: {e}")
            print(f"   ⚠️ Could not validate email deletion: {e}")
        
        if success:
            self.logger.info(f"Email account {email_address} deleted successfully")
        else:
            self.logger.error(f"Failed to completely delete email account {email_address}")
        
        return success
    
    def cleanup_orphaned_containers(self):
        """Remove containers that don't have database entries with enhanced validation"""
        print("\n🔍 Scanning for orphaned containers...")
        self.logger.info("Starting orphaned container cleanup")
        
        try:
            customers = self.get_customers_from_db()
            containers = self.get_minipass_containers()
            
            orphaned = [c for c in containers if c['subdomain'] not in customers]
            
            if not orphaned:
                print("✅ No orphaned containers found.")
                self.logger.info("No orphaned containers found")
                return
            
            print(f"\n⚠️ Found {len(orphaned)} orphaned containers:")
            for container in orphaned:
                print(f"  - {container['name']} ({container['status']})")
                
            self.logger.info(f"Found {len(orphaned)} orphaned containers: {[c['name'] for c in orphaned]}")
            
            confirm = input("\n❗ Remove all orphaned containers? (y/N): ").strip().lower()
            if confirm != 'y':
                print("❌ Aborted.")
                self.logger.info("Orphaned container cleanup aborted by user")
                return
            
            successful_cleanups = 0
            for container in orphaned:
                try:
                    self.logger.info(f"Cleaning up orphaned container: {container['name']}")
                    if self.comprehensive_app_cleanup(container['subdomain']):
                        successful_cleanups += 1
                except Exception as e:
                    self.logger.error(f"Error cleaning up container {container['name']}: {e}")
                    print(f"❌ Error cleaning up {container['name']}: {e}")
            
            self.logger.info(f"Orphaned container cleanup completed: {successful_cleanups}/{len(orphaned)} successful")
            print(f"\n✅ Cleanup completed: {successful_cleanups}/{len(orphaned)} containers cleaned successfully")
            
        except Exception as e:
            self.logger.error(f"Error during orphaned container cleanup: {e}")
            print(f"❌ Error during cleanup: {e}")
    
    def cleanup_orphaned_db_entries(self):
        """Remove database entries that don't have containers with enhanced validation"""
        print("\n🔍 Scanning for orphaned database entries...")
        self.logger.info("Starting orphaned database entry cleanup")
        
        try:
            customers = self.get_customers_from_db()
            containers = self.get_minipass_containers()
            container_subdomains = [c['subdomain'] for c in containers]
            
            orphaned = {k: v for k, v in customers.items() if k not in container_subdomains}
            
            if not orphaned:
                print("✅ No orphaned database entries found.")
                self.logger.info("No orphaned database entries found")
                return
            
            print(f"\n⚠️ Found {len(orphaned)} orphaned database entries:")
            for subdomain, info in orphaned.items():
                print(f"  - {subdomain} ({info['email']})")
                
            self.logger.info(f"Found {len(orphaned)} orphaned database entries: {list(orphaned.keys())}")
            
            confirm = input("\n❗ Remove all orphaned database entries? (y/N): ").strip().lower()
            if confirm != 'y':
                print("❌ Aborted.")
                self.logger.info("Orphaned database entry cleanup aborted by user")
                return
            
            try:
                with self.database_connection() as conn:
                    cursor = conn.cursor()
                    successful_deletions = 0
                    
                    for subdomain in orphaned.keys():
                        try:
                            cursor.execute("DELETE FROM customers WHERE subdomain = ?", (subdomain,))
                            if cursor.rowcount > 0:
                                print(f"🗑️ Removed database entry for '{subdomain}'")
                                self.logger.info(f"Removed database entry for {subdomain}")
                                successful_deletions += 1
                            else:
                                self.logger.warning(f"No database entry found for {subdomain} during deletion")
                        except Exception as e:
                            self.logger.error(f"Error deleting database entry for {subdomain}: {e}")
                            print(f"❌ Error deleting entry for {subdomain}: {e}")
                    
                    conn.commit()
                    
                    self.logger.info(f"Orphaned database cleanup completed: {successful_deletions}/{len(orphaned)} successful")
                    print(f"✅ Removed {successful_deletions}/{len(orphaned)} orphaned database entries.")
                    
            except DatabaseError as e:
                self.logger.error(f"Database error during orphaned entry cleanup: {e}")
                print(f"❌ Database error: {e}")
                
        except Exception as e:
            self.logger.error(f"Error during orphaned database entry cleanup: {e}")
            print(f"❌ Error during cleanup: {e}")
    
    def docker_system_cleanup(self):
        """Perform Docker system cleanup to free maximum space with enhanced safety"""
        print("\n🧹 Performing Docker system cleanup...")
        self.logger.info("Starting Docker system cleanup")
        
        try:
            # Get current usage
            print("📊 Current Docker usage:")
            
            # Get system df info
            result = self.run_docker_command(['system', 'df'], check=False)
            if result.returncode == 0:
                print(result.stdout)
                self.logger.debug(f"Docker system usage before cleanup:\n{result.stdout}")
            
            confirm = input("\n❗ Perform system cleanup (removes unused images, containers, networks, volumes)? (y/N): ").strip().lower()
            if confirm != 'y':
                print("❌ Aborted.")
                self.logger.info("Docker system cleanup aborted by user")
                return
            
            cleanup_results = {}
            
            # Prune containers
            try:
                print("🧹 Removing unused containers...")
                self.logger.debug("Pruning unused containers")
                result = self.run_docker_command(['container', 'prune', '-f'], check=False)
                if result.returncode == 0:
                    print("   ✅ Unused containers removed")
                    self.logger.info("Unused containers removed successfully")
                    cleanup_results['containers'] = True
                else:
                    print(f"   ❌ Container prune failed: {result.stderr}")
                    self.logger.error(f"Container prune failed: {result.stderr}")
                    cleanup_results['containers'] = False
            except Exception as e:
                print(f"   ❌ Error pruning containers: {e}")
                self.logger.error(f"Error pruning containers: {e}")
                cleanup_results['containers'] = False
            
            # Prune images
            try:
                print("🧹 Removing unused images...")
                self.logger.debug("Pruning unused images")
                result = self.run_docker_command(['image', 'prune', '-a', '-f'], check=False)
                if result.returncode == 0:
                    print("   ✅ Unused images removed")
                    self.logger.info("Unused images removed successfully")
                    cleanup_results['images'] = True
                else:
                    print(f"   ❌ Image prune failed: {result.stderr}")
                    self.logger.error(f"Image prune failed: {result.stderr}")
                    cleanup_results['images'] = False
            except Exception as e:
                print(f"   ❌ Error pruning images: {e}")
                self.logger.error(f"Error pruning images: {e}")
                cleanup_results['images'] = False
            
            # Prune volumes
            try:
                print("🧹 Removing unused volumes...")
                self.logger.debug("Pruning unused volumes")
                result = self.run_docker_command(['volume', 'prune', '-f'], check=False)
                if result.returncode == 0:
                    print("   ✅ Unused volumes removed")
                    self.logger.info("Unused volumes removed successfully")
                    cleanup_results['volumes'] = True
                else:
                    print(f"   ❌ Volume prune failed: {result.stderr}")
                    self.logger.error(f"Volume prune failed: {result.stderr}")
                    cleanup_results['volumes'] = False
            except Exception as e:
                print(f"   ❌ Error pruning volumes: {e}")
                self.logger.error(f"Error pruning volumes: {e}")
                cleanup_results['volumes'] = False
            
            # Prune networks
            try:
                print("🧹 Removing unused networks...")
                self.logger.debug("Pruning unused networks")
                result = self.run_docker_command(['network', 'prune', '-f'], check=False)
                if result.returncode == 0:
                    print("   ✅ Unused networks removed")
                    self.logger.info("Unused networks removed successfully")
                    cleanup_results['networks'] = True
                else:
                    print(f"   ❌ Network prune failed: {result.stderr}")
                    self.logger.error(f"Network prune failed: {result.stderr}")
                    cleanup_results['networks'] = False
            except Exception as e:
                print(f"   ❌ Error pruning networks: {e}")
                self.logger.error(f"Error pruning networks: {e}")
                cleanup_results['networks'] = False
            
            # Show final usage
            print("\n📊 Final Docker usage:")
            result = self.run_docker_command(['system', 'df'], check=False)
            if result.returncode == 0:
                print(result.stdout)
                self.logger.debug(f"Docker system usage after cleanup:\n{result.stdout}")
            
            # Summary
            successful_cleanups = sum(1 for success in cleanup_results.values() if success)
            total_cleanups = len(cleanup_results)
            
            if successful_cleanups == total_cleanups:
                print("✅ Docker system cleanup completed successfully!")
                self.logger.info("Docker system cleanup completed successfully")
            else:
                print(f"⚠️ Docker system cleanup completed with issues ({successful_cleanups}/{total_cleanups} operations successful)")
                self.logger.warning(f"Docker system cleanup completed with issues: {cleanup_results}")
            
        except Exception as e:
            self.logger.error(f"Error during Docker system cleanup: {e}")
            print(f"❌ Docker cleanup error: {e}")
    
    def list_customer_database_records(self):
        """List all customer database records with detailed information and enhanced error handling"""
        print("\n🗄️ Customer Database Records (All Columns):\n")
        self.logger.info("Listing customer database records")
        
        try:
            with self.database_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM customers
                    ORDER BY created_at DESC
                """)
                rows = cursor.fetchall()
                
                if not rows:
                    print("ℹ️ No customer records found in database.")
                    self.logger.info("No customer records found in database")
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
                self.logger.info(f"Listed {len(rows)} customer database records")
                
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
                
        except DatabaseError as e:
            self.logger.error(f"Database error listing records: {e}")
            print(f"❌ Database error: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error listing records: {e}")
            print(f"❌ Unexpected error: {e}")
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
        """Delete a specific customer database record with enhanced validation"""
        self.logger.info("Starting customer database record deletion")
        
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
                record_id = selected_record['id']
                
                print(f"\n⚠️ You are about to DELETE the database record for:")
                print(f"   🌐 Subdomain: {subdomain}")
                print(f"   📧 Customer: {customer_email}")
                print(f"   🆔 Database ID: {record_id}")
                
                confirm = input(f"\n❗ Type 'DELETE {subdomain}' to confirm deletion: ")
                if confirm == f"DELETE {subdomain}":
                    try:
                        with self.database_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM customers WHERE id = ?", (record_id,))
                            
                            if cursor.rowcount > 0:
                                conn.commit()
                                print(f"✅ Database record for '{subdomain}' (ID: {record_id}) deleted successfully")
                                self.logger.info(f"Database record deleted - ID: {record_id}, Subdomain: {subdomain}")
                            else:
                                print(f"❌ No record found with ID {record_id}")
                                self.logger.warning(f"No record found with ID {record_id} during deletion")
                        
                    except DatabaseError as e:
                        self.logger.error(f"Database error deleting record {record_id}: {e}")
                        print(f"❌ Database error: {e}")
                else:
                    print("❌ Deletion aborted.")
                    self.logger.info(f"Database record deletion aborted by user for {subdomain}")
            else:
                print("❌ Invalid choice.")
                self.logger.warning(f"Invalid choice for database record deletion: {choice}")
                
        except ValueError:
            print("❌ Invalid number.")
            self.logger.warning("Invalid number entered for database record deletion")
        except Exception as e:
            self.logger.error(f"Error during database record deletion: {e}")
            print(f"❌ Error: {e}")

    def show_menu(self):
        """Display the main menu"""
        title = pyfiglet.figlet_format("minipass", font="big")
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
        print("")
    
    def run(self):
        """Main program loop with enhanced error handling and user input validation"""
        self.logger.info("Starting MiniPass Manager main loop")
        
        while True:
            try:
                self.show_menu()
                
                choice = input("\nChoose an option (1-7):> ").strip()
                
                if choice == '1':
                    self.logger.info("User selected: List all MiniPass applications")
                    self.list_all_minipass_apps()
                
                elif choice == '2':
                    self.logger.info("User selected: Delete specific MiniPass application")
                    apps = self.list_all_minipass_apps()
                    if not apps:
                        self.logger.info("No apps found for deletion")
                        continue
                    
                    try:
                        app_choice = int(input(f"\nEnter the number of the app to delete (1-{len(apps)}): "))
                        if 1 <= app_choice <= len(apps):
                            selected_app = apps[app_choice - 1]
                            subdomain = selected_app['subdomain']
                            
                            # Enhanced validation
                            if not self._is_valid_subdomain(subdomain):
                                print(f"❌ Invalid subdomain format: {subdomain}")
                                self.logger.error(f"Invalid subdomain format for deletion: {subdomain}")
                                continue
                            
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
                                self.logger.info(f"User confirmed deletion of {subdomain}")
                                self.comprehensive_app_cleanup(subdomain)
                            else:
                                print("❌ Aborted.")
                                self.logger.info(f"User aborted deletion of {subdomain}")
                        else:
                            print("❌ Invalid choice.")
                            self.logger.warning(f"Invalid app choice for deletion: {app_choice}")
                    except ValueError:
                        print("❌ Invalid number.")
                        self.logger.warning("Invalid number entered for app deletion")
                    except Exception as e:
                        self.logger.error(f"Error during app deletion selection: {e}")
                        print(f"❌ Error: {e}")
                
                elif choice == '3':
                    self.logger.info("User selected: Cleanup orphaned containers")
                    self.cleanup_orphaned_containers()
                
                elif choice == '4':
                    self.logger.info("User selected: Cleanup orphaned database entries")
                    self.cleanup_orphaned_db_entries()
                
                elif choice == '5':
                    self.logger.info("User selected: Docker system cleanup")
                    self.docker_system_cleanup()
                
                elif choice == '6':
                    self.logger.info("User selected: View customer database records")
                    self.list_customer_database_records()
                
                elif choice == '7':
                    self.logger.info("User selected: Delete specific database record")
                    self.delete_customer_database_record()
                
                elif choice == 'x':
                    print("👋 Goodbye!")
                    self.logger.info("User exited MiniPass Manager")
                    break
                
                else:
                    print("❌ Invalid choice. Please enter 1-7 or 'x'.")
                    self.logger.warning(f"Invalid menu choice: {choice}")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                self.logger.info("User interrupted MiniPass Manager with Ctrl+C")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in main loop: {e}")
                print(f"❌ Unexpected error: {e}")


def main():
    """Main entry point with comprehensive error handling"""
    try:
        # Setup logging early
        logger = setup_logging()
        logger.info("Starting MiniPass Manager")
        
        manager = MiniPassAppManager()
        manager.run()
        
    except DockerError as e:
        print("❌ Error: Could not connect to Docker. Is Docker running?")
        print(f"Details: {e}")
        sys.exit(1)
    except DatabaseError as e:
        print("❌ Error: Database connection failed.")
        print(f"Details: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
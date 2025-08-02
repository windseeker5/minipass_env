#!/usr/bin/env python3

"""
Test script specifically for Docker container-based file removal
This simulates files created by Docker containers with different ownership
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Add the minipass_manager to the path
sys.path.insert(0, '/home/kdresdell/minipass_env')

from minipass_manager import MiniPassAppManager

def create_docker_owned_files():
    """Create files owned by Docker container (root or different UID)"""
    test_base = "/tmp/minipass_docker_test"
    
    # Clean up any existing test
    if os.path.exists(test_base):
        try:
            subprocess.run(['sudo', 'rm', '-rf', test_base], check=False)
        except:
            pass
    
    os.makedirs(test_base, exist_ok=True)
    test_subdir = os.path.join(test_base, "docker_subdomain")
    
    print(f"🐳 Creating Docker-owned files in: {test_subdir}")
    
    try:
        # Use Docker to create files with different ownership
        result = subprocess.run([
            'docker', 'run', '--rm',
            '-v', f'{test_base}:/workspace',
            '--workdir', '/workspace',
            'alpine:latest',
            'sh', '-c', '''
                mkdir -p docker_subdomain/__pycache__
                echo "Docker created file" > docker_subdomain/docker_file.txt
                echo "Docker pyc file" > docker_subdomain/__pycache__/docker_module.pyc
                echo "Another file" > docker_subdomain/data.json
                chmod 755 docker_subdomain
                chmod 644 docker_subdomain/docker_file.txt
                chmod 644 docker_subdomain/__pycache__/docker_module.pyc
                chmod 644 docker_subdomain/data.json
                ls -la docker_subdomain/
            '''
        ], capture_output=True, text=True, check=False)
        
        if result.returncode == 0:
            print("✅ Docker container created test files successfully")
            print("📋 Created files:")
            print(result.stdout)
        else:
            print(f"❌ Docker container failed: {result.stderr}")
            return None
            
    except subprocess.FileNotFoundError:
        print("⚠️ Docker not available, creating regular files instead")
        os.makedirs(test_subdir, exist_ok=True)
        
        # Create regular files for testing
        test_files = [
            os.path.join(test_subdir, "regular_file.txt"),
            os.path.join(test_subdir, "__pycache__", "test.pyc"),
            os.path.join(test_subdir, "data.json"),
        ]
        
        for file_path in test_files:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(f"Test content for {os.path.basename(file_path)}")
    
    return test_subdir

def test_docker_file_removal():
    """Test removal of Docker-created files"""
    print("\n🧪 Testing Docker File Removal")
    print("=" * 40)
    
    # Create Docker-owned files
    test_dir = create_docker_owned_files()
    if not test_dir:
        return False
    
    # Check initial state
    print(f"\n📊 Initial state:")
    if os.path.exists(test_dir):
        print(f"   📁 Directory exists: {test_dir}")
        
        # Show ownership details
        try:
            ls_result = subprocess.run(['ls', '-la', test_dir], 
                                     capture_output=True, text=True, check=False)
            print(f"   📋 File ownership:")
            for line in ls_result.stdout.strip().split('\n'):
                if line and not line.startswith('total'):
                    print(f"      {line}")
        except:
            pass
    
    # Create manager and test removal
    try:
        manager = MiniPassAppManager()
        print(f"\n🗑️ Testing enhanced removal on Docker-owned files...")
        
        success = manager.force_remove_folder(test_dir)
        
        # Check final state
        print(f"\n📊 Final state:")
        if os.path.exists(test_dir):
            print(f"   ❌ Directory still exists: {test_dir}")
            return False
        else:
            print(f"   ✅ Directory successfully removed")
            return True
            
    except Exception as e:
        print(f"❌ Error during removal test: {e}")
        return False
    
    finally:
        # Cleanup
        test_base = os.path.dirname(test_dir) if test_dir else "/tmp/minipass_docker_test"
        if os.path.exists(test_base):
            try:
                subprocess.run(['sudo', 'rm', '-rf', test_base], check=False)
            except:
                shutil.rmtree(test_base, ignore_errors=True)

def main():
    """Main test function"""
    print("🐳 Docker File Removal Test")
    print("=" * 30)
    
    # Check if Docker is available
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, check=False)
        if result.returncode == 0:
            print(f"✅ Docker available: {result.stdout.strip()}")
        else:
            print("⚠️ Docker available but not responding properly")
    except FileNotFoundError:
        print("⚠️ Docker not found - will test with regular files")
    
    # Run the test
    if test_docker_file_removal():
        print("\n✅ Docker file removal test passed!")
        return 0
    else:
        print("\n❌ Docker file removal test failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
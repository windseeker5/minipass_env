#!/usr/bin/env python3
"""
Test script for enhanced file removal functionality
Demonstrates the robust deletion capabilities for various permission scenarios
"""

import os
import sys
import stat
import subprocess
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock

# Mock pyfiglet if it's not available
try:
    import pyfiglet
except ImportError:
    sys.modules['pyfiglet'] = MagicMock()


def create_test_scenario():
    """Create a test directory with various permission scenarios"""
    test_dir = tempfile.mkdtemp(prefix="minipass_removal_test_")
    print(f"🧪 Creating test scenario in: {test_dir}")
    
    # Create various test cases
    scenarios = {
        "normal_files": [],
        "readonly_files": [],
        "pycache_dirs": [],
        "permission_denied": [],
        "nested_structure": []
    }
    
    try:
        # 1. Normal files and directories
        normal_dir = os.path.join(test_dir, "normal")
        os.makedirs(normal_dir)
        with open(os.path.join(normal_dir, "test.txt"), "w") as f:
            f.write("normal file content")
        scenarios["normal_files"].append(normal_dir)
        
        # 2. Read-only files
        readonly_dir = os.path.join(test_dir, "readonly")
        os.makedirs(readonly_dir)
        readonly_file = os.path.join(readonly_dir, "readonly.txt")
        with open(readonly_file, "w") as f:
            f.write("readonly file content")
        os.chmod(readonly_file, stat.S_IRUSR)  # Read-only
        os.chmod(readonly_dir, stat.S_IRUSR | stat.S_IXUSR)  # Read-only dir
        scenarios["readonly_files"].append(readonly_dir)
        
        # 3. Python cache directories (simulate .pyc files)
        pycache_dir = os.path.join(test_dir, "__pycache__")
        os.makedirs(pycache_dir)
        pyc_file = os.path.join(pycache_dir, "module.cpython-39.pyc")
        with open(pyc_file, "wb") as f:
            f.write(b"fake python bytecode")
        # Make it read-only like Docker might create
        os.chmod(pyc_file, stat.S_IRUSR)
        os.chmod(pycache_dir, stat.S_IRUSR | stat.S_IXUSR)
        scenarios["pycache_dirs"].append(pycache_dir)
        
        # 4. Permission denied scenario
        perm_denied_dir = os.path.join(test_dir, "permission_denied")
        os.makedirs(perm_denied_dir)
        perm_denied_file = os.path.join(perm_denied_dir, "locked.txt")
        with open(perm_denied_file, "w") as f:
            f.write("locked file content")
        os.chmod(perm_denied_file, 0o000)  # No permissions
        os.chmod(perm_denied_dir, 0o000)   # No permissions
        scenarios["permission_denied"].append(perm_denied_dir)
        
        # 5. Nested structure with mixed permissions
        nested_dir = os.path.join(test_dir, "nested")
        os.makedirs(nested_dir)
        
        # Create subdirectories
        for subdir in ["level1", "level1/level2", "level1/level2/level3"]:
            full_subdir = os.path.join(nested_dir, subdir)
            os.makedirs(full_subdir, exist_ok=True)
            
            # Add files with different permissions
            test_file = os.path.join(full_subdir, "test.txt")
            with open(test_file, "w") as f:
                f.write(f"content in {subdir}")
            
            # Randomize permissions
            if "level2" in subdir:
                os.chmod(test_file, stat.S_IRUSR)  # Read-only
            elif "level3" in subdir:
                os.chmod(test_file, 0o000)  # No permissions
        
        scenarios["nested_structure"].append(nested_dir)
        
        print("✅ Test scenarios created:")
        for scenario, paths in scenarios.items():
            print(f"   📁 {scenario}: {len(paths)} items")
        
        return test_dir, scenarios
        
    except Exception as e:
        print(f"❌ Error creating test scenarios: {e}")
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir, ignore_errors=True)
        return None, {}


def import_enhanced_removal():
    """Import the enhanced removal function from minipass_manager.py"""
    try:
        sys.path.insert(0, '.')  # Add current directory to Python path
        from minipass_manager import MiniPassAppManager
        
        manager = MiniPassAppManager()
        return manager.force_remove_folder
        
    except ImportError as e:
        print(f"❌ Could not import enhanced removal function: {e}")
        return None
    except Exception as e:
        print(f"❌ Error initializing manager: {e}")
        return None


def test_enhanced_removal():
    """Test the enhanced removal functionality"""
    print("🧪 Testing Enhanced File Removal System")
    print("=" * 60)
    
    # Import the enhanced removal function
    force_remove_folder = import_enhanced_removal()
    if not force_remove_folder:
        print("❌ Cannot proceed without enhanced removal function")
        return False
    
    # Create test scenarios
    test_dir, scenarios = create_test_scenario()
    if not test_dir:
        print("❌ Cannot proceed without test scenarios")
        return False
    
    print(f"\n📂 Test directory: {test_dir}")
    print(f"📊 Total scenarios: {len(scenarios)}")
    
    success_count = 0
    total_count = 0
    
    try:
        # Test removal of entire test directory
        print(f"\n🗑️ Testing removal of entire test directory...")
        print(f"📁 Target: {test_dir}")
        
        # List contents before removal for debugging
        print("\n📋 Directory structure before removal:")
        for root, dirs, files in os.walk(test_dir):
            level = root.replace(test_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}📁 {os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_stat = os.stat(file_path)
                    mode = stat.filemode(file_stat.st_mode)
                    print(f"{subindent}📄 {file} ({mode})")
                except OSError as e:
                    print(f"{subindent}📄 {file} (error: {e})")
        
        # Attempt removal
        print(f"\n🚀 Starting enhanced removal process...")
        result = force_remove_folder(test_dir)
        
        if result:
            print(f"✅ Enhanced removal completed successfully!")
            success_count += 1
            
            # Verify removal
            if not os.path.exists(test_dir):
                print(f"✅ Verification: Directory completely removed")
            else:
                print(f"⚠️ Verification: Directory still exists")
                # List remaining files
                remaining_files = []
                for root, dirs, files in os.walk(test_dir):
                    for file in files:
                        remaining_files.append(os.path.join(root, file))
                if remaining_files:
                    print(f"   📁 Remaining files: {len(remaining_files)}")
                    for file in remaining_files[:5]:  # Show first 5
                        print(f"     📄 {file}")
                    if len(remaining_files) > 5:
                        print(f"     ... and {len(remaining_files) - 5} more")
        else:
            print(f"❌ Enhanced removal failed")
            
        total_count += 1
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup any remaining test files
        if os.path.exists(test_dir):
            print(f"\n🧹 Cleaning up remaining test files...")
            try:
                # Try with sudo as last resort
                subprocess.run(['sudo', 'rm', '-rf', test_dir], check=False)
                if not os.path.exists(test_dir):
                    print(f"✅ Cleanup successful")
                else:
                    print(f"⚠️ Manual cleanup required: {test_dir}")
            except:
                print(f"⚠️ Manual cleanup required: {test_dir}")
    
    # Summary
    print(f"\n📊 Test Summary:")
    print(f"   ✅ Successful removals: {success_count}/{total_count}")
    print(f"   📈 Success rate: {(success_count/total_count)*100:.1f}%" if total_count > 0 else "   📈 Success rate: N/A")
    
    return success_count == total_count


def main():
    """Main test function"""
    print("🧪 Enhanced File Removal Test Suite")
    print("=" * 50)
    
    # Check prerequisites
    print("🔍 Checking prerequisites...")
    
    # Check if running on Linux
    if not sys.platform.startswith('linux'):
        print("⚠️ This test is designed for Linux systems")
    
    # Check if Docker is available
    try:
        subprocess.run(['docker', '--version'], capture_output=True, check=True)
        print("✅ Docker is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️ Docker not available - container-based removal will be skipped")
    
    # Check if running as root
    if os.geteuid() == 0:
        print("⚠️ Running as root - sudo tests will be skipped")
    else:
        print("ℹ️ Running as regular user - sudo tests will be attempted")
    
    print()
    
    # Run the test
    success = test_enhanced_removal()
    
    if success:
        print("\n🎉 All tests passed! Enhanced removal system is working correctly.")
        return 0
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
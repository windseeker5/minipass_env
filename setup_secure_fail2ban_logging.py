#!/home/kdresdell/minipass_env/MinipassWebSite/venv/bin/python
"""
Secure Fail2Ban Manager Logging Setup Script

This script sets up proper logging permissions and directories for the
secure_fail2ban_manager.py script.

Author: Python DevOps Automation Specialist
Created: 2025-08-02
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_logging_directories():
    """Setup logging directories with proper permissions"""
    
    print("🔧 Setting up Secure Fail2Ban Manager logging...")
    
    # Option 1: Try to set up system-wide logging (requires sudo)
    var_log_dir = Path("/var/log")
    system_log_file = var_log_dir / "secure_fail2ban_manager.log"
    
    if os.geteuid() == 0:
        print("⚠️ Running as root - setting up system-wide logging")
        try:
            # Create log file with proper permissions
            system_log_file.touch(mode=0o640, exist_ok=True)
            
            # Set ownership (root:adm is standard for system logs)
            subprocess.run(['chown', 'root:adm', str(system_log_file)], check=True)
            
            print(f"✅ Created system log: {system_log_file}")
            print("💡 Users in 'adm' group can read this log")
            return str(system_log_file)
            
        except Exception as e:
            print(f"❌ Failed to create system log: {e}")
    
    # Option 2: Set up user-space logging
    user_log_dir = Path.home() / ".local" / "log"
    user_log_dir.mkdir(parents=True, exist_ok=True)
    user_log_file = user_log_dir / "secure_fail2ban_manager.log"
    
    try:
        user_log_file.touch(mode=0o640, exist_ok=True)
        print(f"✅ Created user log: {user_log_file}")
        return str(user_log_file)
        
    except Exception as e:
        print(f"❌ Failed to create user log: {e}")
    
    # Option 3: Fall back to current working directory
    cwd_log_file = Path.cwd() / "secure_fail2ban_manager.log"
    try:
        cwd_log_file.touch(mode=0o640, exist_ok=True)
        print(f"✅ Created local log: {cwd_log_file}")
        return str(cwd_log_file)
        
    except Exception as e:
        print(f"❌ Failed to create local log: {e}")
        print("⚠️ Will fall back to console-only logging")
        return None

def check_fail2ban_permissions():
    """Check fail2ban permissions and suggest solutions"""
    
    print("\n🔍 Checking fail2ban permissions...")
    
    # Check if fail2ban-client exists
    fail2ban_client = "/usr/bin/fail2ban-client"
    if not Path(fail2ban_client).exists():
        print("❌ fail2ban-client not found")
        print("💡 Install with: sudo apt install fail2ban")
        return False
    
    # Check if user can run fail2ban commands with sudo
    try:
        result = subprocess.run(
            ['sudo', '-n', fail2ban_client, 'version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ Can execute fail2ban-client with sudo")
            print(f"📊 Fail2ban version: {result.stdout.strip()}")
            return True
        else:
            print("❌ Cannot execute fail2ban-client with sudo")
            print(f"Error: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("⏰ Timeout checking fail2ban permissions")
    except Exception as e:
        print(f"❌ Error checking fail2ban: {e}")
    
    print("💡 Ensure your user is in sudo group and can run commands without password prompts")
    print("💡 Configure sudo NOPASSWD for fail2ban commands if needed")
    return False

def create_sudoers_config():
    """Create a sudoers configuration for fail2ban commands"""
    
    username = os.getenv('USER', 'unknown')
    sudoers_content = f'''# Allow {username} to run fail2ban commands without password
{username} ALL=(ALL) NOPASSWD: /usr/bin/fail2ban-client
{username} ALL=(ALL) NOPASSWD: /bin/cat /var/log/fail2ban.log*
{username} ALL=(ALL) NOPASSWD: /bin/cat /var/log/mail.log*
{username} ALL=(ALL) NOPASSWD: /bin/cat /var/log/dovecot.log*
'''
    
    sudoers_file = f"/tmp/secure-fail2ban-{username}"
    
    try:
        with open(sudoers_file, 'w') as f:
            f.write(sudoers_content)
        
        print(f"\n💡 Optional: Create sudoers configuration for passwordless fail2ban access:")
        print(f"   sudo cp {sudoers_file} /etc/sudoers.d/secure-fail2ban-{username}")
        print(f"   sudo chmod 440 /etc/sudoers.d/secure-fail2ban-{username}")
        print(f"   sudo chown root:root /etc/sudoers.d/secure-fail2ban-{username}")
        print(f"\n⚠️ WARNING: Only do this if you understand the security implications")
        
        return sudoers_file
        
    except Exception as e:
        print(f"❌ Error creating sudoers config: {e}")
        return None

def main():
    """Main setup function"""
    
    print("🛡️ Secure Fail2Ban Manager Setup")
    print("=" * 50)
    
    # Setup logging
    log_file = setup_logging_directories()
    
    # Check fail2ban permissions
    fail2ban_ok = check_fail2ban_permissions()
    
    # Suggest sudoers configuration
    if not fail2ban_ok:
        sudoers_file = create_sudoers_config()
    
    print("\n📋 Setup Summary:")
    print(f"  🗂️ Log file: {log_file or 'Console only'}")
    print(f"  🔧 Fail2ban access: {'✅ Ready' if fail2ban_ok else '❌ Needs configuration'}")
    
    if log_file:
        print(f"\n✅ Run the script with:")
        print(f"   ./secure_fail2ban_manager.py")
        print(f"\n📝 Logs will be written to: {log_file}")
    else:
        print(f"\n⚠️ Script will use console-only logging")
        print(f"   ./secure_fail2ban_manager.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
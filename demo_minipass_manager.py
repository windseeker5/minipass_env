#!/usr/bin/env python3

"""
Demo of MiniPass Manager Enhanced Removal Functionality
This script demonstrates the enhanced file removal capabilities without running the full interactive menu.
"""

import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/kdresdell/minipass_env/minipass_demo.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Add the minipass_manager to the path
sys.path.insert(0, '/home/kdresdell/minipass_env')

try:
    from minipass_manager import MiniPassAppManager
    logging.info("✅ Successfully imported MiniPassAppManager")
except ImportError as e:
    logging.error(f"❌ Failed to import MiniPassAppManager: {e}")
    sys.exit(1)

def demo_list_applications():
    """Demonstrate listing all MiniPass applications"""
    print("\n" + "="*60)
    print("🔍 DEMO: Listing All MiniPass Applications")
    print("="*60)
    
    try:
        manager = MiniPassAppManager()
        apps = manager.list_all_minipass_apps()
        
        if apps:
            print(f"\n📊 Found {len(apps)} applications")
            for app in apps:
                subdomain = app['subdomain']
                has_container = "✅" if app['container'] else "❌"
                has_image = "✅" if app['image'] else "❌"
                has_db = "✅" if app['db_entry'] else "❌"
                
                print(f"   📦 {subdomain}: Container:{has_container} Image:{has_image} DB:{has_db}")
        else:
            print("ℹ️ No MiniPass applications found")
            
    except Exception as e:
        logging.error(f"Error listing applications: {e}")

def demo_enhanced_removal():
    """Demonstrate the enhanced removal capabilities"""
    print("\n" + "="*60)
    print("🧹 DEMO: Enhanced Removal Capabilities")
    print("="*60)
    
    print("This demo shows the multiple removal strategies available:")
    print("   1. 🔧 Standard removal (shutil.rmtree)")
    print("   2. 🔐 Permission-based removal (chmod + retry)")
    print("   3. 🔓 Attribute-based removal (chattr + retry)")
    print("   4. 🐳 Container-based removal (Docker alpine)")
    print("   5. 🔐 Sudo-based removal (if available)")
    print("   6. 🔍 Process-based removal (lsof + kill)")
    
    print("\n📋 Key Features:")
    print("   • Handles Python bytecode files (.pyc)")
    print("   • Manages Docker container ownership issues")
    print("   • Removes immutable file attributes")
    print("   • Detailed logging and progress reporting")
    print("   • Graceful fallback between strategies")
    
def demo_customer_database():
    """Demonstrate customer database operations"""
    print("\n" + "="*60)
    print("🗄️ DEMO: Customer Database Operations")
    print("="*60)
    
    try:
        manager = MiniPassAppManager()
        customers = manager.get_customers_from_db()
        
        if customers:
            print(f"📊 Found {len(customers)} customer records")
            for subdomain, info in list(customers.items())[:3]:  # Show first 3
                print(f"   👤 {subdomain}: {info['email']} ({info['plan']})")
            if len(customers) > 3:
                print(f"   ... and {len(customers) - 3} more")
        else:
            print("ℹ️ No customer records found")
            
    except Exception as e:
        logging.error(f"Error accessing customer database: {e}")

def demo_docker_operations():
    """Demonstrate Docker operations"""
    print("\n" + "="*60)
    print("🐳 DEMO: Docker Operations")
    print("="*60)
    
    try:
        manager = MiniPassAppManager()
        
        # Get containers
        containers = manager.get_minipass_containers()
        print(f"📦 MiniPass Containers: {len(containers)}")
        
        # Get images
        images = manager.get_minipass_images()
        print(f"🖼️ MiniPass Images: {len(images)}")
        
        if containers:
            print("   📋 Container Summary:")
            for container in containers[:3]:
                status = container['status']
                memory = container.get('memory_usage', 'N/A')
                print(f"      • {container['name']}: {status} ({memory})")
                
    except Exception as e:
        logging.error(f"Error with Docker operations: {e}")

def main():
    """Main demo function"""
    print("🚀 MiniPass Manager Enhanced Functionality Demo")
    print("=" * 60)
    print(f"📅 Demo run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💻 Running in: /home/kdresdell/minipass_env")
    print(f"🐍 Python version: {sys.version.split()[0]}")
    
    # Demonstrate various features
    demo_list_applications()
    demo_enhanced_removal()
    demo_customer_database()
    demo_docker_operations()
    
    print("\n" + "="*60)
    print("✅ DEMO COMPLETED SUCCESSFULLY")
    print("="*60)
    print("🔧 The enhanced MiniPass Manager includes:")
    print("   • Multi-strategy file removal for permission issues")
    print("   • Docker container-based cleanup for ownership problems")
    print("   • Python bytecode file handling")
    print("   • Comprehensive error handling and logging")
    print("   • Email account integration cleanup")
    print("   • Database record management")
    print("")
    print("📁 Log file: /home/kdresdell/minipass_env/minipass_demo.log")
    print("🔗 To run the full interactive manager:")
    print("   cd /home/kdresdell/minipass_env")
    print("   source MinipassWebSite/venv/bin/activate")
    print("   python minipass_manager.py")

if __name__ == "__main__":
    main()
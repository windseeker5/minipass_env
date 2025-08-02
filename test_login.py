#!/usr/bin/env python3

import requests
import re
from urllib.parse import urljoin

def test_login():
    base_url = "https://kiteguru.minipass.me"
    email = "kdresdell@gmail.com"
    password = "ci_wp6drHtsa1G5T"
    
    print(f"🧪 Testing login to {base_url}")
    print(f"📧 Email: {email}")
    print(f"🔐 Password: {password}")
    print("=" * 60)
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    try:
        # Step 1: Get the login page to extract CSRF token
        print("1️⃣ Getting login page...")
        login_url = urljoin(base_url, "/login")
        response = session.get(login_url, timeout=30)
        
        print(f"   Status: {response.status_code}")
        print(f"   URL: {response.url}")
        
        if response.status_code != 200:
            print(f"❌ Failed to get login page: {response.status_code}")
            return
        
        # Look for CSRF token in the form
        csrf_token = None
        csrf_match = re.search(r'name="csrf_token".*?value="([^"]+)"', response.text)
        if csrf_match:
            csrf_token = csrf_match.group(1)
            print(f"   ✅ Found CSRF token: {csrf_token[:20]}...")
        else:
            print("   ⚠️ No CSRF token found")
        
        # Step 2: Submit login form
        print("\n2️⃣ Submitting login form...")
        login_data = {
            'email': email,
            'password': password
        }
        
        if csrf_token:
            login_data['csrf_token'] = csrf_token
        
        response = session.post(login_url, data=login_data, timeout=30, allow_redirects=False)
        
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 302:
            # Successful login should redirect
            redirect_location = response.headers.get('Location', '')
            print(f"   ✅ Redirected to: {redirect_location}")
            
            # Follow the redirect
            if redirect_location:
                print("\n3️⃣ Following redirect...")
                if redirect_location.startswith('/'):
                    redirect_url = urljoin(base_url, redirect_location)
                else:
                    redirect_url = redirect_location
                
                response = session.get(redirect_url, timeout=30)
                print(f"   Status: {response.status_code}")
                print(f"   URL: {response.url}")
                
                if 'login' in response.url:
                    print("   ❌ Redirected back to login - authentication failed")
                    # Check for error messages
                    if 'Invalid email or password' in response.text:
                        print("   🔍 Found 'Invalid email or password' message")
                    elif 'error' in response.text.lower():
                        print("   🔍 Found error message in response")
                else:
                    print("   ✅ Successfully logged in!")
                    return True
        
        elif response.status_code == 200:
            # Check if we're still on login page (failed login)
            if 'login' in response.url or 'Invalid' in response.text:
                print("   ❌ Login failed - still on login page")
                # Look for error messages
                if 'Invalid email or password' in response.text:
                    print("   🔍 Error: Invalid email or password")
                elif 'required' in response.text.lower():
                    print("   🔍 Error: Required field missing")
                else:
                    print("   🔍 Check response for error messages")
            else:
                print("   ✅ Login successful (no redirect)")
                return True
        else:
            print(f"   ❌ Unexpected status code: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out - server may be slow or unresponsive")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - server may be down")
    except Exception as e:
        print(f"❌ Error during login test: {str(e)}")
    
    return False

def test_container_health():
    print("\n🏥 Container Health Check")
    print("=" * 60)
    
    # Check if container is running
    import subprocess
    
    try:
        result = subprocess.run([
            "docker", "ps", "--filter", "name=minipass_kiteguru", 
            "--format", "{{.Names}}\t{{.Status}}\t{{.Ports}}"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and result.stdout.strip():
            print(f"✅ Container status: {result.stdout.strip()}")
        else:
            print("❌ Container not found or not running")
            return False
            
        # Test if the container responds to HTTP internally
        result = subprocess.run([
            "docker", "exec", "minipass_kiteguru", 
            "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "http://localhost:5000/"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            status_code = result.stdout.strip()
            print(f"✅ Internal HTTP response: {status_code}")
            if status_code in ['200', '302']:
                print("✅ Container is responding correctly")
                return True
            else:
                print(f"⚠️ Unexpected HTTP status: {status_code}")
        else:
            print("❌ Failed to test internal HTTP response")
            
    except Exception as e:
        print(f"❌ Error checking container health: {str(e)}")
    
    return False

if __name__ == "__main__":
    print("🔐 MiniPass Login Tester")
    print("=" * 60)
    
    # Test container health first
    container_healthy = test_container_health()
    
    if container_healthy:
        # Test login
        login_success = test_login()
        
        print("\n" + "=" * 60)
        if login_success:
            print("🎉 LOGIN TEST PASSED")
            print("💡 The login system is working correctly")
        else:
            print("❌ LOGIN TEST FAILED")
            print("💡 There may be an issue with authentication logic")
            print("🔍 Check container logs: docker logs minipass_kiteguru")
            print("🔍 Check application configuration inside container")
    else:
        print("\n❌ Container health check failed")
        print("💡 Container may not be responding correctly")
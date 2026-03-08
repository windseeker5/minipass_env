#!/usr/bin/env python3
"""
Mail Connectivity Test Script
Tests SMTP connectivity to mail.minipass.me from different contexts
"""

import smtplib
import socket
import sys
import json
from datetime import datetime

def test_smtp_connection(host, port, timeout=10, use_starttls=True, test_auth=False, username=None, password=None):
    """Test SMTP connection and return detailed results."""
    result = {
        'host': host,
        'port': port,
        'timestamp': datetime.now().isoformat(),
        'success': False,
        'steps': {},
        'error': None
    }

    try:
        # Step 1: DNS Resolution
        try:
            ip = socket.gethostbyname(host)
            result['steps']['dns_resolution'] = {'success': True, 'ip': ip}
            print(f"✅ DNS: {host} → {ip}")
        except Exception as e:
            result['steps']['dns_resolution'] = {'success': False, 'error': str(e)}
            print(f"❌ DNS: Failed to resolve {host} - {e}")
            result['error'] = f"DNS resolution failed: {e}"
            return result

        # Step 2: TCP Connection
        try:
            server = smtplib.SMTP(host, port, timeout=timeout)
            result['steps']['tcp_connection'] = {'success': True}
            print(f"✅ TCP: Connected to {host}:{port}")
        except Exception as e:
            result['steps']['tcp_connection'] = {'success': False, 'error': str(e)}
            print(f"❌ TCP: Failed to connect to {host}:{port} - {e}")
            result['error'] = f"TCP connection failed: {e}"
            return result

        # Step 3: SMTP Greeting
        try:
            greeting = server.ehlo()
            result['steps']['smtp_greeting'] = {'success': True, 'response': str(greeting)}
            print(f"✅ SMTP: Server greeting received")
        except Exception as e:
            result['steps']['smtp_greeting'] = {'success': False, 'error': str(e)}
            print(f"❌ SMTP: Greeting failed - {e}")
            result['error'] = f"SMTP greeting failed: {e}"
            server.quit()
            return result

        # Step 4: STARTTLS (if requested)
        if use_starttls:
            try:
                server.starttls()
                result['steps']['starttls'] = {'success': True}
                print(f"✅ TLS: STARTTLS successful")
            except Exception as e:
                result['steps']['starttls'] = {'success': False, 'error': str(e)}
                print(f"❌ TLS: STARTTLS failed - {e}")
                result['error'] = f"STARTTLS failed: {e}"
                server.quit()
                return result

        # Step 5: Authentication (if requested)
        if test_auth and username and password:
            try:
                server.login(username, password)
                result['steps']['authentication'] = {'success': True}
                print(f"✅ AUTH: Login successful")
            except Exception as e:
                result['steps']['authentication'] = {'success': False, 'error': str(e)}
                print(f"❌ AUTH: Login failed - {e}")
                result['error'] = f"Authentication failed: {e}"
                server.quit()
                return result

        # Clean close
        try:
            server.quit()
            result['steps']['clean_close'] = {'success': True}
            print(f"✅ CLOSE: Clean disconnect")
        except Exception as e:
            result['steps']['clean_close'] = {'success': False, 'error': str(e)}
            print(f"⚠️ CLOSE: Disconnect warning - {e}")

        result['success'] = True
        return result

    except Exception as e:
        result['error'] = f"Unexpected error: {e}"
        print(f"❌ FATAL: {e}")
        return result

def test_mail_connectivity():
    """Run comprehensive mail connectivity tests."""
    print("=" * 60)
    print("Mail Connectivity Test")
    print("=" * 60)

    # Test configurations
    tests = [
        {
            'name': 'Basic SMTP Connection',
            'host': 'mail.minipass.me',
            'port': 587,
            'use_starttls': False,
            'test_auth': False
        },
        {
            'name': 'SMTP with STARTTLS',
            'host': 'mail.minipass.me',
            'port': 587,
            'use_starttls': True,
            'test_auth': False
        },
        {
            'name': 'IMAPS Connection',
            'host': 'mail.minipass.me',
            'port': 993,
            'use_starttls': False,
            'test_auth': False
        },
        {
            'name': 'IMAP Connection',
            'host': 'mail.minipass.me',
            'port': 143,
            'use_starttls': False,
            'test_auth': False
        }
    ]

    results = []

    for test_config in tests:
        print(f"\n--- {test_config['name']} ---")

        # For IMAP tests, use socket test instead of smtplib
        if test_config['port'] in [143, 993]:
            result = test_socket_connection(
                test_config['host'],
                test_config['port']
            )
        else:
            result = test_smtp_connection(
                test_config['host'],
                test_config['port'],
                use_starttls=test_config['use_starttls'],
                test_auth=test_config['test_auth']
            )

        results.append({
            'test': test_config['name'],
            'result': result
        })

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = True
    for test_result in results:
        status = "✅ PASS" if test_result['result']['success'] else "❌ FAIL"
        print(f"{status} {test_result['test']}")
        if not test_result['result']['success']:
            print(f"     Error: {test_result['result']['error']}")
            all_passed = False

    print(f"\nOverall Status: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")

    # Write detailed results to file
    with open('/tmp/mail_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to: /tmp/mail_test_results.json")

    return all_passed

def test_socket_connection(host, port, timeout=10):
    """Test basic socket connection (for IMAP ports)."""
    result = {
        'host': host,
        'port': port,
        'timestamp': datetime.now().isoformat(),
        'success': False,
        'steps': {},
        'error': None
    }

    try:
        # DNS Resolution
        try:
            ip = socket.gethostbyname(host)
            result['steps']['dns_resolution'] = {'success': True, 'ip': ip}
            print(f"✅ DNS: {host} → {ip}")
        except Exception as e:
            result['steps']['dns_resolution'] = {'success': False, 'error': str(e)}
            print(f"❌ DNS: Failed to resolve {host} - {e}")
            result['error'] = f"DNS resolution failed: {e}"
            return result

        # Socket Connection
        try:
            sock = socket.create_connection((host, port), timeout)
            result['steps']['socket_connection'] = {'success': True}
            print(f"✅ Socket: Connected to {host}:{port}")
            sock.close()
            result['success'] = True
        except Exception as e:
            result['steps']['socket_connection'] = {'success': False, 'error': str(e)}
            print(f"❌ Socket: Failed to connect to {host}:{port} - {e}")
            result['error'] = f"Socket connection failed: {e}"

    except Exception as e:
        result['error'] = f"Unexpected error: {e}"
        print(f"❌ FATAL: {e}")

    return result

if __name__ == "__main__":
    # Check if running in container
    try:
        with open('/proc/1/cgroup', 'r') as f:
            if 'docker' in f.read() or 'containerd' in f.read():
                print("🐳 Running inside Docker container")
            else:
                print("🖥️  Running on host system")
    except:
        print("🤷 Could not determine execution context")

    success = test_mail_connectivity()
    sys.exit(0 if success else 1)
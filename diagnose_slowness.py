#!/usr/bin/env python3
"""
VPS Slowness Diagnostic Tool
Run this on your VPS: python3 diagnose_slowness.py
"""

import subprocess
import time
import sys

def run_cmd(cmd):
    """Run a command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", -1

def test_url(name, cmd):
    """Test a URL and return time taken"""
    print(f"  Testing {name}...", end=" ", flush=True)
    start = time.time()
    stdout, stderr, code = run_cmd(cmd)
    elapsed = time.time() - start

    if code == 0:
        print(f"{elapsed:.2f}s")
        return elapsed
    else:
        print(f"FAILED ({stderr[:50]})")
        return -1

def main():
    print("=" * 50)
    print("VPS SLOWNESS DIAGNOSTIC")
    print("=" * 50)
    print()

    results = {}

    # Test 1: External internet
    print("[1] EXTERNAL INTERNET")
    results['google'] = test_url("Google", "curl -s -o /dev/null -w '%{time_total}' https://google.com")
    print()

    # Test 2: Flask app directly (bypass nginx)
    print("[2] FLASK APP DIRECT (bypass nginx)")
    results['flask_lhgi'] = test_url("lhgi:8889", "curl -s -o /dev/null -w '%{time_total}' http://localhost:8889/")
    results['flask_heq'] = test_url("heq:8890", "curl -s -o /dev/null -w '%{time_total}' http://localhost:8890/")
    print()

    # Test 3: Through nginx
    print("[3] THROUGH NGINX")
    results['nginx_lhgi'] = test_url("lhgi via nginx", "curl -s -o /dev/null -w '%{time_total}' -H 'Host: lhgi.minipass.me' http://localhost/")
    results['nginx_heq'] = test_url("heq via nginx", "curl -s -o /dev/null -w '%{time_total}' -H 'Host: heq.minipass.me' http://localhost/")
    print()

    # Test 4: Static file
    print("[4] STATIC FILE TEST")
    results['static'] = test_url("static CSS", "curl -s -o /dev/null -w '%{time_total}' http://localhost:8889/static/minipass.css")
    print()

    # Test 5: DNS resolution
    print("[5] DNS RESOLUTION")
    results['dns'] = test_url("DNS lookup", "dig +short lhgi.minipass.me | head -1 && echo")
    print()

    # Summary
    print("=" * 50)
    print("DIAGNOSIS")
    print("=" * 50)

    issues = []

    # Analyze results
    if results.get('google', 0) > 2:
        issues.append("- INTERNET: Slow external connectivity (hosting provider issue?)")

    if results.get('flask_lhgi', 0) > 1:
        issues.append("- FLASK APP: Direct Flask access is slow (code/database issue)")
    elif results.get('nginx_lhgi', 0) > 1 and results.get('flask_lhgi', 0) < 1:
        issues.append("- NGINX: Nginx is causing delay (proxy config issue)")

    if results.get('static', 0) > 1:
        issues.append("- STATIC FILES: Static files slow (disk I/O issue)")

    if not issues:
        if all(v < 1 for v in results.values() if isinstance(v, float) and v > 0):
            issues.append("+ SERVER IS FAST - Problem is likely browser cache or service worker")
            issues.append("  Clear browser data and try again")

    if issues:
        for issue in issues:
            print(issue)
    else:
        print("Could not determine issue from tests")

    print()
    print("Raw times:", {k: f"{v:.2f}s" if isinstance(v, float) and v > 0 else v for k, v in results.items()})

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Credential scanner — searches the entire minipass codebase for hardcoded
passwords, API keys, and secrets that should never be in source code.

Usage:
    python3 scan_credentials.py
    python3 scan_credentials.py --path /home/kdresdell/minipass_env

Run this periodically (weekly) or before any git push.
"""

import os
import re
import sys
import argparse
from pathlib import Path

# Directories to scan
DEFAULT_SCAN_PATHS = [
    "/home/kdresdell/Documents/DEV/minipass_env",
    "/home/kdresdell/Documents/DEV/minipass_env/MinipassWebSite",
]

# File extensions to scan
SCAN_EXTENSIONS = {".py", ".js", ".ts", ".sh", ".env", ".conf", ".yml", ".yaml", ".json", ".html"}

# Directories to always skip
SKIP_DIRS = {
    "venv", "__pycache__", ".git", "node_modules", ".cache",
    "site-packages", "dist", "build", ".npm", ".oh-my-zsh",
    "maildata", "customer_backups", "migrations",
}

# Files to always skip
SKIP_FILES = {
    "scan_credentials.py",  # this script itself
    "package-lock.json",
    "yarn.lock",
}

# Patterns that indicate a hardcoded credential
# Each tuple: (regex_pattern, description, severity)
CREDENTIAL_PATTERNS = [
    # Direct assignment of password-like values
    (r'(?i)(password|passwd|pass|pwd)\s*=\s*["\'][^"\'${\s]{4,}["\']', "Hardcoded password", "HIGH"),
    (r'(?i)(mail_pass|smtp_pass|imap_pass)\s*=\s*["\'][^"\'${\s]{4,}["\']', "Hardcoded mail password", "HIGH"),
    (r'(?i)(secret_key|secret)\s*=\s*["\'][^"\'${\s]{8,}["\']', "Hardcoded secret key", "HIGH"),
    (r'(?i)(api_key|apikey|api_secret)\s*=\s*["\'][^"\'${\s]{8,}["\']', "Hardcoded API key", "HIGH"),
    (r'(?i)(token|auth_token|access_token)\s*=\s*["\'][^"\'${\s]{8,}["\']', "Hardcoded token", "HIGH"),

    # Known service key formats
    (r'sk_live_[a-zA-Z0-9]{20,}', "Stripe LIVE secret key", "CRITICAL"),
    (r'sk_test_[a-zA-Z0-9]{20,}', "Stripe test secret key", "MEDIUM"),
    (r'whsec_[a-zA-Z0-9]{20,}', "Stripe webhook secret", "HIGH"),
    (r'AKIA[0-9A-Z]{16}', "AWS Access Key ID", "CRITICAL"),
    (r'(?i)github_token\s*=\s*["\'][a-zA-Z0-9_]{20,}["\']', "GitHub token", "CRITICAL"),
    (r'ghp_[a-zA-Z0-9]{36}', "GitHub personal access token", "CRITICAL"),

    # Neomutt / mail config with literal passwords
    (r'set\s+(imap_pass|smtp_pass)\s*=\s*"[^"${\s]{4,}"', "Hardcoded mail password in neomutt config", "HIGH"),
]

# Lines containing these strings are likely safe (false positive suppression)
SAFE_INDICATORS = [
    "os.environ",
    "os.getenv",
    "get_setting(",
    "getenv(",
    "environ.get(",
    "# example",
    "# placeholder",
    "# your_",
    "YOUR_PASSWORD",
    "your_password",
    "<password>",
    "CHANGE_ME",
    "example.com",
    "monsterinc00",   # known rotated password — already compromised, flag it anyway
]


def should_skip_dir(dirname):
    return dirname in SKIP_DIRS or dirname.startswith(".")


def should_skip_file(filename):
    if filename in SKIP_FILES:
        return True
    # Skip compiled/binary files
    if filename.endswith((".pyc", ".pyo", ".so", ".db", ".sqlite", ".log", ".gz", ".zip")):
        return True
    return False


def scan_file(filepath):
    findings = []
    try:
        content = Path(filepath).read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()
        for lineno, line in enumerate(lines, 1):
            # Skip commented-out lines
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//"):
                continue
            for pattern, description, severity in CREDENTIAL_PATTERNS:
                if re.search(pattern, line):
                    findings.append({
                        "file": filepath,
                        "line": lineno,
                        "content": line.strip()[:120],
                        "description": description,
                        "severity": severity,
                    })
                    break  # one finding per line is enough
    except Exception:
        pass
    return findings


def scan_path(root_path):
    all_findings = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Prune skipped directories in-place
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]

        for filename in filenames:
            if should_skip_file(filename):
                continue
            ext = Path(filename).suffix.lower()
            if ext not in SCAN_EXTENSIONS and not filename.endswith((".conf", ".cfg")):
                continue
            filepath = os.path.join(dirpath, filename)
            findings = scan_file(filepath)
            all_findings.extend(findings)
    return all_findings


def main():
    parser = argparse.ArgumentParser(description="Scan codebase for hardcoded credentials")
    parser.add_argument("--path", nargs="+", default=DEFAULT_SCAN_PATHS, help="Paths to scan")
    args = parser.parse_args()

    print("=" * 70)
    print("  CREDENTIAL SCANNER")
    print("=" * 70)

    all_findings = []
    for path in args.path:
        if os.path.exists(path):
            print(f"\nScanning: {path}")
            findings = scan_path(path)
            all_findings.extend(findings)
        else:
            print(f"WARNING: Path not found: {path}")

    if not all_findings:
        print("\n✅  No hardcoded credentials found.")
        sys.exit(0)

    # Group by severity
    critical = [f for f in all_findings if f["severity"] == "CRITICAL"]
    high     = [f for f in all_findings if f["severity"] == "HIGH"]
    medium   = [f for f in all_findings if f["severity"] == "MEDIUM"]

    print(f"\n{'=' * 70}")
    print(f"  RESULTS: {len(all_findings)} potential credential(s) found")
    print(f"  CRITICAL: {len(critical)}  HIGH: {len(high)}  MEDIUM: {len(medium)}")
    print(f"{'=' * 70}\n")

    for severity, findings in [("CRITICAL", critical), ("HIGH", high), ("MEDIUM", medium)]:
        if not findings:
            continue
        print(f"[{severity}]")
        for f in findings:
            print(f"  File    : {f['file']}:{f['line']}")
            print(f"  Type    : {f['description']}")
            print(f"  Content : {f['content']}")
            print()

    print("Review each finding. If it is a real credential, rotate it immediately")
    print("and replace it with an environment variable.")
    sys.exit(1)


if __name__ == "__main__":
    main()

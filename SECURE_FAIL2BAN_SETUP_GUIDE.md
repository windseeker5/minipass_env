# Secure Fail2Ban Manager - Setup and Troubleshooting Guide

## Overview

The `secure_fail2ban_manager.py` script is a security-hardened fail2ban management tool with enhanced email monitoring capabilities. This guide addresses common permission issues and provides setup instructions.

## Permission Issues and Solutions

### Problem: Permission Denied on Log File

**Error**: `❌ Fatal error: [Errno 13] Permission denied: '/var/log/secure_fail2ban_manager.log'`

**Root Cause**: Regular users cannot write to `/var/log/` directory.

### Solutions Applied

#### 1. Updated Script Location
- **Fixed**: Changed default log location from `/var/log/` to user home directory
- **File**: `secure_fail2ban_manager.py` line 78
- **New Location**: `/home/kdresdell/minipass_env/secure_fail2ban_manager.log`

#### 2. Enhanced Error Handling
- **Added**: Graceful fallback to console-only logging if file creation fails
- **Benefit**: Script continues to work even with permission issues

#### 3. Updated Shebang
- **Fixed**: Updated shebang to use virtual environment Python
- **From**: `#!/usr/bin/env python3`
- **To**: `#!/home/kdresdell/minipass_env/MinipassWebSite/venv/bin/python`

## Running the Script

### Method 1: Direct Execution (Recommended)
```bash
cd /home/kdresdell/minipass_env
./secure_fail2ban_manager.py
```

### Method 2: With Virtual Environment
```bash
cd /home/kdresdell/minipass_env
source MinipassWebSite/venv/bin/activate
python3 secure_fail2ban_manager.py
```

### Method 3: With System-wide Logging (Requires Sudo)
```bash
# If you want system-wide logging in /var/log/
sudo ./secure_fail2ban_manager.py
```

## Setup Script

Run the setup script to configure logging and check permissions:
```bash
./setup_secure_fail2ban_logging.py
```

## File Permissions Reference

### Script Files
```bash
-rwxrwxr-x  secure_fail2ban_manager.py      # Executable
-rwxrwxr-x  setup_secure_fail2ban_logging.py # Executable
```

### Log Files
```bash
# User log (recommended)
-rw-r-----  /home/kdresdell/minipass_env/secure_fail2ban_manager.log

# System log (requires sudo)
-rw-r-----  /var/log/secure_fail2ban_manager.log (root:adm)
```

## Troubleshooting

### Issue: "Module not found" errors
**Solution**: Ensure you're using the virtual environment:
```bash
source /home/kdresdell/minipass_env/MinipassWebSite/venv/bin/activate
pip install pyfiglet  # if missing
```

### Issue: "fail2ban-client not found"
**Solution**: Install fail2ban:
```bash
sudo apt update
sudo apt install fail2ban
```

### Issue: "sudo password required"
**Solution**: Configure passwordless sudo for fail2ban (optional):
```bash
# Create sudoers file (use setup script for template)
sudo visudo -f /etc/sudoers.d/secure-fail2ban-$(whoami)
```

### Issue: Script hangs or times out
**Solution**: Check fail2ban service status:
```bash
sudo systemctl status fail2ban
sudo systemctl start fail2ban  # if stopped
```

## Security Considerations

### File Permissions
- Log files: `640` (owner read/write, group read)
- Script files: `755` (owner read/write/execute, group/others read/execute)

### Sudo Access
- Script requires sudo access for fail2ban operations
- Consider using sudoers.d configuration for specific commands only
- Never run the entire script as root

### Logging
- All operations are logged with session tracking
- Rate limiting prevents abuse
- Input validation prevents injection attacks

## Alternative Log Locations

If the default location doesn't work, the script will try:

1. **User home**: `/home/kdresdell/minipass_env/secure_fail2ban_manager.log`
2. **User local**: `~/.local/log/secure_fail2ban_manager.log`
3. **Current directory**: `./secure_fail2ban_manager.log`
4. **Console only**: If all file options fail

## Performance Notes

- Script includes rate limiting for security
- Log parsing is limited to prevent memory exhaustion
- Timeouts prevent hanging operations

## Support

For additional issues:
1. Check script output for specific error messages
2. Verify fail2ban installation and status
3. Check user group membership (`groups` command)
4. Review system logs (`journalctl -u fail2ban`)
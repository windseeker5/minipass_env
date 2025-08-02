# Secure Fail2Ban Manager Installation Guide

## Overview

The Secure Fail2Ban Manager installer now supports two installation modes:

1. **Full System Installation** - Requires sudo privileges, installs system-wide
2. **User-Space Installation** - No sudo required, limited functionality

## Quick Start

```bash
# Check what mode you'll get
python3 install_secure_fail2ban.py --dry-run --install

# Run the installation
python3 install_secure_fail2ban.py --install
```

## Installation Modes

### 🏠 User-Space Installation Mode

**When this mode is used:**
- User does not have sudo privileges
- Running on a system where you can't get admin access
- Want to test basic functionality

**What gets installed:**
- Manager script in `~/.local/bin/secure-fail2ban-manager`
- User-specific audit logs in `~/.local/var/log/`
- Wrapper script for easy execution
- Manual setup instructions for system administrator

**Limitations:**
- Cannot modify system fail2ban configuration
- Cannot install/reload fail2ban jails and filters
- Read-only monitoring capabilities
- Requires manual setup by system administrator for full functionality

**Post-installation steps:**
```bash
# Add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Run the manager
secure-fail2ban-manager
```

### ✅ Full System Installation Mode

**When this mode is used:**
- User has sudo privileges
- Can make system-wide changes
- Want full fail2ban management capabilities

**What gets installed:**
- System-wide manager script in `/usr/local/bin/`
- fail2ban-managers group creation
- User added to fail2ban-managers group
- Sudoers configuration with restricted access
- Email security jails and filters
- System audit logging
- Complete fail2ban integration

**Post-installation steps:**
```bash
# Log out and back in for group changes
# Then run the manager
secure-fail2ban-manager
```

## Getting Sudo Access

If you're in user-space mode but want full functionality, you need sudo privileges. Here are common scenarios:

### Personal Server/VPS
```bash
# If you're the server owner, add sudo privileges
su -
usermod -aG sudo your_username
```

### Corporate/Shared Environment
Contact your system administrator and provide them with the manual setup instructions from the installation output.

### Ubuntu/Debian Systems
```bash
# System administrator can grant sudo access
sudo usermod -aG sudo username
```

## Manual Setup for System Administrators

If a user has run the user-space installation, system administrators can complete the setup:

### 1. Install fail2ban
```bash
sudo apt-get update
sudo apt-get install fail2ban
```

### 2. Create group and add user
```bash
sudo groupadd fail2ban-managers
sudo usermod -a -G fail2ban-managers USERNAME
```

### 3. Install configuration files
From the user's installation directory (usually `/home/USERNAME/minipass_env/`):

```bash
# Copy jail configuration
sudo cp email-security.conf /etc/fail2ban/jail.d/

# Copy sudoers configuration  
sudo cp secure-fail2ban-sudoers /etc/sudoers.d/secure-fail2ban
sudo chmod 440 /etc/sudoers.d/secure-fail2ban

# Install filters (if email-filters.conf exists)
sudo cp email-filters.conf /etc/fail2ban/filter.d/
```

### 4. Restart fail2ban
```bash
sudo systemctl restart fail2ban
sudo systemctl status fail2ban
```

### 5. Test configuration
```bash
sudo fail2ban-client status
```

## Troubleshooting

### "User does not have sudo privileges" Error

**Solution 1: Get sudo access**
```bash
# Contact system administrator or if you have root access:
su -
usermod -aG sudo your_username
# Log out and back in
```

**Solution 2: Use user-space mode**
The installer will automatically switch to user-space mode. This provides basic functionality.

### "fail2ban is not installed" Error

**For full installation:**
```bash
sudo apt-get install fail2ban
```

**For user-space installation:**
This error is skipped - the installer will work without fail2ban installed.

### PATH Issues in User-Space Mode

If `secure-fail2ban-manager` command is not found after user-space installation:

```bash
# Add to PATH permanently
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Or run with full path
~/.local/bin/secure-fail2ban-manager
```

### Permission Denied Errors

**User-space mode:**
All operations run with user permissions - no permission issues.

**Full system mode:**
```bash
# Ensure you're in the fail2ban-managers group
groups
# Should show: ... fail2ban-managers ...

# If not, log out and back in after installation
```

## Security Considerations

### User-Space Mode Security
- Limited attack surface (no system modifications)
- User-specific audit logging
- Cannot interfere with system fail2ban configuration
- Safe for testing and development

### Full System Mode Security
- Restricted sudo access (only specific fail2ban commands)
- Group-based access control
- Comprehensive audit logging
- Input validation and rate limiting

## Command Reference

### Installation Options
```bash
# Dry run (see what would be installed)
python3 install_secure_fail2ban.py --dry-run --install

# Normal installation
python3 install_secure_fail2ban.py --install

# Verbose logging
python3 install_secure_fail2ban.py --install --log-level DEBUG

# Show version
python3 install_secure_fail2ban.py --version
```

### Post-Installation Commands
```bash
# Full system mode
secure-fail2ban-manager
sudo fail2ban-client status

# User-space mode  
~/.local/bin/secure-fail2ban-manager
# or if PATH is updated:
secure-fail2ban-manager
```

## Files and Locations

### User-Space Installation
- Script: `~/.local/bin/secure-fail2ban-manager`
- Wrapper: `~/.local/bin/fail2ban-manager`
- Logs: `~/.local/var/log/secure_fail2ban_manager.log`

### Full System Installation
- Script: `/usr/local/bin/secure-fail2ban-manager`
- Sudoers: `/etc/sudoers.d/secure-fail2ban`
- Jails: `/etc/fail2ban/jail.d/email-security.conf`
- Filters: `/etc/fail2ban/filter.d/[various].conf`
- Logs: `/var/log/secure_fail2ban_manager.log`

## Getting Help

1. **Installation Issues**: Check the installation summary output
2. **Log Files**: Review installation logs for detailed error information
3. **Permission Issues**: Verify group membership and sudo configuration
4. **System Integration**: Contact system administrator for enterprise environments
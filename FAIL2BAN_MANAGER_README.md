# 🛡️ Fail2Ban Manager

A comprehensive Python script for managing Fail2Ban without command-line complexity. This tool provides an intuitive interface similar to your existing `mail_manager.py` and `manage_app.py` scripts.

## 📋 Features

### 🔍 Monitoring & Status
- **Real-time jail status** - View all active jails with current statistics
- **Banned IP overview** - See all currently banned IPs across all jails
- **Daily/Weekly reports** - Comprehensive activity summaries
- **Attack pattern analysis** - Understand when and how attacks occur

### ⚙️ Management Functions
- **Easy IP unbanning** - Unban IPs individually or from all jails
- **Manual IP banning** - Ban specific IPs with custom reasons
- **IP search** - Find specific IP activity across all logs
- **Configuration overview** - View current jail settings

### 📊 Analytics & Reporting
- **Attack statistics** - Bans, attempts, and trends over time
- **Service targeting analysis** - Which services are attacked most
- **Hourly/daily pattern recognition** - When attacks typically occur
- **Repeat offender identification** - IPs targeting multiple services
- **CSV export** - Export data for external analysis

## 🚀 Installation & Setup

### 1. Prerequisites
- Fail2Ban installed and running
- Python 3.6+
- Sudo privileges
- User in `adm` group (for log access)

### 2. Quick Setup
```bash
# Run the setup script
./setup_fail2ban_manager.sh

# Log out and back in (to apply group changes)
# OR run: newgrp adm

# Start the manager
./fail2ban_manager.py
```

### 3. Manual Setup
```bash
# Install fail2ban if not already installed
sudo apt update && sudo apt install fail2ban

# Add user to adm group for log access
sudo usermod -a -G adm $(whoami)

# Make sure fail2ban is running
sudo systemctl start fail2ban
sudo systemctl enable fail2ban

# Make the script executable
chmod +x fail2ban_manager.py
```

## 📖 Usage

### Main Menu Options

```
🛡️ FAIL2BAN MANAGEMENT TOOL
============================================================
1. 📊 Show jail status and statistics
2. 🚫 List all banned IPs
3. ✅ Unban specific IP
4. ⚠️ Ban specific IP manually
5. 📋 Daily/Weekly activity report
6. 📈 Attack pattern analysis
7. 🔍 Search IP across all logs
8. ⚙️ Jail configuration overview
9. 📤 Export ban data to CSV
x. ❌ Exit
```

### Example Workflows

#### View System Status
- Choose option **1** to see all jails and their current status
- Check which services are under attack
- See total ban counts and current threats

#### Unban an IP Address
- Choose option **3** 
- View currently banned IPs
- Select IP to unban by number or enter IP address
- Confirm unbanning from specific jail or all jails

#### Generate Daily Report
- Choose option **5**
- View today's attack summary
- See weekly trends and patterns
- Identify top attacking IPs

#### Search for Specific IP
- Choose option **7**
- Enter IP address to investigate
- View complete history of bans, unbans, and attempts
- Analyze IP behavior over time

#### Export Data for Analysis
- Choose option **9**
- Choose time period (days)
- Export to CSV format
- Import into Excel/other tools for further analysis

## 🔧 Configuration

The script automatically detects your fail2ban configuration from:
- `/etc/fail2ban/jail.local` - Your custom jail configurations
- `/var/log/fail2ban.log` - Main log file for analysis

### Supported Jails
Based on your current configuration:
- **sshd** - SSH brute-force protection
- **nginx-http-auth** - NGINX authentication failures
- **nginx-botsearch** - NGINX bot/scanner protection
- **postfix** - SMTP brute-force protection
- **dovecot** - IMAP login protection

## 📊 Sample Reports

### Daily Activity Report
```
📅 TODAY'S ACTIVITY:
  🚫 Total Bans: 15
  🔍 Failed Attempts: 127
  ✅ Unbans: 2

  📊 Bans by Service:
    • sshd: 8
    • nginx-botsearch: 4
    • postfix: 3

  🎯 Top Attackers Today:
    • 192.168.1.100: 3 bans
    • 10.0.0.50: 2 bans
```

### Attack Pattern Analysis
```
🕐 Attack Distribution by Hour:
  00:00 │███ 6
  01:00 │█ 2
  02:00 │███████ 14
  ...

🎯 Most Targeted Services:
  • sshd: 45 attacks (60.0%)
  • nginx-botsearch: 20 attacks (26.7%)
  • postfix: 10 attacks (13.3%)
```

## 🛠️ Troubleshooting

### Permission Errors
```bash
# Make sure you're in the adm group
groups $(whoami)

# If not in adm group, add yourself
sudo usermod -a -G adm $(whoami)

# Log out and back in, or run
newgrp adm
```

### Sudo Issues
```bash
# Test sudo access to fail2ban
sudo fail2ban-client status

# If this fails, check sudo group membership
groups $(whoami) | grep sudo
```

### Log Access Issues
```bash
# Check log file permissions
ls -la /var/log/fail2ban.log

# Should show: -rw-r----- 1 root adm
# Your user needs to be in 'adm' group
```

## 🔒 Security Notes

- Script requires sudo privileges for fail2ban commands
- Only displays sanitized information (no sensitive data)
- All actions are logged by fail2ban itself
- Script validates IP addresses before processing
- No persistent storage of sensitive information

## 📈 Advanced Features

### CSV Export Format
The CSV export includes:
- Timestamp
- Event Type (BAN/UNBAN/ATTEMPT)
- Jail Name
- IP Address

### Log Analysis
The script analyzes:
- Current and rotated log files
- Compressed historical logs (.gz)
- Pattern matching for bans, unbans, and attempts
- Time-based filtering and aggregation

### Attack Pattern Recognition
- Hourly attack distribution
- Daily attack patterns
- Service-specific targeting
- Repeat offender identification
- Geographic clustering (IP ranges)

## 🤝 Integration

This script follows the same design patterns as your other management tools:
- Similar menu structure to `mail_manager.py`
- Consistent error handling and user feedback
- Modular function design for easy maintenance
- Clear separation of concerns

## 📝 Logs

The script itself doesn't create additional log files but relies on:
- Fail2ban's own logging (`/var/log/fail2ban.log`)
- System authentication logs (`/var/log/auth.log`)
- Service-specific logs (nginx, postfix, etc.)

---

**Created by:** Claude Code Assistant  
**Compatible with:** Ubuntu/Debian systems with fail2ban  
**Version:** 1.0  
**Last Updated:** $(date)
# Secure Fail2Ban Manager v2.0.0

A security-hardened fail2ban management script with comprehensive email monitoring capabilities, enhanced security features, and audit logging.

## 🛡️ Security Features

### Core Security Enhancements
- **Input Validation & Sanitization**: Prevents command injection and path traversal attacks
- **Rate Limiting**: Prevents abuse of ban/unban operations
- **Audit Logging**: Comprehensive security event logging with session management
- **Principle of Least Privilege**: Restricted sudo access for specific fail2ban operations only
- **Session Management**: Secure session tracking with unique session IDs
- **Enhanced Error Handling**: Secure error messages that don't leak sensitive information

### Email Security Monitoring
- **SMTP Attack Detection**: Monitors postfix SASL authentication failures and relay attempts
- **IMAP/POP3 Protection**: Enhanced Dovecot authentication monitoring
- **Directory Harvest Detection**: Identifies email address enumeration attacks
- **Spam Injection Monitoring**: Detects content filtering bypass attempts
- **Mail Queue Analysis**: Real-time email queue failure monitoring
- **Attack Pattern Analysis**: Email-specific attack trending and analysis

## 📧 Email Jail Coverage

### Postfix Protection
- `postfix-sasl`: SMTP authentication brute force protection
- `postfix-rbl`: RBL bypass and reputation attack detection  
- `postfix-relay`: Unauthorized mail relay attempt blocking
- `postfix-spam`: Spam injection and content filtering bypass detection
- `postfix-ratelimit`: Connection rate limiting protection

### Dovecot Protection
- `dovecot`: General IMAP/POP3 authentication protection
- `dovecot-auth`: Enhanced authentication failure detection
- `dovecot-pop3-imap`: Specific POP3/IMAP brute force protection

### Webmail Protection
- `roundcube-auth`: Roundcube webmail authentication protection
- `squirrelmail`: SquirrelMail webmail attack detection

### Advanced Email Threats
- `email-directory-harvest`: Directory harvest attack detection
- `email-content-filter-bypass`: Content filter bypass detection
- `email-reputation-bypass`: Reputation system bypass detection

## 📁 File Structure

```
/home/kdresdell/minipass_env/
├── secure_fail2ban_manager.py      # Main security-hardened manager script
├── install_secure_fail2ban.py      # Automated installation script
├── email-security.conf             # Comprehensive email jail configuration
├── email-filters.conf              # Email security filter definitions
├── secure-fail2ban-sudoers         # Restricted sudoers configuration
├── requirements.txt                 # Python dependencies
└── SECURE_FAIL2BAN_README.md       # This documentation
```

## 🚀 Installation

### Prerequisites
- Ubuntu Linux 18.04+ 
- Python 3.8+
- fail2ban installed (`sudo apt install fail2ban`)
- sudo privileges

### Quick Installation
```bash
# Clone or download the files to your directory
cd /home/kdresdell/minipass_env/

# Install Python dependencies
pip install -r requirements.txt

# Run the automated installer
python install_secure_fail2ban.py --install

# Follow the prompts and confirm installation
```

### Manual Installation Steps
```bash
# 1. Create fail2ban-managers group
sudo groupadd fail2ban-managers

# 2. Add your user to the group
sudo usermod -a -G fail2ban-managers $USER

# 3. Install sudoers configuration
sudo cp secure-fail2ban-sudoers /etc/sudoers.d/secure-fail2ban
sudo chmod 440 /etc/sudoers.d/secure-fail2ban
sudo visudo -c  # Validate syntax

# 4. Install email jail configuration
sudo cp email-security.conf /etc/fail2ban/jail.d/

# 5. Install filter configurations (see email-filters.conf for individual filters)

# 6. Install manager script
sudo cp secure_fail2ban_manager.py /usr/local/bin/secure-fail2ban-manager
sudo chmod 755 /usr/local/bin/secure-fail2ban-manager

# 7. Reload fail2ban
sudo systemctl reload fail2ban

# 8. Log out and back in for group changes to take effect
```

## 🔧 Usage

### Running the Manager
```bash
# Run from anywhere (after installation)
secure-fail2ban-manager

# Or run directly
./secure_fail2ban_manager.py

# Show version
secure-fail2ban-manager --version
```

### Main Menu Options
1. **Jail Status Overview** - Security-enhanced jail monitoring with service categorization
2. **Banned IPs Analysis** - Detailed banned IP list with network analysis  
3. **Secure IP Unbanning** - Rate-limited unbanning with audit logging
4. **Secure IP Banning** - Manual IP banning with reason tracking
5. **Security Activity Report** - Daily/weekly activity with security insights
6. **Attack Pattern Analysis** - Enhanced pattern analysis with risk assessment
7. **IP Search & Investigation** - Comprehensive IP history search
8. **📧 Email Security Report** - NEW: Comprehensive email threat analysis
9. **Secure Data Export** - Validated CSV export with network information
10. **Security Audit Log** - View recent security events and session logs

### New Email Security Report Features
- **Email Attack Statistics**: SMTP/IMAP/POP3 attack summaries
- **Authentication Failure Analysis**: Failed login pattern detection
- **Directory Harvest Detection**: Email enumeration attack identification  
- **Relay Abuse Monitoring**: Unauthorized relay attempt tracking
- **Spam Injection Alerts**: Content filtering bypass detection
- **Attack Timing Analysis**: Peak attack time identification
- **Geographic Analysis**: Basic network-based attack source classification

## 🔐 Security Configuration

### Rate Limiting
- **Command Operations**: 20 commands per minute
- **Unban Operations**: 5 unbans per 5 minutes  
- **Ban Operations**: 3 bans per 5 minutes

### Audit Logging
- **Session Tracking**: Unique session IDs for all operations
- **Command Logging**: All fail2ban commands logged with outcomes
- **Security Events**: Authentication, authorization, and error events
- **Log Location**: `/var/log/secure_fail2ban_manager.log`

### Input Validation
- **IP Address Validation**: IPv4/IPv6 format validation with private IP restrictions
- **Jail Name Validation**: Alphanumeric characters only to prevent injection
- **Filename Validation**: Path traversal prevention for exports
- **Time Period Validation**: Reasonable limits (1-365 days) to prevent resource exhaustion

## 📊 Email Monitoring Configuration

### Jail Configuration Highlights
```ini
# Example email jail configuration
[postfix-sasl]
enabled = true
port = smtp,465,587,submission
maxretry = 3
findtime = 600
bantime = 3600

[dovecot-auth]  
enabled = true
port = pop3,pop3s,imap,imaps
maxretry = 3
findtime = 600
bantime = 7200
```

### Customization Options
- **Adjust ban times** based on threat severity
- **Modify retry thresholds** for different attack types
- **Configure ignore lists** for trusted networks
- **Enable/disable specific jails** based on your mail server setup

## 🔍 Monitoring & Troubleshooting

### Log Monitoring
```bash
# Monitor fail2ban activity
sudo tail -f /var/log/fail2ban.log

# Monitor email security events
sudo tail -f /var/log/mail.log

# Monitor manager audit log  
sudo tail -f /var/log/secure_fail2ban_manager.log

# Check active jails
sudo fail2ban-client status
```

### Testing Email Jails
```bash
# Test specific email jail
sudo fail2ban-client status postfix-sasl

# Test filter against log file
sudo fail2ban-regex /var/log/mail.log /etc/fail2ban/filter.d/postfix-sasl.conf

# View banned IPs for email services
sudo fail2ban-client status dovecot-auth
```

### Common Issues
1. **Permission Denied**: Ensure user is in `fail2ban-managers` group and logged out/in
2. **Rate Limit Exceeded**: Wait for rate limit window to reset
3. **Jail Not Found**: Check if specific email jails are enabled for your mail server
4. **Filter Not Matching**: Verify log file paths and regex patterns for your setup

## 🛠️ Customization

### Adding Custom Email Jails
1. Create new filter in `/etc/fail2ban/filter.d/`
2. Add jail configuration to `/etc/fail2ban/jail.d/email-security.conf`
3. Reload fail2ban: `sudo systemctl reload fail2ban`
4. Test with the manager script

### Extending Security Features
The script is designed for extensibility:
- Add new validation functions to `InputValidator` class
- Extend rate limiting with additional `RateLimiter` instances  
- Add new audit events to `SecurityAuditor` class
- Implement additional email log parsers for other mail servers

## 🔒 Security Best Practices

### Access Control
- Use dedicated service account for production deployments
- Implement SSH key-based authentication
- Consider adding 2FA for critical operations
- Regularly review audit logs for suspicious activity

### Monitoring
- Set up log rotation for audit files
- Monitor for repeated rate limit violations
- Track successful vs failed operations ratios
- Alert on unusual authentication patterns

### Maintenance
- Update dependencies regularly for security patches
- Review and update email filter patterns quarterly
- Audit user group memberships monthly
- Test backup and recovery procedures

## 📈 Performance Considerations

### Resource Usage
- Memory: ~50MB typical usage
- CPU: Low impact, burst during log parsing
- Disk: Audit logs grow over time (implement rotation)
- Network: Minimal impact

### Optimization Tips
- Use log file rotation to prevent large file parsing
- Consider implementing log caching for frequently accessed data
- Monitor rate limiter effectiveness and adjust thresholds as needed

## 🆘 Support & Troubleshooting

### Debug Mode
```bash
# Enable debug logging
secure-fail2ban-manager --log-level DEBUG

# Use debug menu option
# Menu option 'd' provides detailed debugging information
```

### Getting Help
1. Check the security audit log for detailed error messages
2. Verify fail2ban service status: `sudo systemctl status fail2ban`
3. Test sudo permissions: `sudo -l` to see allowed commands
4. Validate fail2ban configuration: `sudo fail2ban-client --test`

## 📝 License & Attribution

Created by: Python DevOps Automation Specialist  
Version: 2.0.0 (Security Enhanced)  
Date: 2025-08-02

This script provides enhanced security and email monitoring capabilities for fail2ban management while maintaining the user-friendly interface of the original script.

## 🔄 Migration from Original Script

If migrating from the original `fail2ban_manager.py`:

1. **Backup existing configuration**: Save any custom jail configurations
2. **Install new version**: Follow installation steps above  
3. **Migrate settings**: Transfer any custom IP whitelists or ban settings
4. **Test functionality**: Verify all features work as expected
5. **Update automation**: Update any scripts calling the old manager

The new version maintains command compatibility while adding security hardening and email monitoring features.
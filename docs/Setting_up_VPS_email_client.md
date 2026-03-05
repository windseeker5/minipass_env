# Setting up VPS Email Client

## Option 1: Gmail SMTP (Recommended - Most reliable)

### Install required packages

```bash
sudo apt update && sudo apt install msmtp msmtp-mta mailutils
```

### Create configuration file

```bash
sudo nano /etc/msmtprc
```

Add this content to `/etc/msmtprc`:

```
defaults
auth           on
tls            on
tls_trust_file /etc/ssl/certs/ca-certificates.crt
logfile        /var/log/msmtp.log

account        gmail
host           smtp.gmail.com
port           587
from           your-email@gmail.com
user           your-email@gmail.com
password       your-app-password

account default : gmail
```

### Set proper permissions

```bash
sudo chmod 640 /etc/msmtprc
sudo chown root:mail /etc/msmtprc
```

### Gmail App Password Setup

**You'll need a Gmail App Password** (not regular password):

1. Go to Google Account → Security → 2-Step Verification → App passwords
2. Generate app password for "Mail"
3. Use this app password in the config file above

### Test the setup

```bash
echo "Test alert from VPS" | mail -s "Server Alert Test" your-email@gmail.com
```

## Option 2: Use your mail container

### Configure Postfix to relay through container

```bash
sudo postconf -e "relayhost = [172.27.0.8]:587"
sudo postconf -e "smtp_sasl_auth_enable = yes"
sudo postconf -e "smtp_sasl_security_options = noanonymous"
```

### Create authentication file

```bash
# Create auth file
echo "[172.27.0.8]:587 lhgi@minipass.me:your-password" | sudo tee /etc/postfix/sasl_passwd
sudo postmap /etc/postfix/sasl_passwd
sudo chmod 600 /etc/postfix/sasl_passwd*
sudo systemctl restart postfix
```

### Test the setup

```bash
echo "Test alert from VPS" | mail -s "Server Alert Test" your-email@gmail.com
```

## Setting up monitoring alerts

### Add to crontab for automated monitoring

```bash
crontab -e
```

Add these lines:

```bash
# Check disk space every hour
0 * * * * df -h | awk '$5 > 80 {print "ALERT: " $0}' | mail -s "Disk Space Warning" your-email@gmail.com

# Check if services are running
0 * * * * systemctl is-active --quiet docker || echo "Docker is down!" | mail -s "Service Alert" your-email@gmail.com
```

## Reading your current mbox file

To read existing emails in your mbox file:

```bash
neomutt -f ~/mbox
```

## Why the original email bounced

The email bounce occurred because:

1. Someone sent an email **from the VPS host** using a command like `mail lhgi@minipass.me`
2. The VPS host's Postfix tried to send it, but failed because it doesn't know how to reach your container's mail server
3. The email bounced back and got saved in your host's mbox file

The container mail server is working perfectly - this was just a routing issue between the host and container mail systems.

## Recommendation

**Option 1 (Gmail SMTP) is recommended** because:
- More reliable for alerts since it doesn't depend on your container being healthy
- Simpler configuration
- Better deliverability for critical alerts
- No dependency on your local mail infrastructure
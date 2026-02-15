# Safe Ubuntu Server Upgrade & Reboot Cheat Sheet

## Current Infrastructure Analysis
✅ **10 containers running** across 3 Docker Compose files:
- **Main services**: nginx-proxy, Let's Encrypt, mailserver, 3 Flask apps
- **All have `restart: always` or `restart: unless-stopped`** - will auto-restart
- **System services**: docker.service and fail2ban.service are enabled

## Safe Upgrade & Reboot Procedure

### 1. Pre-Upgrade Backup
```bash
# Backup critical data
sudo docker-compose exec mailserver postconf -n > mail_config_backup.txt
cp -r ./app/instance ./app/instance_backup_$(date +%Y%m%d)
```

### 2. Update System (Safe - no kernel updates detected)
```bash
sudo apt update && sudo apt upgrade -y
```

### 3. Reboot System
```bash
sudo reboot
```

### 4. Post-Reboot Validation
```bash
# Check all containers are running
docker ps

# Verify main services
curl -I https://minipass.me
curl -I https://lhgi.minipass.me
dig MX minipass.me

# Check mail ports
netstat -tlnp | grep -E ":(25|587|993|143)"
```

## Why This is Safe
- **All containers have restart policies** - will auto-start after reboot
- **Docker service is enabled** - starts automatically
- **Fail2ban service is enabled** - starts automatically
- **No critical kernel updates** - just security patches and library updates
- **Let's Encrypt companion** will handle SSL certificates automatically

## Recovery Commands (if needed)
```bash
# Restart main stack
cd /home/kdresdell/minipass_env
docker-compose up -d

# Restart individual customer apps
cd deployed/heq && docker-compose up -d
cd deployed/monorganisation && docker-compose up -d
```

## Available Updates (Dec 11, 2025)
- apparmor security updates
- binutils security updates
- glib2.0 updates
- libpng security patch
- netplan updates
- nodejs minor version update
- ubuntu-pro-client updates

The updates are routine security patches - no breaking changes expected!
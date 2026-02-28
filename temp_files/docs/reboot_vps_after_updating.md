# VPS Restart Guide After Updating

## Quick Commands (Copy & Paste)

```bash
# Navigate to project directory
cd /home/kdresdell/minipass_env/

# Restart all Docker containers
docker-compose restart

# Restart Flask web controller service
sudo systemctl restart minipass-web.service

# Verify everything is running
docker ps
systemctl status minipass-web.service
```

## Step-by-Step Instructions

### 1. Navigate to Project Directory
```bash
cd /home/kdresdell/minipass_env/
```

### 2. Restart All Containers
```bash
# This restarts all 7 containers at once
docker-compose restart
```

**Containers that will be restarted:**
- lhgi (customer app)
- mailserver (email server)
- flask-controller-nginx
- nginx-proxy
- bloomcap
- flask-controller-proxy
- mail-cert-request
- nginx-letsencrypt

### 3. Restart Flask Web Service
```bash
# Restart the Flask controller service
sudo systemctl restart minipass-web.service
```

### 4. Verification
```bash
# Check all containers are running
docker ps

# Check Flask service is active
systemctl status minipass-web.service
```

## Expected Results

All containers should show status "Up" and the Flask service should show "active (running)".

## That's It!

Your VPS is now updated and all services restarted.
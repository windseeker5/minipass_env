# Bloomcap Website Update Guide

This guide provides step-by-step instructions for updating the Bloomcap website after uploading new HTML files.

## When to Use This Guide

Use this guide when you have:
- Updated existing HTML files in `./bloomcap/html/`
- Added new HTML files to the bloomcap website
- Made changes that require refreshing the website

## Prerequisites

- SSH access to the VPS
- Navigate to the project directory: `/home/kdresdell/minipass_env/`

## Step-by-Step Instructions

### 1. Restart the Bloomcap Container

```bash
# Restart the bloomcap nginx container
docker restart bloomcap
```

**Why:** This ensures nginx picks up any new or updated HTML files from the volume mount.

### 2. Restart the Flask Controller Service

```bash
# Restart the Flask controller service
sudo systemctl restart minipass-web.service
```

**Why:** This restarts the local Flask service that manages containers and ensures it has the latest state.

### 3. Verification Steps

#### Check Container Status
```bash
# Verify bloomcap container is running
docker ps | grep bloomcap
```

Expected output: Container should show as "Up" with recent restart time.

#### Check Flask Service Status
```bash
# Check Flask controller service status
systemctl status minipass-web.service
```

Expected output: Service should show as "active (running)".

#### Test Website
- Visit https://bloomcap.ca
- Visit https://www.bloomcap.ca
- Verify new content is displayed

## Quick Commands Summary

```bash
# Navigate to project directory
cd /home/kdresdell/minipass_env/

# Restart both services
docker restart bloomcap
sudo systemctl restart minipass-web.service

# Verify everything is running
docker ps | grep bloomcap
systemctl status minipass-web.service
```

## Troubleshooting

### Container Won't Start
```bash
# Check container logs
docker logs bloomcap
```

### Service Won't Start
```bash
# Check service logs
journalctl -u minipass-web.service -n 20
```

### Website Not Updating
1. Check if HTML files are in the correct location: `./bloomcap/html/`
2. Verify file permissions are correct
3. Try a hard refresh in browser (Ctrl+F5)

## File Locations

- **HTML Files:** `./bloomcap/html/` (mounted to container)
- **Docker Compose:** `./docker-compose.yml`
- **Flask Service:** `/home/kdresdell/minipass_env/MinipassWebSite/`

---

**Last Updated:** September 2025
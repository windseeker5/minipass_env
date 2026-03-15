# .env Setup for VPS Containers - 3 Steps

**Do this ONCE. All containers will automatically have your API keys.**

**📘 Note:** This is a ONE-TIME setup. For regular deployments, use [QUICK_DEPLOY_LHGI.md](QUICK_DEPLOY_LHGI.md) or [VPS_DEPLOYMENT_GUIDE.md](VPS_DEPLOYMENT_GUIDE.md).

---

## Step 1: Copy .env to VPS

On your **local computer**, run:

```bash
scp /home/kdresdell/Documents/DEV/minipass_env/app/.env YOUR_USER@YOUR_VPS_IP:/home/kdresdell/minipass_env/.env
```

**Example:**
```bash
scp /home/kdresdell/Documents/DEV/minipass_env/app/.env kdresdell@minipass.me:/home/kdresdell/minipass_env/.env
```

✅ Done? .env is now on your VPS at `/home/kdresdell/minipass_env/.env`

---

## Step 2: Edit docker-compose.yml on VPS

SSH to your VPS:
```bash
ssh YOUR_USER@YOUR_VPS_IP
cd /home/kdresdell/minipass_env
nano docker-compose.yml
```

**Find the `lhgi` service** (around line 79-98).

**Add these 2 lines** right after `restart: always`:

```yaml
  lhgi:
    build:
      context: ./app
    container_name: lhgi
    restart: always
    env_file:              # ← ADD THIS LINE
      - .env               # ← ADD THIS LINE
    environment:
      - FLASK_ENV=prod
```

**Save and exit** (Ctrl+O, Enter, Ctrl+X)

✅ Done? docker-compose.yml now loads .env for lhgi container

---

## Step 3: Deploy

Still on the VPS:

```bash
cd /home/kdresdell/minipass_env
./deploy-lghi-vps.sh
```

✅ Done! Your container now has all API keys (Google Maps, Groq, Unsplash, Google AI)

---

## Verify It Works

After deployment, check if environment variables are loaded:

```bash
docker exec lhgi printenv | grep -E "GOOGLE_MAPS|GROQ|UNSPLASH|GOOGLE_AI"
```

You should see your API keys.

---

## Future Containers

### For LHGI-style containers (same directory level)

When you add a new customer container at the same level as LHGI (e.g., `customer2`), just add the same 2 lines:

```yaml
  customer2:
    build:
      context: ./app
    container_name: customer2
    restart: always
    env_file:              # ← SAME 2 LINES
      - .env               # ← SAME FILE (same directory)
    environment:
      - FLASK_ENV=prod
```

### For auto-deployed customers (deployed/{customer}/ directory)

For customers deployed via Flask controller in `/deployed/{customer}/` directory (like HEQ), use a **relative path going up 2 levels**:

**Location:** `/home/kdresdell/minipass_env/deployed/heq/docker-compose.yml`

```yaml
  heq:
    build:
      context: ./app
    container_name: minipass_heq
    restart: always
    env_file:
      - ../../.env         # ← Goes up 2 levels to /home/kdresdell/minipass_env/.env
    environment:
      - FLASK_ENV=prod
    ports:
      - "8890:5000"
```

**Why `../../.env`?**
- Current location: `/deployed/heq/`
- First `../` goes to: `/deployed/`
- Second `../` goes to: `/home/kdresdell/minipass_env/`
- Result: `/home/kdresdell/minipass_env/.env` ✅

**After editing:**
```bash
cd /home/kdresdell/minipass_env/deployed/heq
docker-compose down
docker-compose up -d  # No rebuild needed!
```

**ALL containers share the SAME .env file.** Simple!

---

## Update API Keys Later

If you get new API keys:

**Step 1:** Edit .env on VPS
```bash
ssh YOUR_USER@YOUR_VPS_IP
cd /home/kdresdell/minipass_env
nano .env
# Edit your keys
# Save and exit
```

**Step 2:** Restart containers
```bash
docker-compose restart lhgi
# Restart other containers if needed
```

Done!

---

## Summary

✅ ONE .env file at `/home/kdresdell/minipass_env/.env`
✅ ALL containers read it automatically
✅ Update once, all containers get new keys
✅ Never commit .env to git (it's in .gitignore)

**That's it!**

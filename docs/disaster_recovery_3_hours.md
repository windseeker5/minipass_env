# VPS Disaster Recovery - Step by Step Guide
*Target Recovery Time: < 3 hours*

## Scenario 1: Complete minipass_env/ folder corruption

### 1.1 Backup corrupted folder
```bash
cd /home/kdresdell/
mv minipass_env minipass_bk_$(date +%Y%m%d_%H%M%S)
```

### 1.2 Clone fresh minipass_env with submodules
```bash
git clone --recurse-submodules git@github.com:windseeker5/minipass_env.git
cd minipass_env
git submodule update --init --recursive
```

### 1.3 SCP restore from local DEV backup (SSH port 2222)
```bash
# From your LOCAL machine, copy to VPS:
scp -P 2222 -r /home/kdresdell/customer_backups/MinipassWebSite/.env kdresdell@your-vps:/home/kdresdell/minipass_env/MinipassWebSite/
scp -P 2222 -r /home/kdresdell/customer_backups/MinipassWebSite/venv kdresdell@your-vps:/home/kdresdell/minipass_env/MinipassWebSite/
scp -P 2222 -r /home/kdresdell/customer_backups/deployed kdresdell@your-vps:/home/kdresdell/minipass_env/
scp -P 2222 /home/kdresdell/customer_backups/mailserver.env kdresdell@your-vps:/home/kdresdell/minipass_env/
scp -P 2222 -r /home/kdresdell/customer_backups/config kdresdell@your-vps:/home/kdresdell/minipass_env/
scp -P 2222 -r /home/kdresdell/customer_backups/maildata kdresdell@your-vps:/home/kdresdell/minipass_env/
scp -P 2222 -r /home/kdresdell/customer_backups/mailstate kdresdell@your-vps:/home/kdresdell/minipass_env/
```

### 1.4 Restore MinipassWebSite Python environment
```bash
cd /home/kdresdell/minipass_env/MinipassWebSite
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --break-system-packages
```

### 1.5 Fix mail server permissions and config
```bash
# Fix maildata/mailstate ownership (Docker runs as specific UIDs)
sudo chown -R 5000:5000 /home/kdresdell/minipass_env/maildata
sudo chown -R root:root /home/kdresdell/minipass_env/mailstate

# Fix config permissions
sudo chown -R kdresdell:kdresdell /home/kdresdell/minipass_env/config

# Restart mail server to pick up restored config
cd /home/kdresdell/minipass_env
docker-compose restart mailserver

# Wait and check logs
docker-compose logs -f mailserver
```

### 1.6 Restore customer deployments and make them upgradable
```bash
# For each customer that needs git setup (check with: ls deployed/*/app/.git)
# Example for KDC:

cd /home/kdresdell/minipass_env/deployed/kdc/app

# Check if .git exists
if [ ! -d ".git" ]; then
    echo "Fixing git repo for KDC..."
    git clone git@github.com:windseeker5/dpm.git temp_clone
    mv temp_clone/.git .
    rm -rf temp_clone
    git status  # Should show modified files
fi

# Repeat for HEQ and TestDel:
cd /home/kdresdell/minipass_env/deployed/heq/app
if [ ! -d ".git" ]; then
    git clone git@github.com:windseeker5/dpm.git temp_clone
    mv temp_clone/.git .
    rm -rf temp_clone
fi

cd /home/kdresdell/minipass_env/deployed/testdelancementmf/app
if [ ! -d ".git" ]; then
    git clone git@github.com:windseeker5/dpm.git temp_clone
    mv temp_clone/.git .
    rm -rf temp_clone
fi

# Start all customer containers
cd /home/kdresdell/minipass_env
for customer in deployed/*/; do
    echo "Starting $(basename $customer)..."
    cd $customer && docker-compose up -d
    cd /home/kdresdell/minipass_env
done

# Test upgrade system
python3 tools/upgrade_customers.py --dry-run
```

---

## Key Repository Structure

**Understanding the git architecture:**
- **Main infrastructure**: `/home/kdresdell/minipass_env/` → `minipass_env.git`
  - Contains: tools/, docker-compose.yml, MinipassWebSite/, mail server
- **App template**: `/home/kdresdell/minipass_env/app/` → `dpm.git` (submodule)
  - Contains: migrations/, Flask app code (the product customers buy)
- **Customer instances**: `/home/kdresdell/minipass_env/deployed/*/app/` → `dpm.git`
  - Each customer gets deployed copy with git repository for upgrades

## Crisis Prevention Checklist

**Daily/Weekly checks:**
```bash
# Check main repository structure
cd /home/kdresdell/minipass_env
git status
git remote -v  # Should be minipass_env.git

# Check app submodule
cd app
git remote -v  # Should be dpm.git

# Check customer git status
for customer in /home/kdresdell/minipass_env/deployed/*/app; do
    echo "Checking $customer"
    cd "$customer" && git remote -v 2>/dev/null || echo "No git repo"
done

# Verify containers running
docker ps --filter "name=minipass_"

# Test upgrade system
python3 tools/upgrade_customers.py --dry-run
```

## Emergency Contacts & Resources

- **Repository URLs**:
  - Infrastructure: `git@github.com:windseeker5/minipass_env.git`
  - App code: `git@github.com:windseeker5/dpm.git`
- **Backup location**: `/home/kdresdell/customer_backups/`
- **SSH Port**: 2222
- **Key directories**: maildata/, mailstate/, config/, deployed/

---

*Created after 2026-03-05 crisis to prevent future 10+ hour recovery sessions*
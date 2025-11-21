# COMPLETE WORKFLOW: Stripe Payment → Customer Deployment

## 📍 ENTRY POINT: Stripe Webhook

**File:** `MinipassWebSite/app.py:222`
**Function:** `stripe_webhook()`
**Trigger:** Stripe sends HTTP POST to `/webhook` endpoint when `checkout.session.completed` event occurs

---

## 🔄 EXECUTION FLOW (8 STEPS)

### Step 1: Validate Subdomain (`app.py:318-325`)
```python
init_customers_db()  # Initialize customers.db if not exists
if subdomain_taken(app_name):  # Check if subdomain already exists
    raise ValueError(f"Subdomain '{app_name}' is already taken")
```

### Step 2: Assign Resources (`app.py:328-332`)
```python
port = get_next_available_port()  # Starts from 9100
email_address = f"{app_name}_app@minipass.me"
```

### Step 3: Deploy Container (`app.py:335-343`)
**This calls:** `deploy_customer_container()` from `utils/deploy_helpers.py:163`

**Parameters passed:**
- `app_name` - subdomain name
- `admin_email` - customer's email
- `admin_password` - admin password
- `plan_key` - "basic", "pro", or "ultimate"
- `port` - assigned port (9100+)
- `organization_name` - optional org name
- `tier` - 1, 2, or 3
- `billing_frequency` - "monthly" or "annual"

---

## 🐳 DEPLOY_CUSTOMER_CONTAINER() - THE MAIN DEPLOYMENT SCRIPT

**File:** `utils/deploy_helpers.py:163-337`

### Sub-Step 3.1: Define Directories (`deploy_helpers.py:186-203`)
```python
base_dir = "/home/kdresdell/Documents/DEV/minipass_env"
source_dir = "/home/kdresdell/Documents/DEV/minipass_env/app"  # ⭐ SOURCE TEMPLATE
target_dir = "/home/kdresdell/Documents/DEV/minipass_env/deployed/{app_name}/app"
deploy_dir = "/home/kdresdell/Documents/DEV/minipass_env/deployed/{app_name}"
```

### Sub-Step 3.2: Clone App from GitHub (`deploy_helpers.py:218-248`)
```python
git_repo_url = "git@github.com:windseeker5/dpm.git"
git_clone_cmd = ["git", "clone", git_repo_url, target_dir]
subprocess.run(git_clone_cmd, capture_output=True, text=True, check=True)
```

**✅ UPDATED BEHAVIOR:** Uses `git clone` to pull the latest code from GitHub repository
**Changed from:** `shutil.copytree()` which copied a static local template

### Sub-Step 3.3: Generate .env File (`deploy_helpers.py:250-297`)
```python
env_path = os.path.join(target_dir, ".env")
env_content = f"""
MINIPASS_TIER={tier}
BILLING_FREQUENCY={billing_frequency}
GOOGLE_MAPS_API_KEY={parent_env_vars.get('GOOGLE_MAPS_API_KEY', '')}
# ... other API keys
"""
with open(env_path, "w") as f:
    f.write(env_content)
```

**✅ NEW STEP:** Generates deployment-specific `.env` file with tier configuration and API keys
- Reads API keys from parent environment (`/home/kdresdell/Documents/DEV/minipass_env/.env`)
- Sets tier-specific variables (MINIPASS_TIER, BILLING_FREQUENCY)
- Configures chatbot and API settings

### Sub-Step 3.4: Initialize Database Schema (`deploy_helpers.py:299-340`)
```python
instance_dir = os.path.join(target_dir, "instance")
os.makedirs(instance_dir, exist_ok=True)

migrate_cmd = ["flask", "db", "upgrade"]
subprocess.run(migrate_cmd, cwd=target_dir, env={"FLASK_APP": "app.py"}, check=True)
```

**✅ NEW STEP:** Runs Flask migrations to create complete database schema
- Creates `instance/` directory
- Executes all migration scripts to build full database structure
- **Changed from:** Database was copied with pre-populated data from template

### Sub-Step 3.5: Configure Admin & Organization (`deploy_helpers.py:342-352`)
```python
db_path = "deployed/{app_name}/app/instance/minipass.db"
insert_admin_user(db_path, admin_email, admin_password)
set_organization_name(db_path, organization_name)
```

**Database operations (`deploy_helpers.py:16-133`):**
- Inserts admin user into existing `Admin` table (created by migrations)
- Uses bcrypt hashed password stored as BLOB
- Inserts organization name into existing `Organization` table (created by migrations)
- **Changed from:** Previously created tables manually; now assumes schema exists from migrations

### Sub-Step 3.6: Generate docker-compose.yml (`deploy_helpers.py:354-405`)

**File created:** `deployed/{app_name}/docker-compose.yml`

```yaml
version: '3.8'

services:
  flask-app:
    container_name: minipass_{app_name}
    build:
      context: ./app

    volumes:
      - ./app:/app
      - ./app/instance:/app/instance
    environment:
      - FLASK_ENV=dev
      - ADMIN_EMAIL={admin_email}
      - ADMIN_PASSWORD={admin_password}
      - ORG_NAME={organization_name}
      - TIER={tier}
      - BILLING_FREQUENCY={billing_frequency}
      - VIRTUAL_HOST={app_name}.minipass.me
      - VIRTUAL_PORT=8889
      - LETSENCRYPT_HOST={app_name}.minipass.me
      - LETSENCRYPT_EMAIL=kdresdell@gmail.com

    restart: unless-stopped
    networks:
      - proxy

networks:
  proxy:
    external:
      name: minipass_env_proxy
```

**✅ UPDATED CONFIGURATION:**
- `VIRTUAL_PORT=8889` - now matches Dockerfile EXPOSE port **8889**
- `build: context: ./app` - builds from the git-cloned app folder
- Volumes mount `./app` (the cloned directory)

### Sub-Step 3.7: Build & Deploy Container (`deploy_helpers.py:406-418`)
```bash
cd deployed/{app_name}
docker-compose up -d
```

**What Docker does:**
1. Reads `docker-compose.yml`
2. Looks in `./app/dockerfile`
3. Builds image from Dockerfile:
   ```dockerfile
   FROM python:3.9
   WORKDIR /app
   COPY . .
   RUN pip install -r requirements.txt
   EXPOSE 8889
   CMD ["gunicorn", "--workers=2", "--threads=4", "--bind=0.0.0.0:8889", "app:app"]
   ```
4. Creates container named `minipass_{app_name}`
5. Connects to `minipass_env_proxy` network (nginx reverse proxy)
6. Starts container

### Sub-Step 3.8: Verify Container Running (`deploy_helpers.py:420-430`)
```bash
docker ps --filter name=minipass_{app_name}
```

---

### Step 4: Create Customer Database Record (`app.py:346-364`)
**After successful deployment**, creates record in `customers.db`:

```python
insert_customer(
    admin_email, app_name, app_name, plan_key, admin_password, port,
    email_address=email_address,
    forwarding_email=forwarding_email,
    email_status='pending',
    organization_name=organization_name,
    billing_frequency=billing_frequency,
    subscription_start_date=subscription_start_date,
    subscription_end_date=subscription_end_date,
    stripe_price_id=stripe_price_id,
    stripe_checkout_session_id=stripe_checkout_session_id,
    stripe_customer_id=stripe_customer_id,
    stripe_subscription_id=stripe_subscription_id,
    payment_amount=payment_amount,
    currency=currency,
    subscription_status='active'
)
```

### Step 5: Setup Customer Email (`app.py:367-380`)
```python
setup_customer_email_complete(app_name, admin_password, forwarding_email)
```

Creates:
- Mail account: `{app_name}_app@minipass.me`
- Sieve forwarding script: `config/user-patches/{app_name}_app@minipass.me/sieve/forward.sieve`

### Step 6: Send Deployment Email (`app.py:383-392`)
Sends email to customer with:
- App URL: `https://{app_name}.minipass.me`
- Admin credentials
- Email credentials

### Step 7: Mark Deployment Complete (`app.py:395-397`)
```python
update_customer_deployment_status(app_name, deployed=True)
```
Updates `customers.db` → sets `deployed=1`

### Step 8: Write Subscription Info (`app.py:400-423`)
**File created:** `/home/kdresdell/minipass_customers/{app_name}/app/instance/subscription.json`

```json
{
  "stripe_customer_id": "cus_xxx",
  "stripe_subscription_id": "sub_xxx",
  "plan": "basic",
  "billing_frequency": "monthly",
  "subscription_start_date": "2025-11-13...",
  "subscription_end_date": "2025-12-13...",
  "stripe_price_id": "price_xxx",
  "tier": 1
}
```

---

## 📁 FILES & DIRECTORIES CREATED

For customer with subdomain `example`:

```
/home/kdresdell/Documents/DEV/minipass_env/deployed/example/
├── docker-compose.yml                           # Generated in Step 3.4
└── app/                                         # Copied in Step 3.2
    ├── dockerfile                               # From source template
    ├── app.py                                   # From source template
    ├── models.py                                # From source template
    ├── utils.py                                 # From source template
    ├── requirements.txt                         # From source template
    ├── templates/                               # From source template
    ├── static/                                  # From source template
    ├── migrations/                              # From source template
    ├── instance/
    │   ├── minipass.db                         # Created in Step 3.3
    │   └── subscription.json                   # Created in Step 8
    └── [all other files from /app template]

/home/kdresdell/Documents/DEV/minipass_env/MinipassWebSite/
└── customers.db                                 # Updated in Step 4 & 7

./config/user-patches/example_app@minipass.me/
└── sieve/
    └── forward.sieve                           # Created in Step 5
```

**Docker artifacts:**
- Docker image: `deployed_example_flask-app` (built from dockerfile)
- Docker container: `minipass_example` (running)
- Docker network: `minipass_env_proxy` (connected)

---

## 🎯 UPDATED DEPLOYMENT PROCESS (Git-Based)

**✅ What now happens (as of latest update):**
1. `git clone git@github.com:windseeker5/dpm.git` pulls latest code → `deployed/{app_name}/app`
2. `.env` file is auto-generated with tier-specific configuration and API keys
3. `flask db upgrade` creates complete database schema from migrations
4. Admin user and organization are configured in the database
5. `docker-compose build` builds from `./app/dockerfile` (in cloned directory)
6. Volumes mount `./app` and `./app/instance`
7. VIRTUAL_PORT correctly set to 8889 (matches dockerfile EXPOSE)

**✅ Key improvements implemented:**
1. ✅ Replaced `shutil.copytree()` with `git clone` from GitHub
2. ✅ Added automatic .env file generation with tier configuration
3. ✅ Added database initialization via Flask migrations (`flask db upgrade`)
4. ✅ Fixed VIRTUAL_PORT mismatch (5000 → 8889)
5. ✅ Comprehensive logging for all deployment steps

**Git Repository for Customer App:**
- URL: `git@github.com:windseeker5/dpm.git`
- Strategy: Clone fresh on each deployment (always uses latest code)
- Database handling: Clone repo → run migrations → configure admin/org

**Benefits of Git-Based Deployment:**
- Always deploys latest code from repository
- Easier updates for existing customers (git pull vs re-copying)
- Proper migration handling ensures schema consistency across all deployments
- Clean separation between template repo and deployed instances

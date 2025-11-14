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

### Sub-Step 3.2: Copy App Template (`deploy_helpers.py:219-230`)
```python
shutil.copytree(source_dir, target_dir)
```

**⚠️ CURRENT BEHAVIOR:** Uses `shutil.copytree()` to copy the entire `/app` folder
**✅ THIS IS WHAT YOU WANT TO CHANGE TO GIT CLONE**

### Sub-Step 3.3: Setup Database (`deploy_helpers.py:233-243`)
```python
db_path = "deployed/{app_name}/app/instance/minipass.db"
insert_admin_user(db_path, admin_email, admin_password)  # Create Admin table & user
set_organization_name(db_path, organization_name)  # Create Organization table
```

**Database operations (`deploy_helpers.py:16-133`):**
- Creates `Admin` table with columns: `id`, `email`, `password_hash` (BLOB)
- Inserts admin user with bcrypt hashed password
- Creates `Organization` table with columns: `id`, `name`, `created_at`, `updated_at`
- Inserts organization name

### Sub-Step 3.4: Generate docker-compose.yml (`deploy_helpers.py:246-295`)

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
      - VIRTUAL_PORT=5000
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

**⚠️ IMPORTANT NOTES:**
- `VIRTUAL_PORT=5000` - but Dockerfile exposes port **8889**
- `build: context: ./app` - builds from the copied app folder
- Volumes mount `./app` (the copied directory)

### Sub-Step 3.5: Build & Deploy Container (`deploy_helpers.py:298-309`)
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

### Sub-Step 3.6: Verify Container Running (`deploy_helpers.py:312-321`)
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

## 🎯 KEY TAKEAWAYS FOR YOUR GIT MIGRATION

**What currently happens:**
1. `shutil.copytree()` copies **entire `/app` folder** → `deployed/{app_name}/app`
2. `docker-compose build` builds from `./app/dockerfile` (in copied directory)
3. Volumes mount `./app` and `./app/instance`

**What you need to change:**
1. Replace `shutil.copytree()` with `git clone git@github.com:windseeker5/dpm.git`
2. Ensure dockerfile and docker-compose.yml in your git repo match your VPS changes
3. Update volume mounts and environment variables as needed

**Files you mentioned changing on VPS:**
- `docker-compose.yml` - environment variables & volume mounts
- `dockerfile` - need to see your VPS version to compare

**Git Repository for Customer App:**
- URL: `git@github.com:windseeker5/dpm.git`
- Strategy: Always pull fresh (clone on each deployment)
- Database handling: Git clone, then create database

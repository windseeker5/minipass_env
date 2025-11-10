# Local Development Setup

Quick guide to run the MiniPass website locally on your machine.

## Prerequisites
- Python 3.8 or higher
- Git

## Setup Steps

### Step 1: Remove Old Virtual Environment (if exists)
```bash
cd /home/kdresdell/Documents/DEV/minipass_env/MinipassWebSite
rm -rf venv
```

### Step 2: Create New Virtual Environment
```bash
python3 -m venv venv
```

### Step 3: Activate Virtual Environment
```bash
source venv/bin/activate
```
You should see `(venv)` at the start of your terminal prompt.

### Step 4: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: Create Environment File
Create a `.env` file in the MinipassWebSite directory:

```bash
cat > .env << 'EOF'
# Flask Configuration
SECRET_KEY=your-secret-key-here-change-this-in-production

# Stripe Configuration (for testing, use test keys from Stripe Dashboard)
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Mail Configuration (optional for local dev - can use dummy values)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
EOF
```

**Note:** For local development/testing only, you can generate a quick SECRET_KEY:
```bash
python3 -c "import secrets; print(f'SECRET_KEY={secrets.token_hex(32)}')" >> .env
```

### Step 6: Run Flask Development Server
```bash
python app.py
```

The website will be available at: **http://localhost:5000**

## Quick Reset (if you have issues)

If something goes wrong, run these commands:
```bash
# Deactivate venv if active
deactivate

# Clean and restart
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

## Troubleshooting

### "No module named 'flask'"
- Make sure you activated the virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

### "SECRET_KEY environment variable is required!"
- Make sure you created the `.env` file in Step 5
- Check that `.env` is in the same directory as `app.py`

### Port 5000 already in use
- Stop other Flask apps or change the port in `app.py`:
  ```python
  app.run(debug=True, port=5001)
  ```

## Testing Your Changes

After making changes to templates or static files:
1. Save your changes
2. Refresh your browser (Flask auto-reloads in debug mode)
3. Check http://localhost:5000 for updates

## Stop the Server

Press `Ctrl + C` in the terminal where Flask is running.

To deactivate the virtual environment:
```bash
deactivate
```

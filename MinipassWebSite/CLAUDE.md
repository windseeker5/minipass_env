# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MiniPass is a Flask-based SaaS platform that provides automated password management app deployment. The system processes payments via Stripe, deploys containerized applications, and manages customer subdomains with integrated mail server functionality.

## Architecture

### Core Structure
- **`MinipassWebSite/app.py`** - Main Flask application with payment processing and deployment orchestration
- **`MinipassWebSite/manage_app.py`** - Customer management and cleanup utilities
- **`utils/`** - Modular helper functions:
  - `deploy_helpers.py` - Docker container deployment and admin user setup
  - `customer_helpers.py` - SQLite database operations for customer management
  - `email_helpers.py` - Flask-Mail configuration and notification system
  - `mail_manager.py` - Mail server account management and forwarding utilities
  - `mail_integration.py` - Enhanced mail server operations with comprehensive logging
  - `logging_config.py` - Centralized logging configuration for operations tracking
- **`templates/`** - Jinja2 templates for web interface
- **`static/`** - Frontend assets (CSS, JS, images)
- **`app/`** - Customer application template used for all subscription tiers
- **`migrations/`** - Database schema migration scripts

### Docker Infrastructure
- Main infrastructure runs via `docker-compose.yml` (located in parent directory)
- Nginx reverse proxy with Let's Encrypt SSL automation
- Integrated mail server with automatic email account creation
- Customer app deployment to isolated containers with unique subdomains

### Database Schema
- SQLite-based customer management (`customers.db`)
- Enhanced schema with email integration fields:
  - Basic customer info (email, subdomain, plan, port)
  - Email account details (email_address, email_password, forwarding_email)
  - Organization metadata (organization_name)
  - Deployment tracking (deployed status, created_at timestamps)

## Development Commands

### Python Environment
```bash
# Install dependencies
cd MinipassWebSite
pip install -r requirements.txt

# Run development server
python app.py

# Activate virtual environment (if using venv)
source venv/bin/activate  # or: venv\Scripts\activate on Windows
```

### Testing
```bash
# Run enhanced logging system test
cd MinipassWebSite
python test_enhanced_logging.py

# Run customer app specific tests
cd ../app && python test_payment_email.py
cd ../app && python test_admin.py

# Database migration and validation
python utils/migrate_customer_db.py
python migrations/add_email_fields.py
python migrations/add_organization_name.py
```

### Docker Operations
```bash
# Start main infrastructure (from parent directory)
cd /home/kdresdell/minipass_env
docker-compose up -d

# View running services
docker-compose ps

# Check logs
docker-compose logs -f

# Rebuild and restart containers
docker-compose down && docker-compose up -d --build
```

### Customer Management
```bash
# Interactive customer deletion tool
cd MinipassWebSite
python manage_app.py

# Mail server management utility
python utils/mail_manager.py
```

## Environment Configuration

Required environment variables in `.env`:
- `SECRET_KEY` - Flask session security
- `STRIPE_SECRET_KEY` / `STRIPE_PUBLISHABLE_KEY` - Payment processing
- `STRIPE_WEBHOOK_SECRET` - Webhook verification
- `MAIL_*` - Email configuration for deployment notifications

## Key Features

1. **Payment Processing**: Stripe integration with webhook-driven deployment
2. **Dynamic Deployment**: Automatic Docker container creation per customer
3. **Integrated Mail Server**: Automatic email account creation with forwarding
4. **Enhanced Logging**: Comprehensive operation tracking in `subscribed_app.log`
5. **Subdomain Management**: Automated DNS and SSL certificate provisioning
6. **Unified App Template**: Single app template (`app`) used for all subscription plans

## Deployment Flow

1. Customer selects plan and submits payment via Stripe
2. Stripe webhook triggers deployment process with comprehensive logging
3. App template copied from unified app folder
4. Email account created with forwarding to customer email
5. Docker container built and deployed with unique subdomain
6. Admin user created in customer app database
7. Deployment confirmation email sent with access credentials

## Enhanced Logging System

### Log File Location
All subscription operations are logged to `./subscribed_app.log` with detailed step-by-step tracking.

### Diagnostic Functions
```python
from utils.mail_integration import verify_mail_server_status, diagnose_email_setup_issue

# Check mail server health
status = verify_mail_server_status()

# Diagnose specific email issues
diagnosis = diagnose_email_setup_issue("user_app@minipass.me", "user@example.com")
```

### Log Entry Types
- 🚀 Operation start/end with context parameters
- 💻 Command execution with full output capture
- 📁 File operations (sieve scripts, configuration files)
- 🔍 Validation checks with pass/fail status
- ⚠️ Error conditions with detailed diagnostics

## Development Workflow

### Code Organization
- Flask application follows MVC pattern with clear separation of concerns
- Modular utilities in `utils/` package for reusability across app tiers
- Single customer app template serves all subscription tiers
- Database operations centralized in helper modules for consistency

### Port Management
- Dynamic port assignment handled by customer database tracking
- Each deployed customer app gets unique port allocation (starting from 8001)
- Port conflicts avoided through database coordination

### Email Integration Workflow
1. Mail account creation via Docker exec commands to mailserver container
2. Sieve script generation for email forwarding rules
3. Configuration file updates in `config/user-patches/` directory
4. Mail server container restart to activate new accounts
5. Validation checks to confirm successful setup

## Testing Strategy

- **`test_enhanced_logging.py`** - Mail server status validation and logging verification
- **`test_payment_email.py`** - Payment notification and email processing (app)
- **`test_admin.py`** - Admin authentication and database operations (app)
- **Migration scripts** - Database schema validation and updates

## Security Notes

- Passwords stored as bcrypt hashes in customer databases
- SSL certificates automatically provisioned via Let's Encrypt
- Container isolation between customer deployments
- Environment-based configuration for sensitive data
- Mail server integration with secure password generation
- Admin user authentication with secure BLOB storage for binary hashes
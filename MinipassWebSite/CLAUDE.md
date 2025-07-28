# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MiniPass is a Flask-based SaaS platform that provides automated password management app deployment. The system processes payments via Stripe, deploys containerized applications, and manages customer subdomains.

## Architecture

### Core Structure
- **`MinipassWebSite/app.py`** - Main Flask application with payment processing and deployment orchestration
- **`MinipassWebSite/manage_app.py`** - Customer management and cleanup utilities
- **`utils/`** - Modular helper functions:
  - `deploy_helpers.py` - Docker container deployment and admin user setup
  - `customer_helpers.py` - SQLite database operations for customer management
  - `email_helpers.py` - Flask-Mail configuration and notification system
  - `mail_manager.py` - Mail server account management and forwarding utilities
- **`templates/`** - Jinja2 templates for web interface
- **`static/`** - Frontend assets (CSS, JS, images)
- **`app/`, `app_beta/`, `app_o1/`** - Customer application templates for different subscription tiers
- **`tests/`** - Test suites for system validation and functionality testing

### Docker Infrastructure
- Main app runs in containerized environment via `docker-compose.yml`
- Nginx reverse proxy with Let's Encrypt SSL automation
- Mail server integration for customer notifications
- Automatic customer app deployment to isolated containers

### Database
- SQLite-based customer management (`customers.db`)
- Admin user authentication with bcrypt password hashing
- Port assignment and subdomain tracking

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
# Run tests from MinipassWebSite directory
cd MinipassWebSite
python test_enhanced_logging.py

# Run specific test files in customer apps
cd ../app_beta && python test_payment_email.py
cd ../app_o1 && python test_admin.py

# Database validation tests
python utils/migrate_customer_db.py
python migrations/add_email_fields.py
python migrations/add_organization_name.py
```

### Docker Operations
```bash
# Start main infrastructure
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

# Database migrations
cd MinipassWebSite
python migrations/add_email_fields.py
python migrations/add_organization_name.py
```

### Mail Server Management
```bash
# Mail server management utility
cd MinipassWebSite
python utils/mail_manager.py
```

## Environment Configuration

Required environment variables in `.env`:
- `SECRET_KEY` - Flask session security
- `STRIPE_SECRET_KEY` / `STRIPE_PUBLISHABLE_KEY` - Payment processing
- `STRIPE_WEBHOOK_SECRET` - Webhook verification
- `MAIL_*` - Email configuration for notifications

## Key Features

1. **Payment Processing**: Stripe integration with webhook-driven deployment
2. **Dynamic Deployment**: Automatic Docker container creation per customer
3. **Email Notifications**: Deployment confirmations and error reporting  
4. **Subdomain Management**: Automated DNS and SSL certificate provisioning
5. **Plan-based Apps**: Different app tiers (`app`, `app_beta`, `app_o1`) based on subscription

## Deployment Flow

1. Customer selects plan and submits payment
2. Stripe webhook triggers deployment process
3. App template copied based on plan selection
4. Docker container built and deployed with unique subdomain
5. Admin user created in customer database
6. Email sent with access credentials

## Development Workflow

### Code Organization
- Flask application follows MVC pattern with clear separation of concerns
- Modular utilities in `utils/` package for reusability across different app tiers
- Each customer app template (`app`, `app_beta`, `app_o1`) represents different feature sets and pricing tiers
- Database operations centralized in helper modules for consistency

### Port Management
- Dynamic port assignment handled by customer database tracking
- Each deployed customer app gets unique port allocation
- Port conflicts avoided through database coordination

### Email Integration
- Flask-Mail integration for deployment notifications and customer communication
- Email templates stored in `templates/emails/` directory
- Support for both deployment success and error notification workflows

## Testing Strategy

The codebase includes comprehensive test coverage:
- **`test_enhanced_logging.py`** - Enhanced logging system validation and mail integration testing
- **`test_payment_email.py`** - Payment notification and email processing tests
- **`test_admin.py`** - Admin user authentication and database operations testing
- **Customer app tests** - Individual testing for each app tier's functionality

## Security Notes

- Passwords stored as bcrypt hashes in customer databases
- SSL certificates automatically provisioned via Let's Encrypt
- Container isolation between customer deployments
- Environment-based configuration for sensitive data
- Admin user authentication with secure password hashing (BLOB storage for binary hashes)
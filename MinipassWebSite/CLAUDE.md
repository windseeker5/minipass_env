# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MiniPass is a Flask-based SaaS platform that provides automated password management app deployment. The system processes payments via Stripe, deploys containerized applications, and manages customer subdomains.

## Architecture

### Core Structure
- **`MinipassWebSite/app.py`** - Main Flask application with payment processing and deployment orchestration
- **`MinipassWebSite/manage.py`** - Customer management and cleanup utilities
- **`utils/`** - Modular helper functions:
  - `deploy_helpers.py` - Docker container deployment and admin user setup
  - `customer_helpers.py` - SQLite database operations for customer management
  - `email_helpers.py` - Flask-Mail configuration and notification system
- **`templates/`** - Jinja2 templates for web interface
- **`static/`** - Frontend assets (CSS, JS, images)

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
```

### Docker Operations
```bash
# Start main infrastructure
docker-compose up -d

# View running services
docker-compose ps

# Check logs
docker-compose logs -f
```

### Customer Management
```bash
# Interactive customer deletion tool
cd MinipassWebSite
python manage.py
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
5. **Plan-based Apps**: Different app tiers (`app_o1`, `app_o2`, `app_o3`) based on subscription

## Deployment Flow

1. Customer selects plan and submits payment
2. Stripe webhook triggers deployment process
3. App template copied based on plan selection
4. Docker container built and deployed with unique subdomain
5. Admin user created in customer database
6. Email sent with access credentials

## Security Notes

- Passwords stored as bcrypt hashes in customer databases
- SSL certificates automatically provisioned via Let's Encrypt
- Container isolation between customer deployments
- Environment-based configuration for sensitive data
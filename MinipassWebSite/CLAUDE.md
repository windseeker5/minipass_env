# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Application Overview

This is a Flask-based SaaS platform called "MiniPass" that offers subscription-based deployment services. The application allows users to purchase subscription plans and automatically deploys Docker containers for their applications.

### Core Architecture

- **Flask Web Application**: Main application (`app.py`) serving the frontend and handling API routes
- **Database**: SQLite database for customer management (`customers.db`)
- **Container Orchestration**: Docker Compose for deploying customer applications
- **Payment Processing**: Stripe integration for subscription payments
- **Email System**: Flask-Mail for sending deployment notifications
- **Frontend**: Bootstrap-based responsive design with custom CSS/JS

## Key Components

### Main Flask Application (`app.py`)
- Routes for home page, checkout flow, and Stripe webhooks
- Session management for checkout process
- Integration with deployment helpers and email system

### Utilities (`utils/`)
- `customer_helpers.py`: Database operations for customer management
- `deploy_helpers.py`: Container deployment and admin user setup
- `email_helpers.py`: Email configuration and sending functions

### Templates (`templates/`)
- `base.html`: Base template with navigation and footer
- `index.html`: Landing page with pricing plans and signup modal
- `deployment_progress.html`: Progress page shown during deployment

## Development Commands

### Running the Application
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables (create .env file)
# Required: STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY, STRIPE_WEBHOOK_SECRET, SECRET_KEY

# Run development server
python app.py
```

### Testing
No specific test framework is configured. Manual testing recommended for:
- Stripe payment flow
- Docker container deployment
- Email notifications
- Database operations

## Environment Variables

Required environment variables:
- `STRIPE_SECRET_KEY`: Stripe secret key for payment processing
- `STRIPE_PUBLISHABLE_KEY`: Stripe publishable key for frontend
- `STRIPE_WEBHOOK_SECRET`: Stripe webhook endpoint secret
- `SECRET_KEY`: Flask session secret key
- Email configuration variables for Flask-Mail

## Deployment Architecture

The application deploys customer containers using Docker Compose with:
- Individual containers per customer
- NGINX reverse proxy integration
- SSL certificates via Let's Encrypt
- Port assignment starting from 9100

### Plan Structure
- **Basic**: `app_o1` folder deployment
- **Pro**: `app_o2` folder deployment  
- **Ultimate**: `app_o3` folder deployment

## Database Schema

### customers table
- `id`: Primary key
- `email`: Customer email
- `subdomain`: Unique subdomain identifier
- `app_name`: Application name
- `plan`: Subscription plan (basic/pro/ultimate)
- `admin_password`: Generated admin password
- `port`: Assigned port number
- `created_at`: Timestamp
- `deployed`: Deployment status

## Important Notes

- Passwords are stored in plain text for debugging purposes
- SQLite database is used for development
- The application expects `app_o1`, `app_o2`, `app_o3` folders for deployment templates
- Customer containers are deployed to `deployed/{app_name}/` directory
- Admin users are created with bcrypt-hashed passwords in deployed applications
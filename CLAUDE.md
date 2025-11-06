# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multi-service environment hosting the Minipass SaaS platform and supporting infrastructure:

- **Main Application**: `app/` - Flask-based Minipass activities management platform
- **Security Tools**: Root-level Python scripts for fail2ban management and security monitoring
- **Infrastructure**: Docker Compose setup with nginx proxy, mail server, and SSL certificates
- **Marketing**: Static sites for bloomcap.ca and minipass.me

## Architecture

### Service Structure
- **Flask App**: Located in `app/` directory, runs on port 5000 in development
- **Production Deployment**: Multi-container Docker Compose with nginx reverse proxy
- **Mail Server**: docker-mailserver with automated SSL certificates
- **Security**: Custom fail2ban management tools with monitoring capabilities

### Key Components
- **Database**: SQLite with Flask-Migrate for schema management
- **Authentication**: Session-based authentication for admin users
- **Payment Processing**: Automated e-transfer matching via email parsing
- **Digital Passes**: QR code generation and redemption system

## Common Commands

### Development (Flask App)
```bash
# Navigate to app directory
cd app

# Virtual environment (if not active)
source venv/bin/activate

# Run tests
python -m unittest test.test_kpi_data -v
python test/test_kpi_data.py

# Database migrations
flask db migrate -m "description"
flask db upgrade

# Flask server (runs on localhost:5000)
# Note: Server is typically already running in debug mode
```

### Security Management
```bash
# Fail2ban manager
./simplified_fail2ban_manager.py --version
./secure_fail2ban_manager.py --help

# Security monitoring
./minipass_security_monitor.py --report
```

### Docker Operations
```bash
# Full stack deployment
docker-compose up -d

# Specific service management
docker-compose restart lhgi
docker-compose logs -f mailserver

# SSL certificate management (automatic via Let's Encrypt)
```

## Important Notes

### Development Environment
- **Flask Server**: Always runs on `localhost:5000` in debug mode
- **Main Application**: All core development happens in `app/` directory
- **Testing**: Use unittest framework for Python tests
- **Database**: SQLite located at `app/instance/minipass.db`

### Deployment
- **Production**: Multi-container setup with nginx proxy
- **SSL**: Automated Let's Encrypt certificates
- **Mail**: Full mailserver with fail2ban protection
- **Domains**: minipass.me (main), lhgi.minipass.me (customer), bloomcap.ca (marketing)

### Security Configuration
- **Fail2ban**: Custom management scripts with enhanced monitoring
- **Email Security**: Automated parsing with security validation
- **Permission Management**: Extensive bash command allowlist in `.claude/settings.local.json`

### Code Organization
- **Main App Logic**: Concentrated in `app/app.py` (~66k lines)
- **Models**: Defined in `app/models.py`
- **Business Logic**: Helper functions in `app/utils.py`
- **Templates**: Jinja2 templates using Tabler.io CSS framework

For detailed Flask application development guidelines, see `app/CLAUDE.md`.
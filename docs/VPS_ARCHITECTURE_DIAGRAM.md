# MiniPass VPS Architecture Diagram

## Network Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          INTERNET (Public Traffic)                          │
└────────────────────────┬────────────────────────┬───────────────────────────┘
                         │                        │
                    Port 80/443              Port 25/587/993
                         │                        │
                         ▼                        ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                    VPS: 138.199.152.128 (minipass.me)                      │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                     DOCKER NETWORK: proxy                             │ │
│  │                                                                       │ │
│  │  ┌─────────────────────────────────────────────────────────────┐    │ │
│  │  │  nginx-proxy (jwilder/nginx-proxy)                          │    │ │
│  │  │  - Listens: 0.0.0.0:80, 0.0.0.0:443                         │    │ │
│  │  │  - Auto-configures virtual hosts from container env vars    │    │ │
│  │  │  - Proxies HTTP/HTTPS to backend containers                 │    │ │
│  │  └────────┬────────────────┬──────────────────┬─────────────────┘    │ │
│  │           │                │                  │                       │ │
│  │           │                │                  │                       │ │
│  │  ┌────────▼────────┐  ┌────▼─────────┐  ┌────▼──────────────┐       │ │
│  │  │ lhgi Container  │  │ bloomcap     │  │ flask-controller- │       │ │
│  │  │ (Customer App)  │  │ (Static)     │  │ proxy (nginx)     │       │ │
│  │  ├─────────────────┤  ├──────────────┤  ├───────────────────┤       │ │
│  │  │ Flask App       │  │ nginx:alpine │  │ nginx:alpine      │       │ │
│  │  │ Port: 8889      │  │ Port: 80     │  │ Port: 80          │       │ │
│  │  │ Domain:         │  │ Domain:      │  │ Domain:           │       │ │
│  │  │ lhgi.minipass.me│  │ bloomcap.ca  │  │ minipass.me       │       │ │
│  │  │                 │  │              │  │ www.minipass.me   │       │ │
│  │  │ Volumes:        │  │              │  │                   │       │ │
│  │  │ ./app/instance  │  │              │  │ Proxies to:       │       │ │
│  │  │ → /app/instance │  │              │  │ host.docker.      │       │ │
│  │  │                 │  │              │  │ internal:5000     │       │ │
│  │  │ Database:       │  │              │  │ (MinipassWebSite) │       │ │
│  │  │ /app/instance/  │  │              │  │                   │       │ │
│  │  │ minipass.db     │  │              │  │                   │       │ │
│  │  │                 │  │              │  │                   │       │ │
│  │  │ Email Sender:   │  │              │  │                   │       │ │
│  │  │ lhgi_app@       │  │              │  │                   │       │ │
│  │  │ minipass.me     │  │              │  │                   │       │ │
│  │  └─────────────────┘  └──────────────┘  └───────────────────┘       │ │
│  │                                                                       │ │
│  │  ┌─────────────────────────────────────────────────────────────┐    │ │
│  │  │  mailserver (docker-mailserver)                             │    │ │
│  │  │  - Ports: 25, 143, 587, 993                                 │    │ │
│  │  │  - Hostname: mail.minipass.me                               │    │ │
│  │  │  - Volumes:                                                 │    │ │
│  │  │    ./maildata → /var/mail                                   │    │ │
│  │  │    ./mailstate → /var/mail-state                            │    │ │
│  │  │    ./config → /tmp/docker-mailserver                        │    │ │
│  │  │  - Handles ALL outgoing emails from:                        │    │ │
│  │  │    • MinipassWebSite (support@minipass.me)                  │    │ │
│  │  │    • Customer apps (lhgi_app@minipass.me, etc.)             │    │ │
│  │  └─────────────────────────────────────────────────────────────┘    │ │
│  │                                                                       │ │
│  │  ┌─────────────────────────────────────────────────────────────┐    │ │
│  │  │  nginx-letsencrypt (acme-companion)                         │    │ │
│  │  │  - Auto-provisions SSL certificates                         │    │ │
│  │  │  - Watches container env vars: LETSENCRYPT_HOST             │    │ │
│  │  └─────────────────────────────────────────────────────────────┘    │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                    VPS HOST (NOT CONTAINERIZED)                       │ │
│  │                                                                       │ │
│  │  ┌─────────────────────────────────────────────────────────────┐    │ │
│  │  │  MinipassWebSite/ (Main SaaS Platform)                      │    │ │
│  │  │  - Flask App: app.py                                        │    │ │
│  │  │  - Port: 5000 (localhost only)                              │    │ │
│  │  │  - Accessed via: flask-controller-proxy → minipass.me       │    │ │
│  │  │                                                              │    │ │
│  │  │  Database:                                                  │    │ │
│  │  │  • customers.db (customer registry, email accounts)         │    │ │
│  │  │                                                              │    │ │
│  │  │  Email System:                                              │    │ │
│  │  │  • utils/email_helpers.py                                   │    │ │
│  │  │  • Sends: deployment notifications, password resets         │    │ │
│  │  │  • Sender: support@minipass.me                              │    │ │
│  │  │  • SMTP: mail.minipass.me:587 (mailserver container)        │    │ │
│  │  │                                                              │    │ │
│  │  │  Logs:                                                      │    │ │
│  │  │  • subscribed_app.log (deployment operations)               │    │ │
│  │  └─────────────────────────────────────────────────────────────┘    │ │
│  │                                                                       │ │
│  │  ┌─────────────────────────────────────────────────────────────┐    │ │
│  │  │  app/ (Customer App Template - SOURCE CODE)                 │    │ │
│  │  │  - Used to build lhgi container and future customers        │    │ │
│  │  │  - Contains: app.py, utils.py, templates/, models.py        │    │ │
│  │  │  - Email system: send_email() in utils.py                   │    │ │
│  │  └─────────────────────────────────────────────────────────────┘    │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Email Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           EMAIL SENDING FLOW                             │
└──────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────┐         ┌──────────────────────────────┐
│  MinipassWebSite (Host)     │         │  lhgi Container              │
│  Port: 5000                 │         │  Port: 8889                  │
├─────────────────────────────┤         ├──────────────────────────────┤
│                             │         │                              │
│  Deployment Email:          │         │  Pass Confirmation:          │
│  • To: customer@gmail.com   │         │  • To: user@gmail.com        │
│  • From: support@minipass.me│         │  • From: lhgi_app@minipass.me│
│  • Function:                │         │  • Function:                 │
│    send_user_deployment_    │         │    send_email()              │
│    email()                  │         │    in utils.py               │
│                             │         │                              │
│  Password Reset:            │         │  Survey Invitation:          │
│  • To: customer@gmail.com   │         │  • To: user@gmail.com        │
│  • From: support@minipass.me│         │  • From: lhgi_app@minipass.me│
│  • Function:                │         │  • Function:                 │
│    send_password_reset_     │         │    send_email()              │
│    email()                  │         │                              │
│                             │         │                              │
└──────────────┬──────────────┘         └──────────────┬───────────────┘
               │                                       │
               │  SMTP Connection                      │
               │  mail.minipass.me:587                 │
               │  TLS + Auth                           │
               │                                       │
               └───────────────┬───────────────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │  mailserver Container         │
               │  Port: 587 (SMTP/TLS)         │
               ├───────────────────────────────┤
               │  Accounts:                    │
               │  • support@minipass.me        │
               │  • lhgi_app@minipass.me       │
               │  • admin@minipass.me          │
               │  • (other customers)          │
               │                               │
               │  Config:                      │
               │  • postfix-accounts.cf        │
               │  • postfix-virtual.cf         │
               │  • opendkim/ (DKIM signing)   │
               └───────────────┬───────────────┘
                               │
                               │ Port 25 (SMTP)
                               │ to external servers
                               ▼
               ┌───────────────────────────────┐
               │  External Mail Servers        │
               │  (Gmail, etc.)                │
               └───────────────────────────────┘
```

## File System Structure on VPS

```
/home/kdresdell/Documents/DEV/minipass_env/
│
├── docker-compose.yml                    # Infrastructure definition
│
├── MinipassWebSite/                      # Main SaaS platform (HOST-BASED)
│   ├── app.py                            # Flask app (port 5000)
│   ├── customers.db                      # Customer registry
│   ├── subscribed_app.log                # Deployment logs (1.6 MB)
│   └── utils/
│       ├── email_helpers.py              # ⚠️ EMAIL SYSTEM - NEEDS RFC FIXES
│       ├── deploy_helpers.py             # Docker deployment logic
│       └── mail_integration.py           # Mail server management
│
├── app/                                  # Customer app template (SOURCE)
│   ├── app.py                            # Flask app template
│   ├── utils.py                          # ⚠️ EMAIL SYSTEM - NEEDS RFC FIXES
│   ├── models.py                         # Database models (EmailLog table)
│   ├── instance/
│   │   └── minipass.db                   # LHGI customer database (local dev)
│   └── templates/email_templates/        # Email templates
│
├── maildata/                             # Mail server storage
├── mailstate/                            # Mail server state
├── config/                               # Mail server config
│   ├── postfix-accounts.cf               # Mail accounts list
│   ├── postfix-virtual.cf                # Virtual aliases
│   └── opendkim/                         # DKIM signing keys
│
├── certs/                                # SSL certificates (Let's Encrypt)
│   ├── mail.minipass.me/                 # Mail server cert
│   ├── lhgi.minipass.me/                 # Customer cert
│   └── minipass.me/                      # Main site cert
│
└── deployed/ (EMPTY in dev)              # Future: Additional customer deployments
```

## Email Log Locations

```
┌──────────────────────────────────────────────────────────────────┐
│                        EMAIL LOGS                                │
└──────────────────────────────────────────────────────────────────┘

MinipassWebSite Emails:
  ✅ subscribed_app.log         (file-based, operations log)
  ❌ No database logging        (Flask-Mail doesn't log to DB)
  ✅ Docker logs: N/A           (runs on host)

Customer App Emails (lhgi):
  ✅ EmailLog table             (in /app/instance/minipass.db)
  ✅ stdout logs                (captured by Docker)
  ✅ Docker logs: docker logs lhgi

Mail Server:
  ✅ Postfix logs               (inside mailserver container)
  ✅ Docker logs: docker logs mailserver
```

## Deployment Flow (What Happens When Customer Subscribes)

```
1. Customer pays via Stripe
   └─> Webhook received by MinipassWebSite (app.py)

2. MinipassWebSite processes subscription
   ├─> Creates customer record in customers.db
   ├─> Generates subdomain (e.g., "newcustomer")
   └─> Triggers deployment

3. Email Account Creation
   ├─> Connects to mailserver container
   ├─> Creates newcustomer_app@minipass.me
   ├─> Updates postfix-accounts.cf
   └─> Restarts mailserver

4. Customer App Deployment
   ├─> Copies /app template to new directory
   ├─> Builds Docker container
   ├─> Exposes on unique port (e.g., 8890)
   ├─> nginx-proxy auto-configures newcustomer.minipass.me
   └─> SSL cert auto-provisioned by nginx-letsencrypt

5. Database Initialization
   ├─> Creates /app/instance/minipass.db in container
   ├─> Injects email settings (mail.minipass.me:587)
   └─> Creates admin user

6. Notification Email Sent
   └─> MinipassWebSite sends deployment email
       via send_user_deployment_email()
       (FROM: support@minipass.me)
```

---

## QUESTIONS FOR YOU TO VERIFY:

1. ✅ Is MinipassWebSite running directly on the VPS host (NOT in a container)?
2. ✅ Does it listen on localhost:5000?
3. ✅ Is the "deployed" folder currently empty (no actual customer deployments yet)?
4. ✅ Do ALL emails (from both systems) go through the mailserver container?
5. ✅ Is LHGI the only deployed customer container right now?
6. ❓ Are there any OTHER customer containers deployed that I should know about?
7. ❓ Is there any email sending code I missed besides:
   - app/utils.py send_email()
   - MinipassWebSite/utils/email_helpers.py (3 functions)

Please review this diagram and tell me what's WRONG or what I'm MISSING!

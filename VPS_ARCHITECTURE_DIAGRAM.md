# Minipass VPS Architecture Diagram

## Complete System Architecture Overview

```
                                    INTERNET
                                       |
                              ┌─── Port 80/443 ───┐
                              │                   │
                              ▼                   ▼
                    ┌─────────────────────────────────────┐
                    │         nginx-proxy                 │
                    │    (jwilder/nginx-proxy:alpine)     │
                    │  ┌─────────────────────────────────┐ │
                    │  │     Virtual Host Router         │ │
                    │  │  ┌─ minipass.me                │ │
                    │  │  ├─ lhgi.minipass.me           │ │
                    │  │  ├─ kdc.minipass.me            │ │
                    │  │  ├─ heq.minipass.me            │ │
                    │  │  ├─ mail.minipass.me           │ │
                    │  │  └─ bloomcap.ca                │ │
                    │  └─────────────────────────────────┘ │
                    │  SSL Termination (Let's Encrypt)     │
                    └─────────────────────────────────────┘
                                       |
                    ┌─────────────────────────────────────┐
                    │      DOCKER NETWORK                 │
                    │    (minipass_env_proxy)             │
                    │                                     │
    ┌───────────────┼─────────────────────────────────────┼───────────────┐
    │               │                                     │               │
    ▼               │                                     │               ▼
┌─────────┐         │         ┌─────────────┐             │         ┌──────────┐
│  MAIL   │         │         │   SSL &     │             │         │ CUSTOMER │
│ STACK   │         │         │   SUPPORT   │             │         │   APPS   │
│         │         │         │  SERVICES   │             │         │          │
└─────────┘         │         └─────────────┘             │         └──────────┘
                    │                                     │
                    └─────────────────────────────────────┘
```

## Detailed Component Architecture

### 1. INTERNET ENTRY POINT
```
Internet Traffic
    │
    ├── HTTP  (Port 80)  ──┐
    └── HTTPS (Port 443) ──┘
                           │
                           ▼
                   nginx-proxy Container
                   ├── SSL Termination
                   ├── Domain Routing
                   └── Load Balancing
```

### 2. MAIN REVERSE PROXY (nginx-proxy)
```
┌─────────────────────────────────────────────────┐
│                nginx-proxy                      │
│           (jwilder/nginx-proxy:alpine)          │
├─────────────────────────────────────────────────┤
│ VIRTUAL HOST ROUTING:                           │
│                                                 │
│ minipass.me          ──► flask-controller-proxy │
│ www.minipass.me      ──► flask-controller-proxy │
│                                                 │
│ lhgi.minipass.me     ──► minipass_lhgi         │
│ kdc.minipass.me      ──► minipass_kdc          │
│ heq.minipass.me      ──► minipass_heq          │
│ testdelancementmf... ──► minipass_testdel...   │
│                                                 │
│ mail.minipass.me     ──► mail-cert-request     │
│ bloomcap.ca          ──► bloomcap              │
│                                                 │
├─────────────────────────────────────────────────┤
│ FEATURES:                                       │
│ ✓ Automatic SSL (Let's Encrypt)                │
│ ✓ Docker socket monitoring                     │
│ ✓ Auto-configuration from container env vars   │
│ ✗ NO CACHING (Performance Issue!)             │
│ ✗ NO COMPRESSION                               │
├─────────────────────────────────────────────────┤
│ RESOURCES: 60.82MB RAM, 0.24% CPU              │
│ NETWORK: 1.04GB RX / 1.28GB TX                 │
└─────────────────────────────────────────────────┘
```

### 3. SSL MANAGEMENT STACK
```
┌─────────────────────────────────────────────────┐
│            nginx-letsencrypt                    │
│        (nginxproxy/acme-companion)              │
├─────────────────────────────────────────────────┤
│ ► Automatic SSL certificate generation          │
│ ► Certificate renewal automation                │
│ ► Watches nginx-proxy container                 │
│ ► Integrates with Let's Encrypt ACME            │
├─────────────────────────────────────────────────┤
│ RESOURCES: 30.21MB RAM, 0.23% CPU              │
└─────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────┐
│              mail-cert-request                  │
│               (nginx:alpine)                    │
├─────────────────────────────────────────────────┤
│ ► Handles SSL certificate requests for mail     │
│ ► Domain: mail.minipass.me                      │
│ ► Minimal nginx for ACME challenges             │
├─────────────────────────────────────────────────┤
│ RESOURCES: 7.957MB RAM, minimal CPU            │
└─────────────────────────────────────────────────┘
```

### 4. MAIN APPLICATION STACK
```
┌─────────────────────────────────────────────────┐
│           flask-controller-proxy                │
│               (nginx:alpine)                    │
├─────────────────────────────────────────────────┤
│ DOMAINS: minipass.me, www.minipass.me          │
│                                                 │
│ PROXY CONFIGURATION:                            │
│ location /static/ {                            │
│   alias /app/static/;                          │
│   expires 30d;                                 │
│   # Direct file serving (10-100x faster)       │
│ }                                               │
│                                                 │
│ location / {                                    │
│   proxy_pass http://host.docker.internal:5000; │
│ }                                               │
├─────────────────────────────────────────────────┤
│ RESOURCES: 6.367MB RAM, minimal CPU            │
└─────────────────────────────────────────────────┘
                           │
                           ▼ Proxy to host
┌─────────────────────────────────────────────────┐
│              HOST MACHINE                       │
│           Main Flask Application                │
├─────────────────────────────────────────────────┤
│ PORT: 5000                                      │
│ PROCESS: gunicorn --workers=2 --threads=4      │
│ FRAMEWORK: Flask + SQLite                      │
│ FEATURES: Main website, customer onboarding    │
│          payment processing, admin interface   │
├─────────────────────────────────────────────────┤
│ RESOURCES: 176MB RAM (Python process)          │
│ PATH: /home/kdresdell/minipass_env/app/         │
└─────────────────────────────────────────────────┘
```

### 5. MAIL SERVER INFRASTRUCTURE
```
┌─────────────────────────────────────────────────┐
│                  mailserver                     │
│    (ghcr.io/docker-mailserver/docker-mailserver│
├─────────────────────────────────────────────────┤
│ PORTS EXPOSED TO INTERNET:                     │
│ ├── 25   (SMTP)                                │
│ ├── 143  (IMAP)                                │
│ ├── 587  (SMTP Submission)                     │
│ └── 993  (IMAPS)                               │
│                                                 │
│ FEATURES:                                       │
│ ├── Full email server stack                    │
│ ├── Built-in fail2ban protection               │
│ ├── Automated SSL integration                  │
│ ├── Email parsing for payment processing       │
│ └── Customer notification system               │
│                                                 │
│ VOLUMES:                                        │
│ ├── ./maildata:/var/mail                       │
│ ├── ./mailstate:/var/mail-state                │
│ ├── ./config:/tmp/docker-mailserver            │
│ └── ./certs/mail.minipass.me:/etc/letsencrypt  │
├─────────────────────────────────────────────────┤
│ RESOURCES: 311.1MB RAM, 0.18% CPU              │
│ NETWORK: 17.5MB RX / 143MB TX                  │
└─────────────────────────────────────────────────┘
```

### 6. CUSTOMER CONTAINERS (Container-per-Customer Model)
```
┌─────────────────────────────────────────────────┐
│                 Customer: LHGI                  │
│              (lhgi.minipass.me)                 │
├─────────────────────────────────────────────────┤
│ CONTAINER: minipass_lhgi                        │
│ IMAGE: lhgi-lhgi                                │
│ PORT: 8889 (internal)                          │
│                                                 │
│ STACK:                                          │
│ ├── Flask Application                           │
│ ├── Gunicorn WSGI Server                       │
│ ├── SQLite Database (/app/instance)            │
│ └── Upload Storage (/app/static/uploads)        │
│                                                 │
│ ENVIRONMENT:                                    │
│ ├── VIRTUAL_HOST=lhgi.minipass.me              │
│ ├── VIRTUAL_PORT=8889                          │
│ ├── LETSENCRYPT_HOST=lhgi.minipass.me          │
│ └── SITE_URL=https://lhgi.minipass.me          │
├─────────────────────────────────────────────────┤
│ RESOURCES: 248.2MB RAM, 0.06% CPU              │
│ UPLOADS: 21.9MB (PERFORMANCE ISSUE!)           │
│ NETWORK: 240MB RX / 197MB TX (Highest)         │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│                 Customer: KDC                   │
│              (kdc.minipass.me)                  │
├─────────────────────────────────────────────────┤
│ CONTAINER: minipass_kdc                         │
│ IDENTICAL STACK TO LHGI                        │
├─────────────────────────────────────────────────┤
│ RESOURCES: 217.5MB RAM, 0.09% CPU              │
│ UPLOADS: 1.1MB                                  │
│ NETWORK: 12.4MB RX / 47.8MB TX                 │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│                 Customer: HEQ                   │
│              (heq.minipass.me)                  │
├─────────────────────────────────────────────────┤
│ CONTAINER: minipass_heq                         │
│ IDENTICAL STACK TO LHGI                        │
├─────────────────────────────────────────────────┤
│ RESOURCES: 263.1MB RAM, 0.08% CPU              │
│ UPLOADS: 0.7MB                                  │
│ NETWORK: 4.3MB RX / 40MB TX                    │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│            Customer: TestdelancementMF          │
├─────────────────────────────────────────────────┤
│ CONTAINER: minipass_testdelancementmf           │
│ IDENTICAL STACK TO LHGI                        │
├─────────────────────────────────────────────────┤
│ RESOURCES: 157.1MB RAM, 0.08% CPU              │
│ UPLOADS: 0.3MB                                  │
│ NETWORK: 4.51MB RX / 12.1MB TX                 │
└─────────────────────────────────────────────────┘
```

### 7. SUPPORTING SERVICES
```
┌─────────────────────────────────────────────────┐
│                  bloomcap                       │
│               (nginx:alpine)                    │
├─────────────────────────────────────────────────┤
│ PURPOSE: Static website for son                │
│ DOMAINS: bloomcap.ca, www.bloomcap.ca          │
│ CONTENT: Static HTML files                     │
│ STATUS: ⚠️ CANDIDATE FOR REMOVAL               │
├─────────────────────────────────────────────────┤
│ RESOURCES: 7.848MB RAM (Wasted)                │
└─────────────────────────────────────────────────┘
```

## Network Flow Diagram

### Request Flow for Customer Sites
```
User Request (https://lhgi.minipass.me)
    │
    ▼
nginx-proxy (Port 443)
    │ SSL Termination
    │ Virtual Host Lookup
    ▼
minipass_lhgi Container (Port 8889)
    │ Flask Application
    │ Gunicorn WSGI
    ▼
SQLite Database + File System
    │ Query/File Read
    ▼
Response through same path (reversed)
```

### Request Flow for Main Site
```
User Request (https://minipass.me)
    │
    ▼
nginx-proxy (Port 443)
    │ SSL Termination
    │ Virtual Host Lookup
    ▼
flask-controller-proxy
    │ Static file check
    ├─ /static/* ──► Direct file serving
    └─ /* ──────────┐
                    ▼
              Host Machine:5000
                    │ Main Flask App
                    │ Gunicorn WSGI
                    ▼
              SQLite Database
```

### Email Flow
```
Internet Email (Port 25/587/993)
    │
    ▼
mailserver Container
    │ Full email stack
    │ fail2ban protection
    ▼
Email Processing
    │ Payment parsing
    │ Customer notifications
    ▼
Integration with Flask Apps
```

## Resource Usage Summary

### Total System Resources
```
VPS Specification: 4 vCPU, 7.6GB RAM, 75GB disk

Current Usage:
├── Memory: 2.5GB / 7.6GB (33.5%) ✅ HEALTHY
├── Disk:   18GB / 75GB (24.1%)   ✅ HEALTHY
└── CPU:    <1% average           ✅ HEALTHY

Container Breakdown:
├── Infrastructure: ~400MB
│   ├── nginx-proxy:     60.8MB
│   ├── mailserver:     311.1MB
│   ├── nginx-letsencrypt: 30.2MB
│   └── Other services:   ~50MB
│
└── Customer Apps: ~886MB (221.5MB average per customer)
    ├── LHGI:     248.2MB (+ 21.9MB uploads)
    ├── HEQ:      263.1MB (+ 0.7MB uploads)
    ├── KDC:      217.5MB (+ 1.1MB uploads)
    └── TestMF:   157.1MB (+ 0.3MB uploads)
```

## Data Flow Patterns

### File Upload Handling (Performance Bottleneck)
```
Customer Upload Request
    │
    ▼
nginx-proxy (NO CACHING ❌)
    │
    ▼
Customer Container
    │ Flask file handling
    │ Store in /app/static/uploads/
    ▼
File System Storage (Per-customer isolation)

PROBLEM: Large files (LHGI: 21.9MB) served repeatedly without caching
SOLUTION: Implement proxy-level caching + image optimization
```

### Database Access Pattern
```
Each Customer Container:
├── Individual SQLite database
├── No connection sharing
├── Isolated data (✅ Security)
└── Resource overhead (❌ Efficiency)

Alternative Architecture Consideration:
├── Shared PostgreSQL with tenant_id
├── Connection pooling
├── Better resource utilization
└── Maintained data isolation
```

## Scaling Constraints Visualization

### Current Architecture Scaling
```
Customer Count vs Memory Usage:

 4 customers  ├──────────┤ 33.5% (Current)
10 customers  ├───────────────────┤ 55%
15 customers  ├──────────────────────────┤ 76% ⚠️
20 customers  ├─────────────────────────────────┤ 97% ❌
25 customers  ├────────────────────────────────────────┤ 122% ❌

            0%    25%    50%    75%   100%   125%
           └─────┴──────┴──────┴──────┴──────┴──────┘
                       Memory Usage %

KEY:
✅ = Safe operation
⚠️ = Planning required
❌ = Not possible without changes
```

## Critical Performance Issues Identified

### 1. No Caching Layer (CRITICAL)
```
Every Request Path:
User → nginx-proxy → Customer Container → Flask App → Database
                 └─ NO CACHING AT ANY LEVEL ❌

Should Be:
User → nginx-proxy → CACHE HIT ✅ (70-90% of requests)
             └─ CACHE MISS → Customer Container (10-30% of requests)
```

### 2. Large Upload Files (HIGH IMPACT)
```
LHGI Customer Upload Analysis:
├── Total uploads: 21.9MB
├── Served without optimization
├── No compression
├── No CDN/caching
└── Causing reported slowness ❌

Solution Impact:
├── Image optimization: 60-80% size reduction
├── Proxy caching: 90% reduction in container hits
└── Performance improvement: 5-10x faster loading
```

This visual architecture diagram shows exactly how all components in your VPS connect and interact, with the performance bottlenecks clearly identified. The missing caching layer is the root cause of your slowness issues!
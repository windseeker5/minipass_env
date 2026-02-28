# Minipass VPS Architecture Documentation

Generated on: 2026-02-27

## Executive Summary

This document provides a comprehensive analysis of the Minipass SaaS platform VPS infrastructure, including architecture diagrams, resource utilization, performance bottlenecks, and optimization recommendations.

## VPS Specifications

- **Provider**: VPS hosting
- **CPU**: 4 vCPU Intel Xeon Processor (Skylake, IBRS, no TSX)
- **RAM**: 7.6GB total (5.2GB available)
- **Storage**: 75GB SSD (19GB used, 26% utilization)
- **OS**: Ubuntu Linux 6.8.0-100-generic
- **Docker**: Latest with docker-compose

## Current Architecture Overview

```
Internet (Port 80/443)
    ↓
nginx-proxy (jwilder/nginx-proxy)
    ├── SSL Termination (Let's Encrypt)
    ├── Virtual Host Routing
    └── Load Balancing
    ↓
┌─────────────────────────────────────────────────────┐
│                Container Network                    │
│                (minipass_env_proxy)                 │
├─────────────────────────────────────────────────────┤
│ Main Application Stack                              │
│ ├── flask-controller-proxy → Host:5000 (Main App)   │
│ └── mailserver (Full Email Stack)                   │
├─────────────────────────────────────────────────────┤
│ Customer Containers (Container-per-Customer)        │
│ ├── minipass_lhgi (lhgi.minipass.me)               │
│ ├── minipass_kdc (kdc.minipass.me)                 │
│ ├── minipass_heq (heq.minipass.me)                 │
│ └── minipass_testdelancementmf                     │
├─────────────────────────────────────────────────────┤
│ Supporting Services                                 │
│ ├── nginx-letsencrypt (SSL Automation)             │
│ ├── mail-cert-request (Mail SSL)                   │
│ └── bloomcap (Static Website)                       │
└─────────────────────────────────────────────────────┘
```

## Detailed Component Analysis

### 1. Core Infrastructure Components

#### nginx-proxy (Main Reverse Proxy)
- **Image**: jwilder/nginx-proxy:alpine
- **Ports**: 80, 443 (Internet-facing)
- **Function**: Routes requests to appropriate containers based on VIRTUAL_HOST
- **Resource Usage**: 60.82MiB RAM, 0.24% CPU
- **Network I/O**: 1.04GB received / 1.28GB sent

#### nginx-letsencrypt (SSL Management)
- **Image**: nginxproxy/acme-companion
- **Function**: Automated Let's Encrypt certificate generation and renewal
- **Resource Usage**: 30.21MiB RAM, 0.23% CPU

#### mailserver (Email Infrastructure)
- **Image**: docker-mailserver/docker-mailserver:latest
- **Ports**: 25, 143, 587, 993 (SMTP, IMAP, IMAPS)
- **Resource Usage**: 311.1MiB RAM, 0.18% CPU
- **Volumes**: maildata, mailstate, config directories
- **Function**: Full email server with fail2ban protection

### 2. Main Application (Host-Based)

#### Main Minipass Application
- **Location**: Host machine (not containerized)
- **Port**: 5000
- **Framework**: Flask with Gunicorn
- **Process**: `/usr/local/bin/gunicorn --workers=2 --threads=4 --bind=0.0.0.0:8889 app:app`
- **Resource Usage**: 176MB RAM (Python process)
- **Access**: Via flask-controller-proxy container

#### flask-controller-proxy
- **Image**: nginx:alpine
- **Function**: Proxy to main Flask app on host:5000
- **Domains**: minipass.me, www.minipass.me
- **Caching**: Basic gzip compression enabled

### 3. Customer Containers (Container-per-Customer Model)

Each customer gets an isolated container with:
- **Dedicated Flask application instance**
- **Individual SQLite database**
- **Separate uploads directory**
- **Unique subdomain routing**

#### Current Customer Containers:
1. **minipass_lhgi** (lhgi.minipass.me)
   - Resource Usage: 248.2MiB RAM, 0.06% CPU
   - Upload Size: 22MB (largest - performance concern)
   - Network I/O: 240MB / 197MB

2. **minipass_kdc** (kdc.minipass.me)
   - Resource Usage: 217.5MiB RAM, 0.09% CPU
   - Upload Size: 1.2MB
   - Network I/O: 12.4MB / 47.8MB

3. **minipass_heq** (heq.minipass.me)
   - Resource Usage: 263.1MiB RAM, 0.06% CPU
   - Upload Size: 752KB
   - Network I/O: 4.3MB / 40MB

4. **minipass_testdelancementmf**
   - Resource Usage: 157.1MiB RAM, 0.08% CPU
   - Upload Size: 332KB
   - Network I/O: 4.51MB / 12.1MB

### 4. Supporting Services

#### bloomcap (Static Website)
- **Image**: nginx:alpine
- **Domains**: bloomcap.ca, www.bloomcap.ca
- **Resource Usage**: 7.848MiB RAM, minimal CPU
- **Note**: Candidate for removal to simplify architecture

## Resource Utilization Analysis

### Current Resource Consumption
- **Total RAM Usage**: ~2.3GB / 7.6GB (30% utilization)
- **Total CPU Usage**: ~1% average
- **Network I/O**: Varies by customer usage
- **Disk Usage**: 19GB / 75GB (25% utilization)

### Per-Customer Resource Footprint
- **Average RAM**: ~200MB per customer container
- **Average CPU**: 0.06-0.09% per customer
- **Base Infrastructure**: ~500MB RAM for core services

### Scaling Capacity Estimation
Based on current resource usage:
- **Conservative Estimate**: 30-35 customers (leaving 2GB RAM buffer)
- **Optimistic Estimate**: 40-50 customers (with optimization)
- **Bottleneck**: RAM will be the limiting factor before CPU

## Performance Issues Identified

### Critical Performance Bottlenecks

1. **No Caching at Proxy Level**
   - Customer containers serve all requests directly
   - No static asset caching in nginx-proxy
   - Large uploads (22MB in LHGI) not cached

2. **Upload Size Issues**
   - LHGI customer has 22MB of uploads
   - No image compression or optimization
   - Direct file serving without CDN benefits

3. **Limited vhost Configurations**
   - Only basic `client_max_body_size 50M` set
   - No caching headers for static assets
   - No compression for customer container responses

4. **Database Per Container**
   - SQLite per container increases I/O
   - No shared connection pooling
   - Backup complexity multiplied by customer count

## Network Architecture

### Port Mapping
- **80/443**: nginx-proxy (Internet-facing)
- **25, 587**: SMTP (mailserver)
- **143, 993**: IMAP/IMAPS (mailserver)
- **5000**: Main Flask app (host)
- **8889**: Customer container internal port

### Domain Routing
- **minipass.me**: Main application (host Flask app)
- **{customer}.minipass.me**: Customer-specific containers
- **mail.minipass.me**: Mail server SSL certificate
- **bloomcap.ca**: Static website

### Docker Networks
- **minipass_env_proxy**: Single bridge network for all services
- **External connectivity**: Through nginx-proxy container

## Architecture Strengths

1. **Isolation**: Each customer has complete isolation
2. **Security**: Container boundaries prevent cross-customer access
3. **Scalability**: Easy to add new customers
4. **SSL Management**: Automated certificate generation
5. **Email Integration**: Full email server with security

## Architecture Weaknesses

1. **Resource Overhead**: ~200MB RAM per customer
2. **No Caching**: Poor performance for repeated requests
3. **Complex Deployment**: Multiple containers to manage
4. **Backup Complexity**: Individual databases per customer
5. **No Load Balancing**: Single point of failure per customer

## Alternative Architecture Considerations

### Option 1: Shared Application with Tenant Isolation
- Single Flask application with multi-tenancy
- Shared database with tenant_id isolation
- ~80% RAM reduction
- Increased complexity in application layer

### Option 2: Microservices Architecture
- Separate services for auth, content, billing
- Horizontal scaling potential
- Higher operational complexity

### Option 3: Kubernetes Migration
- Better resource utilization
- Auto-scaling capabilities
- Significant operational overhead increase

## Immediate Optimization Opportunities

### High Impact, Low Effort
1. **Enable nginx-proxy caching** for static assets
2. **Add compression** to customer container responses
3. **Image optimization** for uploads
4. **Remove bloomcap** container to free resources

### Medium Impact, Medium Effort
1. **Implement CDN** for static assets
2. **Database optimization** with connection pooling
3. **Monitoring setup** for resource tracking
4. **Backup automation** for customer databases

### High Impact, High Effort
1. **Architecture migration** to shared tenancy
2. **Kubernetes deployment**
3. **Separate storage layer** (PostgreSQL cluster)

## Monitoring Recommendations

### Resource Monitoring
- Docker stats collection every minute
- Disk usage alerts at 80% capacity
- Memory alerts at 85% utilization
- Network I/O tracking per customer

### Performance Monitoring
- Response time tracking per customer
- Upload processing time monitoring
- Database query performance
- SSL certificate expiry tracking

## Next Steps

1. Implement caching optimizations
2. Set up comprehensive monitoring
3. Plan customer migration strategy for growth
4. Evaluate alternative architectures
5. Create automated backup system

---

*This document should be updated monthly or when significant architecture changes occur.*
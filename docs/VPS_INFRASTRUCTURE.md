# Minipass VPS Infrastructure Documentation

**Generated**: March 7, 2026
**Business Plan Reference**: Complete infrastructure mapping for scaling analysis

## Executive Summary

This document provides the complete infrastructure mapping of the Minipass SaaS platform VPS. The current setup supports 4 customers using 31.8% of system resources. **Business scaling capacity: 15 customers maximum** on this VPS before requiring migration to a larger server or cluster deployment.

## VPS Specifications

- **Provider**: VPS hosting
- **CPU**: 4 vCPU Intel Xeon Processor
- **RAM**: 7.6GB total
- **Storage**: 75GB SSD
- **OS**: Ubuntu Linux 6.8.0-100-generic
- **Current Utilization**: 31.8% memory, 24% disk

## Complete Infrastructure Deployment Map

*Disaster Recovery View: Every component that needs to be rebuilt if VPS crashes*

```mermaid
graph TB
    subgraph "Internet Entry"
        INT[🌐 Internet Traffic<br/>Ports: 80, 443, 25, 587, 993]
    end

    subgraph "Core Infrastructure Containers"
        PROXY[📦 nginx-proxy<br/>jwilder/nginx-proxy:alpine<br/>61MB RAM<br/>Routing & SSL termination]
        SSL[📦 nginx-letsencrypt<br/>nginxproxy/acme-companion<br/>30MB RAM<br/>SSL certificate automation]
        MAILCERT[📦 mail-cert-request<br/>nginx:alpine<br/>8MB RAM<br/>Mail SSL handling]
    end

    subgraph "Host Services"
        HOSTAPP[🖥️ Main Flask Application<br/>Host Process Port 5000<br/>176MB RAM<br/>minipass.me main site]
        FLASKPROXY[📦 flask-controller-proxy<br/>nginx:alpine<br/>6MB RAM<br/>Proxy to host app]
    end

    subgraph "Mail Infrastructure"
        MAILSERVER[📦 mailserver<br/>docker-mailserver<br/>311MB RAM<br/>Full email stack]
    end

    subgraph "Customer Containers (4 Active)"
        LHGI[📦 minipass_lhgi<br/>Flask app container<br/>280MB RAM + 22MB uploads<br/>lhgi.minipass.me]
        KDC[📦 minipass_kdc<br/>Flask app container<br/>218MB RAM + 1MB uploads<br/>kdc.minipass.me]
        HEQ[📦 minipass_heq<br/>Flask app container<br/>250MB RAM + 1MB uploads<br/>heq.minipass.me]
        TESTDEL[📦 minipass_testdel<br/>Flask app container<br/>157MB RAM + 1MB uploads<br/>testdelancementmf.minipass.me]
    end

    subgraph "Supporting Services"
        BLOOM[📦 bloomcap<br/>nginx:alpine<br/>8MB RAM<br/>Static site: bloomcap.ca<br/>(Optional - can be removed)]
    end

    %% Connections
    INT --> PROXY
    PROXY --> FLASKPROXY
    PROXY --> LHGI
    PROXY --> KDC
    PROXY --> HEQ
    PROXY --> TESTDEL
    PROXY --> MAILCERT
    PROXY --> BLOOM

    FLASKPROXY --> HOSTAPP
    SSL --> PROXY
    MAILCERT --> MAILSERVER

    classDef critical fill:#ffcccb,stroke:#d32f2f,stroke-width:3px
    classDef customer fill:#e1f5fe,stroke:#0288d1,stroke-width:2px
    classDef infrastructure fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef optional fill:#fff3e0,stroke:#f57c00,stroke-width:1px

    class PROXY,SSL,MAILSERVER,HOSTAPP critical
    class LHGI,KDC,HEQ,TESTDEL customer
    class FLASKPROXY,MAILCERT infrastructure
    class BLOOM optional
```

## Infrastructure Components Breakdown

### Critical Components (Cannot be removed)
1. **nginx-proxy** - Routes all web traffic, handles SSL termination
2. **nginx-letsencrypt** - Manages SSL certificates automatically
3. **mailserver** - Complete email infrastructure with security
4. **Host Flask Application** - Main Minipass platform (runs on host, not containerized)

### Customer Application Containers
Each customer receives an isolated container with:
- **Individual Flask application** (identical codebase, separate instances)
- **Dedicated SQLite database**
- **Isolated upload storage**
- **Unique subdomain routing**

**Current Customers:**
- **LHGI** (280MB RAM) - Largest customer with 22MB uploads
- **KDC** (218MB RAM) - Medium usage
- **HEQ** (250MB RAM) - Standard usage
- **TestdelancementMF** (157MB RAM) - Test/development customer

### Supporting Infrastructure
- **flask-controller-proxy** - Nginx proxy for main site static files
- **mail-cert-request** - Handles SSL for mail domain
- **bloomcap** - Optional static website (can be removed to free 8MB RAM)

## Container-per-Customer Business Model

### Current Resource Usage (4 Customers)
- **Total Memory**: 2.4GB / 7.6GB (31.8% utilization)
- **Average per Customer**: 221MB RAM
- **Infrastructure Overhead**: ~500MB for core services
- **Remaining Capacity**: 5.2GB available

### Scaling Analysis for Business Planning

| Customer Count | Memory Usage | Capacity Status | Business Action |
|---------------|--------------|-----------------|-----------------|
| **4 (Current)** | 2.4GB (31.8%) | ✅ Healthy | Continue operations |
| **8 customers** | ~4.2GB (55%) | ✅ Good | Normal scaling |
| **12 customers** | ~5.8GB (76%) | ⚠️ Monitor | Plan for transition |
| **15 customers** | ~6.8GB (89%) | ⚠️ Maximum | **SCALING LIMIT** |
| **18+ customers** | >7.6GB (100%+) | ❌ Impossible | Requires new VPS |

### **Business Critical Finding**: 15 Customer Maximum
- **Current VPS supports maximum 15 customers** before performance degradation
- **At 15 customers**: ~89% memory utilization (safe operational limit)
- **Beyond 15 customers**: Must deploy new VPS or migrate to cluster architecture

## Disaster Recovery Deployment Checklist

If VPS crashes completely, deploy in this order:

### Phase 1: Core Infrastructure
1. **nginx-proxy** container (traffic routing)
2. **nginx-letsencrypt** container (SSL automation)
3. **mailserver** container (email infrastructure)

### Phase 2: Main Application
1. **Deploy Host Flask Application** (port 5000)
2. **flask-controller-proxy** container
3. **mail-cert-request** container

### Phase 3: Customer Applications
1. **minipass_lhgi** container
2. **minipass_kdc** container
3. **minipass_heq** container
4. **minipass_testdel** container
5. **Restore customer databases and uploads**

### Phase 4: Optional Services
1. **bloomcap** container (if required)

## Resource Optimization Status

### Completed Optimizations (February 2026)
- ✅ **Gzip compression**: 72% size reduction on all responses
- ✅ **Browser caching**: 30-day static asset caching
- ✅ **Memory optimization**: Reduced from 33.5% to 31.8% utilization

### Performance Metrics
- **Static assets**: Load instantly on repeat visits (browser cache)
- **All content**: 72% smaller due to compression
- **Upload handling**: Optimized for large files

## Network Architecture

### Port Mapping
- **Port 80/443**: nginx-proxy (all web traffic)
- **Port 25, 587**: SMTP email (mailserver)
- **Port 993**: IMAPS email (mailserver)
- **Port 5000**: Main Flask app (internal, host-based)
- **Port 8889**: Customer container internal port

### Domain Routing
- **minipass.me** → Main application (host Flask app via proxy)
- **lhgi.minipass.me** → LHGI customer container
- **kdc.minipass.me** → KDC customer container
- **heq.minipass.me** → HEQ customer container
- **testdelancementmf.minipass.me** → Test customer container
- **mail.minipass.me** → Mail server SSL
- **bloomcap.ca** → Static website (optional)

## Business Growth Strategy

### Current Phase (1-15 customers)
- **Architecture**: Container-per-customer on single VPS
- **Scaling**: Add containers as customers onboard
- **Resource monitoring**: Track memory usage approaching 85%

### Transition Phase (15+ customers)
- **Option 1**: Deploy second identical VPS
- **Option 2**: Migrate to cluster architecture (Docker Swarm)
- **Option 3**: Move to shared multi-tenant application

### Recommended Scaling Path
1. **0-15 customers**: Optimize current VPS architecture
2. **15-30 customers**: Deploy second VPS with load balancing
3. **30+ customers**: Evaluate cluster or multi-tenant architecture

## Monthly Resource Monitoring

Track these metrics for business planning:
- **Memory utilization trend**
- **Customer onboarding rate**
- **Performance metrics per customer**
- **Storage usage growth**

**Alert Thresholds**:
- 80% memory usage: Plan scaling
- 85% memory usage: Initiate scaling
- 90% memory usage: Emergency scaling required

---

**Business Planning Summary**: Current VPS supports sustainable growth to 15 customers. Beyond 15 customers, infrastructure scaling is required for continued service quality.
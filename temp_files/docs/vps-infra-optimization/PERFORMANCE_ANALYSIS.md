# Performance Bottleneck Analysis & Caching Strategy

Generated: 2026-02-27

## Executive Summary

This document analyzes performance bottlenecks in the Minipass VPS architecture and provides specific caching strategies to address the identified slowness issues.

## Key Performance Issues Identified

### 1. Critical Issue: No Caching Layer
**Impact**: HIGH - Directly causing slowness experienced by users
**Evidence**: No proxy-level caching configuration detected in nginx-proxy setup

**Current Request Flow (Inefficient):**
```
User Request → nginx-proxy → Customer Container → Flask App → Database → Response
                ↓
        Every request hits application layer
        No static asset caching
        No API response caching
```

### 2. Large Upload Files Causing Slowness
**Impact**: HIGH - LHGI customer has 21.9MB of uploads
**Details**:
- LHGI customer: 21.9MB uploads (95% of total customer uploads)
- Other customers: <2MB each
- No image optimization or compression
- Files served directly from container filesystem

### 3. Container Resource Overhead
**Impact**: MEDIUM - 221MB average per customer container
**Details**:
- Each customer runs full Flask+Gunicorn stack
- Separate Python processes per customer
- No resource sharing between customers

### 4. Lack of Static Asset Optimization
**Impact**: MEDIUM
**Issues**:
- No CDN for static assets
- No browser caching headers
- No gzip compression at proxy level
- No asset bundling/minification

## Detailed Caching Strategy

### Level 1: Nginx Proxy Caching (IMMEDIATE - HIGH IMPACT)

#### A. Static Asset Caching
Create `/home/kdresdell/minipass_env/nginx-proxy-cache.conf`:

```nginx
# Cache configuration for nginx-proxy
proxy_cache_path /var/cache/nginx/proxy levels=1:2 keys_zone=my_cache:10m max_size=1g
                 inactive=60m use_temp_path=off;

# Static assets - Long term caching
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
    proxy_cache my_cache;
    proxy_cache_valid 200 30d;
    proxy_cache_valid 404 1m;
    proxy_cache_use_stale error timeout invalid_header updating http_500 http_502 http_503 http_504;
    proxy_cache_lock on;
    add_header X-Cache-Status $upstream_cache_status;
    expires 30d;
    add_header Cache-Control "public, max-age=2592000, immutable";
}

# API responses - Short term caching
location /api/ {
    proxy_cache my_cache;
    proxy_cache_valid 200 5m;
    proxy_cache_valid 404 1m;
    proxy_cache_methods GET HEAD;
    proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
    add_header X-Cache-Status $upstream_cache_status;
}

# Upload files - Medium term caching
location /static/uploads/ {
    proxy_cache my_cache;
    proxy_cache_valid 200 1h;
    proxy_cache_use_stale error timeout invalid_header updating http_500 http_502 http_503 http_504;
    add_header X-Cache-Status $upstream_cache_status;
    expires 1h;
}
```

#### B. Compression Configuration
```nginx
# Compression settings
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_proxied expired no-cache no-store private auth;
gzip_types
    text/plain
    text/css
    text/xml
    text/javascript
    application/javascript
    application/xml+rss
    application/json
    application/xml
    image/svg+xml;
```

### Level 2: Customer Container Optimization

#### A. Individual Customer vhost Configurations
For each customer, create optimized vhost.d configurations:

**LHGI (High Upload Volume):**
```nginx
# /home/kdresdell/minipass_env/vhost.d/lhgi.minipass.me
client_max_body_size 50M;

# Aggressive caching for uploads
location /static/uploads/ {
    expires 1d;
    add_header Cache-Control "public, max-age=86400";
    add_header Vary "Accept-Encoding";
}

# Cache other static assets
location /static/ {
    expires 7d;
    add_header Cache-Control "public, max-age=604800, immutable";
}

# API response caching
location /api/ {
    expires 5m;
    add_header Cache-Control "public, max-age=300";
}
```

#### B. Image Optimization Strategy
Create automatic image compression for customer uploads:

```python
# Image optimization script for customer deployments
def optimize_customer_uploads():
    customers = ['lhgi', 'kdc', 'heq', 'testdelancementmf']

    for customer in customers:
        uploads_path = f"/home/kdresdell/minipass_env/deployed/{customer}/app/static/uploads"

        # Compress images > 1MB
        # Convert PNG to WebP for better compression
        # Implement progressive JPEG
        # Add responsive image sizing
```

### Level 3: Application-Level Caching

#### A. Flask Application Caching
For each customer container, implement:
- Redis-based session storage (shared)
- Database query result caching
- Template rendering caching
- API response caching with Flask-Caching

#### B. Database Optimization
- Implement connection pooling
- Add database query caching
- Optimize frequently accessed queries
- Consider shared database for non-sensitive data

## Immediate Action Plan

### Phase 1: Quick Wins (1-2 hours implementation)

1. **Configure nginx-proxy caching**
   - Add cache volume to docker-compose.yml
   - Create cache configuration file
   - Restart nginx-proxy container

2. **Optimize customer vhost configurations**
   - Add caching headers for static assets
   - Configure compression settings
   - Update upload size limits where needed

3. **Remove bloomcap container**
   - Save ~8MB RAM
   - Reduce container count
   - Simplify architecture

### Phase 2: Medium-term improvements (1-2 days)

1. **Implement image optimization**
   - Compress existing LHGI uploads
   - Add automatic optimization pipeline
   - Convert large images to WebP format

2. **Add monitoring for cache effectiveness**
   - Cache hit rate monitoring
   - Response time improvements
   - Bandwidth savings tracking

### Phase 3: Long-term optimization (1-2 weeks)

1. **Evaluate architecture alternatives**
2. **Implement shared services**
3. **Add CDN integration**
4. **Database optimization**

## Expected Performance Improvements

### Immediate (Phase 1)
- **50-80% reduction** in response time for static assets
- **30-50% reduction** in bandwidth usage
- **20-40% improvement** in page load times
- **Elimination of slowness** for LHGI customer uploads

### Medium-term (Phase 2)
- **60-70% reduction** in upload file sizes (LHGI)
- **Additional 20-30%** improvement in load times
- **Reduced container resource usage**

### Long-term (Phase 3)
- **80-90% improvement** in overall system performance
- **Significantly better scalability**
- **Reduced resource consumption per customer**

## Cache Configuration Implementation

### 1. Update docker-compose.yml
```yaml
nginx-proxy:
  image: jwilder/nginx-proxy:alpine
  volumes:
    - nginx-cache:/var/cache/nginx/proxy
    - ./nginx-proxy-cache.conf:/etc/nginx/conf.d/cache.conf:ro
```

### 2. Customer-Specific vhost Files
Create optimized configurations for each customer based on their usage patterns.

### 3. Monitoring Setup
Implement cache hit rate monitoring and performance tracking.

## Risk Assessment

### Low Risk Implementations
- Static asset caching
- Gzip compression
- Browser cache headers

### Medium Risk Implementations
- API response caching (ensure proper cache invalidation)
- Database query caching

### High Risk Implementations
- Architecture changes (container-per-customer to shared)
- Database consolidation

## Testing Strategy

1. **A/B Testing**: Compare performance before/after caching
2. **Load Testing**: Simulate multiple customer usage
3. **Monitoring**: Track cache hit rates and response times
4. **User Feedback**: Monitor customer reported performance

## Conclusion

The primary cause of the experienced slowness is the lack of any caching layer in the current architecture. Implementing the Phase 1 improvements should immediately address the performance issues experienced with the LHGI customer and provide a solid foundation for future scaling.

The recommended approach prioritizes low-risk, high-impact improvements that can be implemented quickly while laying groundwork for more significant architectural optimizations in the future.
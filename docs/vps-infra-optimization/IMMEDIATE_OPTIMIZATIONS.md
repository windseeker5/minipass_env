# Immediate Optimization Implementation Guide

Generated: 2026-02-27

## Priority 1: Critical Performance Fixes (1-2 hours)

These optimizations will directly address the slowness issues experienced with your beta customers.

### 1. Enable Nginx Proxy Caching

#### Step 1: Create Cache Configuration

Create `/home/kdresdell/minipass_env/nginx/cache.conf`:
```nginx
# Cache path configuration
proxy_cache_path /var/cache/nginx/proxy levels=1:2 keys_zone=minipass_cache:50m max_size=2g inactive=60m use_temp_path=off;

# Cache for static assets (CSS, JS, images)
location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot|pdf)$ {
    proxy_cache minipass_cache;
    proxy_cache_valid 200 7d;
    proxy_cache_valid 404 1m;
    proxy_cache_use_stale error timeout invalid_header updating http_500 http_502 http_503 http_504;
    proxy_cache_lock on;
    proxy_cache_revalidate on;

    add_header X-Cache-Status $upstream_cache_status;
    add_header Cache-Control "public, max-age=604800, immutable";
    expires 7d;
}

# Cache for uploads (customer files)
location /static/uploads/ {
    proxy_cache minipass_cache;
    proxy_cache_valid 200 1h;
    proxy_cache_valid 404 1m;
    proxy_cache_use_stale error timeout invalid_header updating http_500 http_502 http_503 http_504;
    proxy_cache_lock on;

    add_header X-Cache-Status $upstream_cache_status;
    add_header Cache-Control "public, max-age=3600";
    expires 1h;
}

# Cache for API responses (short-term)
location ~ ^/api/ {
    proxy_cache minipass_cache;
    proxy_cache_valid 200 5m;
    proxy_cache_valid 404 30s;
    proxy_cache_methods GET HEAD;
    proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;

    add_header X-Cache-Status $upstream_cache_status;
    add_header Cache-Control "public, max-age=300";
}

# Global compression settings
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_proxied any;
gzip_comp_level 6;
gzip_types
    text/plain
    text/css
    text/xml
    text/javascript
    application/javascript
    application/xml+rss
    application/json
    application/xml
    image/svg+xml
    text/html;
```

#### Step 2: Update Docker Compose for Caching

Update `/home/kdresdell/minipass_env/docker-compose.yml`:
```yaml
nginx-proxy:
  image: jwilder/nginx-proxy:alpine
  container_name: nginx-proxy
  restart: always
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - /var/run/docker.sock:/tmp/docker.sock:ro
    - ./certs:/etc/nginx/certs:rw
    - ./vhost.d:/etc/nginx/vhost.d
    - ./html:/usr/share/nginx/html
    - ./acme:/etc/acme.sh
    - ./nginx/cache.conf:/etc/nginx/conf.d/cache.conf:ro  # Add this line
    - nginx-cache:/var/cache/nginx/proxy                   # Add this line
  networks:
    - proxy

# Add cache volume at bottom of file
volumes:
  nginx-cache:
    driver: local
```

### 2. Optimize Customer vhost Configurations

#### For LHGI (High Upload Volume Customer)
Create `/home/kdresdell/minipass_env/vhost.d/lhgi.minipass.me_location`:
```nginx
# Increase upload limits for high-volume customer
client_max_body_size 100M;
client_body_timeout 120s;
proxy_read_timeout 120s;

# Aggressive caching for uploads
location /static/uploads/ {
    expires 4h;
    add_header Cache-Control "public, max-age=14400";
    add_header Vary "Accept-Encoding";

    # Enable compression for large files
    gzip on;
    gzip_types image/svg+xml application/json text/css;
}

# Cache static assets longer
location /static/ {
    expires 1d;
    add_header Cache-Control "public, max-age=86400, immutable";
}

# Short caching for dynamic content
location / {
    add_header Cache-Control "private, max-age=0, no-cache";
}
```

#### For Other Customers (Standard Configuration)
Create `/home/kdresdell/minipass_env/vhost.d/kdc.minipass.me_location` (and similar for heq, testdelancementmf):
```nginx
client_max_body_size 20M;

# Standard asset caching
location /static/ {
    expires 12h;
    add_header Cache-Control "public, max-age=43200";
}

location / {
    add_header Cache-Control "private, max-age=0, no-cache";
}
```

### 3. Remove Unnecessary Services

#### Remove Bloomcap Container
```bash
# Stop and remove bloomcap container
docker-compose stop bloomcap
docker-compose rm -f bloomcap

# Remove from docker-compose.yml (lines 102-116)
# This will save ~8MB RAM and simplify architecture
```

## Priority 2: Image Optimization for LHGI Customer (2-4 hours)

### Image Compression Script

Create `/home/kdresdell/minipass_env/optimize_customer_uploads.py`:
```python
#!/usr/bin/env python3
"""
Customer Upload Optimization Script
Compresses and optimizes images for better performance
"""

import os
import sys
from PIL import Image, ImageOps
import subprocess
from pathlib import Path

def optimize_images_in_directory(directory_path, customer_name):
    """Optimize all images in a directory"""
    print(f"🖼️ Optimizing images for {customer_name}...")

    total_saved = 0
    files_processed = 0

    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                file_path = os.path.join(root, file)
                saved_bytes = optimize_single_image(file_path)
                if saved_bytes > 0:
                    total_saved += saved_bytes
                    files_processed += 1

    print(f"✅ Processed {files_processed} images")
    print(f"💾 Total space saved: {total_saved / 1024 / 1024:.2f} MB")
    return total_saved

def optimize_single_image(file_path):
    """Optimize a single image file"""
    try:
        original_size = os.path.getsize(file_path)

        # Skip files smaller than 100KB
        if original_size < 100 * 1024:
            return 0

        with Image.open(file_path) as img:
            # Fix orientation
            img = ImageOps.exif_transpose(img)

            # Convert RGBA to RGB if saving as JPEG
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if 'A' in img.mode else None)
                img = background

            # Resize if too large (max 1920px width)
            if img.width > 1920:
                ratio = 1920 / img.width
                new_height = int(img.height * ratio)
                img = img.resize((1920, new_height), Image.Resampling.LANCZOS)

            # Save optimized version
            optimize_params = {
                'optimize': True,
                'quality': 85
            }

            if file_path.lower().endswith('.png'):
                # For PNG, convert to JPEG if no transparency
                if img.mode == 'RGB':
                    new_path = file_path.rsplit('.', 1)[0] + '_optimized.jpg'
                    img.save(new_path, 'JPEG', **optimize_params)

                    # Replace original if smaller
                    new_size = os.path.getsize(new_path)
                    if new_size < original_size:
                        os.replace(new_path, file_path.rsplit('.', 1)[0] + '.jpg')
                        os.remove(file_path)
                        print(f"📉 Converted PNG to JPG: {os.path.basename(file_path)} ({original_size - new_size} bytes saved)")
                        return original_size - new_size
                    else:
                        os.remove(new_path)
            else:
                # For JPEG, optimize in place
                img.save(file_path, 'JPEG', **optimize_params)
                new_size = os.path.getsize(file_path)
                saved = original_size - new_size
                if saved > 0:
                    print(f"📉 Optimized {os.path.basename(file_path)}: {saved} bytes saved")
                return saved

    except Exception as e:
        print(f"❌ Error optimizing {file_path}: {e}")
        return 0

    return 0

def main():
    customers = ['lhgi', 'kdc', 'heq', 'testdelancementmf']
    base_path = Path('/home/kdresdell/minipass_env/deployed')

    total_savings = 0

    for customer in customers:
        uploads_path = base_path / customer / 'app' / 'static' / 'uploads'
        if uploads_path.exists():
            savings = optimize_images_in_directory(uploads_path, customer)
            total_savings += savings
        else:
            print(f"⚠️ No uploads directory found for {customer}")

    print(f"\n🎉 Total optimization complete!")
    print(f"💾 Total space saved across all customers: {total_savings / 1024 / 1024:.2f} MB")

if __name__ == '__main__':
    main()
```

Make it executable:
```bash
chmod +x optimize_customer_uploads.py
```

### Install Required Dependencies
```bash
pip3 install Pillow
```

## Priority 3: Enhanced Monitoring (1 hour)

### Customer Performance Monitoring Script

Create `/home/kdresdell/minipass_env/performance_monitor.py`:
```python
#!/usr/bin/env python3
"""
Performance Monitoring Script
Tracks customer response times and resource usage
"""

import time
import requests
import json
from datetime import datetime
import subprocess

def check_customer_response_time(domain, timeout=30):
    """Check response time for a customer domain"""
    try:
        start_time = time.time()
        response = requests.get(f"https://{domain}", timeout=timeout, allow_redirects=True)
        response_time = time.time() - start_time

        return {
            'domain': domain,
            'response_time': round(response_time, 3),
            'status_code': response.status_code,
            'success': response.status_code == 200,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'domain': domain,
            'response_time': timeout,
            'status_code': 0,
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def get_container_stats():
    """Get current container resource usage"""
    try:
        result = subprocess.run([
            'docker', 'stats', '--no-stream', '--format',
            'table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}'
        ], capture_output=True, text=True)

        lines = result.stdout.strip().split('\n')[1:]  # Skip header
        stats = []

        for line in lines:
            parts = line.split('\t')
            if len(parts) >= 3:
                container, cpu, memory = parts[0], parts[1], parts[2]
                stats.append({
                    'container': container,
                    'cpu_percent': cpu,
                    'memory_usage': memory,
                    'timestamp': datetime.now().isoformat()
                })

        return stats
    except Exception as e:
        print(f"Error getting container stats: {e}")
        return []

def main():
    """Run performance monitoring check"""
    customers = [
        'lhgi.minipass.me',
        'kdc.minipass.me',
        'heq.minipass.me',
        'minipass.me'  # Main site
    ]

    print("🔍 Checking customer response times...")
    response_times = []

    for customer in customers:
        result = check_customer_response_time(customer)
        response_times.append(result)

        status = "✅" if result['success'] else "❌"
        print(f"{status} {customer}: {result['response_time']}s")

    print("\n📊 Getting container resource usage...")
    container_stats = get_container_stats()

    # Save results
    report = {
        'timestamp': datetime.now().isoformat(),
        'response_times': response_times,
        'container_stats': container_stats
    }

    with open(f'performance_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
        json.dump(report, f, indent=2)

    # Print summary
    avg_response_time = sum(r['response_time'] for r in response_times if r['success']) / len([r for r in response_times if r['success']])
    print(f"\n📈 Average successful response time: {avg_response_time:.3f}s")

    failed_customers = [r['domain'] for r in response_times if not r['success']]
    if failed_customers:
        print(f"⚠️ Failed customers: {', '.join(failed_customers)}")

if __name__ == '__main__':
    main()
```

## Implementation Order

### Phase 1: Cache Implementation (30 minutes)
```bash
# 1. Create cache configuration
mkdir -p nginx
# Create cache.conf file as shown above

# 2. Update docker-compose.yml
# Add cache volume and configuration mount

# 3. Restart nginx-proxy with caching
docker-compose up -d nginx-proxy

# 4. Verify caching is working
curl -I https://lhgi.minipass.me/static/uploads/some-image.jpg
# Look for X-Cache-Status header
```

### Phase 2: Customer vhost Optimization (30 minutes)
```bash
# 1. Create customer-specific vhost files
# Files created as shown in examples above

# 2. Restart nginx-proxy to pick up new configurations
docker-compose restart nginx-proxy

# 3. Test customer sites for performance improvement
python3 performance_monitor.py
```

### Phase 3: Image Optimization (1-2 hours)
```bash
# 1. Install dependencies
pip3 install Pillow

# 2. Run image optimization
python3 optimize_customer_uploads.py

# 3. Restart customer containers to clear any cached references
docker-compose restart lhgi minipass_kdc minipass_heq minipass_testdelancementmf
```

### Phase 4: Remove Unnecessary Services (15 minutes)
```bash
# 1. Stop and remove bloomcap
docker-compose stop bloomcap
docker-compose rm -f bloomcap

# 2. Comment out bloomcap service in docker-compose.yml

# 3. Verify system resources freed up
docker stats --no-stream
```

## Expected Results

### Performance Improvements
- **Static asset loading**: 70-90% faster (cached after first load)
- **LHGI customer uploads**: 50-80% faster due to caching + optimization
- **Overall page load times**: 40-60% improvement
- **Bandwidth usage**: 30-50% reduction

### Resource Savings
- **RAM freed**: ~8MB from removing bloomcap
- **Storage saved**: Estimated 10-15MB from image optimization
- **Bandwidth costs**: Significant reduction due to caching

### Monitoring Benefits
- **Response time tracking**: Baseline measurements for future optimizations
- **Resource usage alerts**: Early warning for capacity issues
- **Performance regression detection**: Catch issues before customers notice

## Rollback Plan

If any issues arise:
1. **Cache issues**: Remove cache.conf mount and restart nginx-proxy
2. **vhost issues**: Remove problematic vhost files and restart
3. **Image optimization issues**: Restore from backup (create backup first!)
4. **Container issues**: Roll back to previous docker-compose.yml

## Testing Checklist

- [ ] Cache headers present in HTTP responses
- [ ] Static assets loading faster after first request
- [ ] Customer sites still functional
- [ ] Upload functionality working (especially LHGI)
- [ ] No broken images after optimization
- [ ] Performance monitoring script running successfully
- [ ] Overall system stability maintained

This implementation plan should directly address the slowness issues you experienced with your beta customers while maintaining system stability.
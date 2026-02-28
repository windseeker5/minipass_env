# NEXT STEP: Nginx Caching — Phase 4

**Status:** Deferred — implement directly on VPS when ready
**Context:** Components 1–3 of the cover photo performance fix are already deployed (upload compression, retroactive migration, crop tool). This document covers Component 4.

---

## Why We Skipped This (For Now)

Components 1–3 already solve the core problem: new uploads are auto-compressed from ~7MB to ~120–200KB (60x reduction). Component 4 adds browser-level caching so returning users get images from their local disk cache instead of the network. It's a meaningful improvement but not urgent — the compression fix is the high-impact change.

Component 4 requires working directly on the VPS because it involves Docker container configuration and path mappings that differ between local dev and production.

---

## Your Complete VPS Network Architecture

```
INTERNET (browsers, phones)
         │
         │ TCP port 80 (HTTP) & 443 (HTTPS)
         ▼
┌─────────────────────────────────────────────────────────────┐
│  nginx-proxy  (jwilder/nginx-proxy:alpine)                  │
│                                                             │
│  THE MASTER TRAFFIC COP                                     │
│  - Listens on ports 80 and 443 (the ONLY container that     │
│    binds to the public internet)                            │
│  - Reads VIRTUAL_HOST env var from every container          │
│  - Auto-generates routing rules: "if hostname = X, send     │
│    traffic to container Y"                                  │
│  - Does SSL termination (decrypts HTTPS, sends plain HTTP   │
│    internally to containers)                                │
└───────────────────────┬─────────────────────────────────────┘
                        │ routes by hostname, plain HTTP internally
          ┌─────────────┼───────────────────────────────┐
          │             │             │                  │
          ▼             ▼             ▼                  ▼
  ┌──────────────┐ ┌──────────┐ ┌──────────────┐ ┌──────────────┐
  │minipass_lhgi │ │minipass_ │ │minipass_kdc  │ │minipass_     │
  │              │ │heq       │ │              │ │testlancement │
  │VIRTUAL_HOST= │ │          │ │VIRTUAL_HOST= │ │mf            │
  │lhgi.minipass │ │VIRTUAL_  │ │kdc.minipass  │ │              │
  │.me           │ │HOST=heq. │ │.me           │ │VIRTUAL_HOST= │
  │              │ │minipass. │ │              │ │testlancement │
  │gunicorn      │ │me        │ │gunicorn      │ │mf.minipass.me│
  │port 8889     │ │          │ │port 8889     │ │              │
  │Flask app     │ │gunicorn  │ │Flask app     │ │gunicorn      │
  │(copy of      │ │port 8889 │ │(copy of      │ │port 8889     │
  │your app)     │ │Flask app │ │your app)     │ │Flask app     │
  └──────────────┘ └──────────┘ └──────────────┘ └──────────────┘

          │             │             │                  │
          └─────────────┴─────────────┴──────────────────┘
                        │
                        │ all on shared Docker network
                        │ "minipass_env_proxy"
          ┌─────────────┼───────────────────────────────┐
          │             │             │                  │
          ▼             ▼             ▼                  ▼
  ┌──────────────┐ ┌──────────┐ ┌──────────────┐ ┌──────────────┐
  │flask-        │ │bloomcap  │ │mailserver    │ │nginx-        │
  │controller-   │ │          │ │              │ │letsencrypt   │
  │proxy         │ │VIRTUAL_  │ │ports 25/143/ │ │              │
  │              │ │HOST=     │ │587/993       │ │Watches       │
  │VIRTUAL_HOST= │ │bloomcap  │ │(email server)│ │Docker events,│
  │minipass.me   │ │.ca       │ │              │ │auto-requests │
  │www.minipass  │ │          │ │              │ │SSL certs via │
  │.me           │ │serves    │ │              │ │Let's Encrypt │
  │              │ │static    │ │              │ │for every     │
  │nginx proxies │ │HTML files│ │              │ │LETSENCRYPT_  │
  │→ HOST:5000   │ │          │ │              │ │HOST it sees  │
  └──────┬───────┘ └──────────┘ └──────────────┘ └──────────────┘
         │
         │ host.docker.internal:5000
         │ (escapes Docker network, goes to VPS host OS)
         ▼
  ┌─────────────────────────────────────────────────┐
  │  Flask app — running directly on VPS HOST       │
  │  as a systemd service: minipass-web.service     │
  │  port 5000                                      │
  │                                                 │
  │  This is your main app — the one you develop    │
  │  locally and deploy here. NOT containerized.    │
  └─────────────────────────────────────────────────┘
```

---

## Two Different Deployment Patterns on Your VPS

You have two completely different ways apps run:

| | Customer apps (lhgi, heq, kdc, mf) | Main app (minipass.me) |
|---|---|---|
| **Runs as** | Docker container | systemd service on host |
| **Port** | 8889 (gunicorn) | 5000 (Flask dev server) |
| **Static files** | Inside container at `/app/static/` | On host at `~/minipass_env/app/static/` |
| **Config** | `docker-compose.yml` per customer in `deployed/` | `nginx/controller-proxy.conf` as bridge container |
| **Network** | `minipass_env_proxy` Docker network | `host.docker.internal:5000` via `flask-controller-proxy` |

---

## What Nginx Caching Actually Means

Two separate things are often called "nginx caching" — they are different:

| Thing | What it does | Where the cache lives |
|---|---|---|
| **Browser cache headers** | nginx tells the browser "cache this file for 30 days" | User's browser disk |
| **Nginx proxy cache** | nginx stores a copy of the app's response on the server disk | VPS disk |

The plan only uses **browser cache headers** — the simpler, safer option. No server-side cache storage involved.

### The Caching Hierarchy (fastest to slowest)

```
1. Browser disk cache   → 0ms    — file already on user's device
2. Nginx static serving → <1ms   — file read from disk by nginx (C, zero-copy)
3. Flask static serving → 5–20ms — Python processes the request
4. SQLite query         → 1–10ms — disk I/O for dynamic data
```

Before the compression fix: every page load hits layer 3 (Flask) for a 7MB PNG.
After compression (already done): same layer 3 but for a 120KB JPEG.
After caching (Phase 4): returning users hit layer 1 (browser cache, 0ms). First-time users hit layer 2 (nginx direct, <1ms). Flask never sees a static file request again.

---

## The Request Path Right Now (Without Caching)

A request for `minipass.me/static/uploads/cover.jpg` travels through **TWO nginx hops** before reaching Flask:

```
Browser
  → nginx-proxy        (SSL termination, routes by hostname)
    → flask-controller-proxy  (proxies everything to Flask)
      → Flask on host:5000    (Python serves the file)
```

With Phase 4, the path for static files becomes:

```
Browser
  → nginx-proxy        (SSL termination, routes by hostname)
    → flask-controller-proxy  (serves file directly from disk, skips Flask)
```

---

## Why Nginx is 10–100x Faster Than Flask for Static Files

Flask is Python. Every static file request wakes up the Python interpreter, runs code, and copies memory. Nginx is written in C and uses `sendfile()` — a Linux kernel call that moves bytes from disk to network without copying through application memory ("zero-copy"). For a page with 5 images, the difference is ~100ms vs ~5ms.

---

## Implementation Plan for Phase 4

### Step 1 — Main app (minipass.me): `flask-controller-proxy`

**File:** `nginx/controller-proxy.conf` (already updated locally — ready to deploy)

```nginx
gzip on;
gzip_types text/plain text/css application/javascript application/json;
gzip_min_length 256;
gzip_vary on;

server {
    listen 80;
    server_name minipass.me www.minipass.me;

    # Serve static files directly — bypass Flask entirely
    location /static/ {
        alias /app/static/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000, immutable";
        access_log off;
    }

    location / {
        proxy_pass http://host.docker.internal:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

**File:** `docker-compose.yml` — add static volume to `flask-controller-proxy`:

```yaml
flask-controller-proxy:
  volumes:
    - ./nginx/controller-proxy.conf:/etc/nginx/conf.d/default.conf:ro
    - ./app/static:/app/static:ro     # ADD THIS LINE
```

The `:ro` (read-only) mount ensures nginx can never write to the static folder.

**Why `immutable` in Cache-Control:** UUID filenames (`upload_a7c3f29b12.jpg`) guarantee that a new upload always gets a new URL. The browser can safely cache the file forever — if the user changes their photo, the new file gets a new name. The old cached URL is simply never requested again.

**Deploy command:**
```bash
cd ~/minipass_env
docker-compose up -d --force-recreate flask-controller-proxy
```

**Rollback if 404s appear** (wrong alias path):
```bash
# Remove the volume line from docker-compose.yml, then:
docker-compose up -d --force-recreate flask-controller-proxy
```

---

### Step 2 — Customer containers (lhgi, heq, kdc, mf): `vhost.d/` config

For customer containers, `nginx-proxy` does the routing. You can add per-domain config via the `vhost.d/` directory — no container rebuild needed.

The file `vhost.d/lhgi.minipass.me` already exists and sets `client_max_body_size`. Add cache headers for static files:

**File:** `vhost.d/lhgi.minipass.me` (and repeat for heq, kdc, testdelancementmf):

```nginx
client_max_body_size 50M;

location /static/ {
    expires 30d;
    add_header Cache-Control "public, max-age=2592000, immutable";
    access_log off;
}
```

**Note:** For customer containers the static files are already inside the container at `/app/static/` — nginx-proxy proxies everything including static files to gunicorn. These cache headers tell the **browser** to cache after the first download. They don't bypass Flask/gunicorn on the server side. Full static-file bypass for customer containers would require a more complex setup (not recommended yet).

**Deploy (no restart needed — nginx-proxy reloads vhost.d automatically):**
```bash
# After editing vhost.d files, force nginx-proxy to reload:
docker exec nginx-proxy nginx -s reload
```

---

## Verification Checklist

After deploying Phase 4 on the VPS:

1. **No 404s on static assets:** Open browser DevTools → Network tab, hard refresh activity page. All images/CSS/JS should load.

2. **Cache headers present:** Click any image request in DevTools. Response headers should include:
   ```
   Cache-Control: public, max-age=2592000, immutable
   ```

3. **Second load uses cache:** Refresh without hard-reload. Images should show `(disk cache)` or `304 Not Modified` in the Status column.

4. **Flask not serving static:** Check Flask logs — you should see zero requests for `/static/` paths after the first load.

---

## Notes on Your Architecture

- The `vhost.d/` directory is mounted into `nginx-proxy` at `/etc/nginx/vhost.d/`. Files in it are included as extra config for that virtual host. This is the `jwilder/nginx-proxy` way to customize per-domain settings without rebuilding the container.
- `flask-controller-proxy` exists solely because your main Flask app runs on the host (not in a container). It's a "fake container" that lets `nginx-proxy` discover it via `VIRTUAL_HOST` and route traffic to it.
- The `minipass_env_proxy` Docker network is the shared network that lets all containers talk to `nginx-proxy`. Customer containers declare `external: true` in their `docker-compose.yml` because this network is created by the main `docker-compose.yml`, not by each customer's compose file.
- The `nginx-letsencrypt` (acme-companion) container watches Docker events. Whenever a container starts with `LETSENCRYPT_HOST` set, it automatically requests/renews an SSL certificate and installs it into `nginx-proxy`. Zero manual cert management needed.

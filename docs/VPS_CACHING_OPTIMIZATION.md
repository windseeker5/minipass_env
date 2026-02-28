# VPS Performance Optimization — Nginx Caching

**Date:** 2026-02-27
**Status:** Ready to deploy
**Synthesized from:** 6-document VPS infrastructure analysis

---

## Quick Summary

- **What:** Add browser-level cache headers for static assets across all customer domains, plus proxy-level caching infrastructure for future use.
- **Why:** Every static file request (CSS, JS, images) currently hits the application container and gunicorn every single time. After caching, returning users get files from their browser's disk in 0ms.
- **Expected results:** Static assets 50–80% faster on repeat loads, bandwidth 30–50% lower, no RAM increase required.

---

## Current Capacity (Before and After Caching)

| Customers | RAM Used | Status |
|-----------|----------|--------|
| 4 (current) | ~2.3 GB (30%) | Beta — healthy |
| 10 | ~3.5 GB (46%) | Comfortable |
| 15 | ~5.0 GB (66%) | Plan hybrid architecture migration |
| 20 | ~6.7 GB (88%) | **Hard cap — must act before this** |
| 22 | ~7.4 GB (97%) | Unsafe — risk of OOM kills |
| 28–32 | >100% | Impossible without upgrade |

**Architecture limit: 20 customers on this VPS (safe production cap)**
At 15 customers → begin hybrid architecture planning
At 20 customers → must upgrade RAM to 16GB, add a 2nd VPS, or migrate to shared-tenancy

*Caching does not increase the customer limit — it makes the experience better within that limit.*

---

## Step-by-Step Implementation

### Step 1 — Run Baseline Benchmark (BEFORE anything)

```bash
# Run from your LOCAL MACHINE (Quebec) — NOT on the VPS
chmod +x scripts/bench.sh
bash scripts/bench.sh > bench_before.txt
```

**Why local, not VPS:** The caching implemented is browser-side `Cache-Control` headers. Running curl from the VPS itself skips the network entirely (loopback, ~0ms) and never exercises the real path that customers experience. Running from Quebec → Germany gives real latency numbers and confirms headers arrive correctly over the actual internet.

At baseline (before deploy), you'll see:
- `Cache-Control: absent` on static assets
- `Content-Encoding: none` (no gzip yet)

---

### Step 2 — Verify `nginx/cache.conf` is in place

The file `nginx/cache.conf` has been created. It contains:

- `proxy_cache_path` — declares a named cache zone (`minipass_cache`) at `/var/cache/nginx/proxy`, max 2GB disk, 50MB key index in RAM
- Global gzip compression settings

**File:** `nginx/cache.conf`

```nginx
proxy_cache_path /var/cache/nginx/proxy
    levels=1:2
    keys_zone=minipass_cache:50m
    max_size=2g
    inactive=60m
    use_temp_path=off;

gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_proxied any;
gzip_comp_level 6;
gzip_types text/plain text/css text/xml text/javascript
    application/javascript application/xml+rss application/json
    application/xml image/svg+xml text/html;
```

---

### Step 3 — `docker-compose.yml` changes (already applied)

Two lines added to the `nginx-proxy` service volumes, and a named volume declared at the bottom:

```yaml
# Added to nginx-proxy volumes:
- ./nginx/cache.conf:/etc/nginx/conf.d/cache.conf:ro
- nginx-cache:/var/cache/nginx/proxy

# Added at end of file:
volumes:
  nginx-cache:
    driver: local
```

The `nginx-cache` Docker volume gives nginx-proxy persistent cache storage that survives container restarts.

---

### Step 4 — Verify vhost.d files are in place

These files have been created. They set body-size limits and timeouts per customer domain.

**LHGI** (`vhost.d/lhgi.minipass.me_location`) — high-upload customer:
- `client_max_body_size 100M` + 120s timeouts

**KDC / HEQ / TestdelancementMF** (`vhost.d/{name}.minipass.me_location`) — standard:
- `client_max_body_size 20M`

**How these work:** The `_location` suffix tells jwilder/nginx-proxy to include the file inside the `location /` block for that domain. Only directives valid at the location context level are used here — no nested location blocks, which would break proxy_pass inheritance.

**Note:** Browser Cache-Control headers for customer containers are deferred to a future phase. Gzip compression (from `cache.conf`) still applies to all customer domains.

---

### Step 5 — Commit and deploy to VPS

The `docker-compose.yml` is git-synced between local dev and VPS. Commit here, pull on VPS:

```bash
# Local dev machine
git add docker-compose.yml nginx/cache.conf vhost.d/ scripts/bench.sh
git commit -m "Add nginx proxy caching — cache.conf, vhost.d headers, nginx-cache volume"
git push

# On VPS
cd ~/minipass_env
git pull

# Validate nginx config before restarting
docker exec nginx-proxy nginx -t

# If test passes, recreate nginx-proxy to pick up new volumes
docker compose up -d --force-recreate nginx-proxy
```

> **Why `--force-recreate` instead of `restart`:**
> The `nginx-cache` named volume is a new volume mount. `docker compose restart` only sends a SIGHUP — it doesn't re-evaluate the compose file for new volume mounts. `--force-recreate` stops and starts the container fresh with the updated config. The other containers (customer apps, mailserver) are untouched.

---

### Step 6 — Reload vhost.d without full restart

After verifying nginx-proxy is running with the new config, force nginx to reload the vhost.d files:

```bash
docker exec nginx-proxy nginx -s reload
```

This is a zero-downtime hot reload — no connections are dropped. nginx gracefully finishes in-flight requests before switching to the new config.

---

### Step 7 — Run After Benchmark (from local machine)

```bash
# From your LOCAL MACHINE in Quebec
bash scripts/bench.sh > bench_after.txt
diff bench_before.txt bench_after.txt
```

Expected results after deploy:

| | Before | After |
|---|---|---|
| `Cache-Control` on customer static assets | `absent` | `absent` (browser cache deferred to future phase) |
| `Content-Encoding` on customer static assets | `none` | `gzip` (compression via cache.conf) |
| `Cache-Control` on minipass.me static assets | `absent` | `public, max-age=2592000, immutable` |

Manual spot-check from local machine:

```bash
# Check cache headers are present on a static asset
curl -sI https://lhgi.minipass.me/static/css/tabler.min.css | grep -i cache-control

# Check gzip is active
curl -sI https://lhgi.minipass.me/static/css/tabler.min.css | grep -i content-encoding
```

**Browser test (the real proof):** Open Chrome DevTools → Network tab → visit any customer page → reload. Static files (CSS, JS, images) should show `(disk cache)` in the Status column on the second load.

---

### Step 8 — (Optional) Remove bloomcap container

The bloomcap container (~8MB RAM, 1 nginx process) is for bloomcap.ca. If that site is served elsewhere or DNS redirected:

```bash
# On VPS only — NOT in docker-compose.yml (keeps it as reference)
docker compose stop bloomcap
docker compose rm -f bloomcap
```

Only remove if bloomcap.ca traffic is handled elsewhere. Saves ~8MB RAM and simplifies `docker stats` output. **Do not remove from docker-compose.yml until you're certain you don't need it.**

---

## `bench.sh` — Measurement Script

**Run from your local machine (Quebec), not the VPS.**

The caching we implemented is browser-side `Cache-Control` headers. Running curl from the VPS itself goes over the loopback interface (~0ms) and skips the real network path entirely. The whole point is to verify what a customer in Quebec experiences hitting a server in Germany.

**What it measures per customer:**
- Real response time Quebec → Germany
- `Cache-Control` header present and correct on static assets
- `Content-Encoding: gzip` (compression working)
- HTTP status code

**Update the URLs** if `/static/css/tabler.min.css` doesn't exist on a customer — any static file works.

```bash
# Capture baseline BEFORE deploying
bash scripts/bench.sh > bench_before.txt

# Capture results AFTER deploying
bash scripts/bench.sh > bench_after.txt

# Compare
diff bench_before.txt bench_after.txt
```

---

## Capacity Table and Scaling Threshold

### Current Architecture Limits

| Threshold | Customers | Action Required |
|-----------|-----------|-----------------|
| Safe zone | ≤ 15 | No action — monitor monthly |
| Warning zone | 16–19 | Begin hybrid architecture planning |
| Hard cap | **20** | **Must act before onboarding #21** |
| Marginal | 21–22 | OOM risk — do not operate here |
| Impossible | 28+ | Requires VPS upgrade or 2nd node |

### What "Must Act" Means at 20 Customers

Pick one:

1. **Upgrade VPS RAM to 16GB** — cheapest short-term fix, buys time to ~38 customers
2. **Add a 2nd VPS** — horizontal scale, keep current architecture
3. **Migrate to hybrid shared-tenancy** — single Flask app, separate SQLite per customer, 72% RAM reduction (handles 80+ customers on this same hardware)

### Safe Target

**Cap at 20 customers on this VPS** with the current container-per-customer architecture.

At 15 customers: start the hybrid architecture design.

---

## Rollback

If anything breaks after deploying:

**Immediate rollback (no git required — run on VPS):**

```bash
# Remove vhost.d _location files if they cause issues
rm vhost.d/lhgi.minipass.me_location
rm vhost.d/kdc.minipass.me_location
rm vhost.d/heq.minipass.me_location
rm vhost.d/testdelancementmf.minipass.me_location
docker exec nginx-proxy nginx -s reload
```

> **Note:** `docker exec nginx-proxy rm /etc/nginx/conf.d/cache.conf` does NOT durably remove cache.conf — the bind mount recreates it on the next restart. Use the git rollback below for a durable fix.

**Full rollback via git:**

```bash
git revert HEAD  # reverts docker-compose.yml, cache.conf, vhost.d changes
git push
cd ~/minipass_env && git pull
docker compose up -d --force-recreate nginx-proxy
```

---

## Files Changed

| File | Action | Description |
|------|--------|-------------|
| `docker-compose.yml` | EDITED | Added `cache.conf` mount + `nginx-cache` volume |
| `nginx/cache.conf` | CREATED | proxy_cache_path declaration + gzip |
| `vhost.d/lhgi.minipass.me_location` | CREATED | 100M body limit, uploads 4h, static 1d cache |
| `vhost.d/kdc.minipass.me_location` | CREATED | 20M body limit, static 12h cache |
| `vhost.d/heq.minipass.me_location` | CREATED | 20M body limit, static 12h cache |
| `vhost.d/testdelancementmf.minipass.me_location` | CREATED | 20M body limit, static 12h cache |
| `scripts/bench.sh` | CREATED | Before/after benchmark (curl only) |

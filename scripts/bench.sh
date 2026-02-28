#!/usr/bin/env bash
# bench.sh — Minipass caching benchmark
#
# Run from your LOCAL MACHINE (Quebec), not the VPS.
# Tests real network latency Quebec → Germany and verifies cache headers.
#
# What this measures:
#   - Real response time from your location to the VPS
#   - Cache-Control header is present (browser knows to cache the file)
#   - Content-Encoding: gzip (compression is working)
#   - HTTP status code
#
# What "caching working" looks like:
#   BEFORE: Cache-Control header absent, no gzip, slower times
#   AFTER:  Cache-Control: public, max-age=... present, gzip present
#           On 2nd+ real browser visit: file served from browser disk (0ms)
#
# Usage:
#   bash scripts/bench.sh
#   bash scripts/bench.sh > bench_before.txt   # save baseline
#   bash scripts/bench.sh > bench_after.txt    # save after deploy
#   diff bench_before.txt bench_after.txt      # compare

set -uo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTFILE="bench_results_${TIMESTAMP}.txt"
DIVIDER="────────────────────────────────────────────────────────────────────"

# ── URLs to test ─────────────────────────────────────────────────────────────
# One static asset per customer (CSS file present on all Minipass deployments)
# One home page per customer (always dynamic — should never be cached)
CUSTOMERS=(lhgi kdc heq testdelancementmf)

# ── Helper: check one URL ─────────────────────────────────────────────────────
check_url() {
    local label="$1"
    local url="$2"

    # Single curl call: grab headers + timing, discard body
    local headers
    headers=$(curl -sI --max-time 15 \
        -H "Accept-Encoding: gzip, deflate" \
        -H "User-Agent: bench.sh/1.0" \
        "$url" 2>/dev/null || true)

    # Timing — separate call (curl -I doesn't download body, so timing reflects TTFB)
    local timing
    timing=$(curl -sk -o /dev/null -w "%{http_code} %{time_total} %{size_download}" \
        --max-time 15 \
        -H "Accept-Encoding: gzip, deflate" \
        -H "User-Agent: bench.sh/1.0" \
        "$url" 2>/dev/null || echo "000 0.000 0")

    local http_code time_s size_bytes
    http_code=$(echo "$timing" | awk '{print $1}')
    time_s=$(echo "$timing"    | awk '{print $2}')
    size_bytes=$(echo "$timing" | awk '{print $3}')

    # Extract relevant headers (lowercase for portability)
    local cache_control gzip_status
    cache_control=$(echo "$headers" | grep -i "^cache-control:" | sed 's/^[^:]*: *//' | tr -d '\r' || echo "absent")
    gzip_status=$(echo "$headers"   | grep -i "^content-encoding:" | sed 's/^[^:]*: *//' | tr -d '\r' || echo "none")

    [ -z "$cache_control" ] && cache_control="absent"
    [ -z "$gzip_status" ]   && gzip_status="none"

    printf "  %-52s  HTTP %s  %ss  %s bytes\n" "$label" "$http_code" "$time_s" "$size_bytes"
    printf "    Cache-Control:    %s\n" "$cache_control"
    printf "    Content-Encoding: %s\n" "$gzip_status"
    echo ""
}

# ── Output tee ───────────────────────────────────────────────────────────────
exec > >(tee -a "$OUTFILE") 2>&1

echo ""
echo "Minipass Benchmark — run from LOCAL MACHINE — $TIMESTAMP"
echo "(Quebec → Germany, real network latency)"
echo "$DIVIDER"
echo ""

# ── Section 1: Static assets ─────────────────────────────────────────────────
echo "STATIC ASSETS"
echo "  What to look for:"
echo "  BEFORE deploy: Cache-Control: absent,  Content-Encoding: none"
echo "  AFTER  deploy: Cache-Control: public max-age=...,  Content-Encoding: gzip"
echo "$DIVIDER"
echo ""

for c in "${CUSTOMERS[@]}"; do
    check_url "${c}.minipass.me  /static/css/tabler.min.css" \
              "https://${c}.minipass.me/static/css/tabler.min.css"
done

# minipass.me main site (served by flask-controller-proxy, already has caching)
check_url "minipass.me  /static/css/tabler.min.css" \
          "https://minipass.me/static/css/tabler.min.css"

# ── Section 2: Home pages (dynamic — Cache-Control should say no-cache) ──────
echo "HOME PAGES"
echo "  What to look for:"
echo "  Cache-Control: private, max-age=0, no-cache  (dynamic pages must NOT be cached)"
echo "$DIVIDER"
echo ""

for c in "${CUSTOMERS[@]}"; do
    check_url "${c}.minipass.me  /" "https://${c}.minipass.me/"
done
check_url "minipass.me  /" "https://minipass.me/"

# ── Section 3: Summary ───────────────────────────────────────────────────────
echo "$DIVIDER"
echo "Results saved to: $OUTFILE"
echo ""
echo "Quick pass/fail checklist:"
echo "  [ ] Static assets: Cache-Control contains 'public' and a max-age value"
echo "  [ ] Static assets: Content-Encoding is 'gzip'"
echo "  [ ] Home pages:    Cache-Control contains 'no-cache' or 'private'"
echo "  [ ] All URLs:      HTTP 200 (not 404 or 502)"
echo ""
echo "Note: browser cache benefit (0ms on repeat visit) is NOT visible in curl."
echo "To see it: open Chrome DevTools → Network tab → reload a customer page twice."
echo "Second load should show '(disk cache)' next to static files."
echo ""

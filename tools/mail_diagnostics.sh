#!/bin/bash
# Mail connectivity diagnostics — run on VPS host
# Tests hairpin NAT hypothesis: public hostname ports vs localhost ports

set -euo pipefail

MAIL_HOST="mail.minipass.me"
PORTS=(25 143 587 993)
TIMEOUT=3

echo "=== DNS Resolution ==="
dig +short "$MAIL_HOST" || echo "(dig not available)"
echo ""

echo "=== Port Tests via public hostname ($MAIL_HOST) ==="
for port in "${PORTS[@]}"; do
    if nc -zv -w"$TIMEOUT" "$MAIL_HOST" "$port" 2>&1 | grep -q "succeeded\|open\|Connected"; then
        echo "  port $port — PASS"
    else
        echo "  port $port — FAIL"
    fi
done
echo ""

echo "=== Port Tests via localhost (127.0.0.1) ==="
for port in "${PORTS[@]}"; do
    if nc -zv -w"$TIMEOUT" 127.0.0.1 "$port" 2>&1 | grep -q "succeeded\|open\|Connected"; then
        echo "  port $port — PASS"
    else
        echo "  port $port — FAIL"
    fi
done
echo ""

echo "=== Mailserver container ==="
docker ps --filter name=mailserver --format "{{.Names}}  status={{.Status}}" 2>/dev/null || echo "(docker not accessible)"
echo ""
echo "=== Published ports ==="
docker port mailserver 2>/dev/null || echo "(mailserver container not found)"
echo ""

echo "=== /etc/hosts mail entries ==="
grep -E "mail\.minipass\.me|smtp\.minipass\.me" /etc/hosts || echo "(no entries — hairpin NAT fix not applied)"
echo ""

echo "=== Expected outcome ==="
echo "If hairpin NAT is the issue:"
echo "  Public hostname ports → FAIL"
echo "  Localhost ports       → PASS"
echo ""
echo "Fix: sudo bash -c 'echo \"127.0.0.1 mail.minipass.me smtp.minipass.me\" >> /etc/hosts'"

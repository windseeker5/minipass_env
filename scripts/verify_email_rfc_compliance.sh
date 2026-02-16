#!/bin/bash
# RFC 5322 & Email Authentication Verification Script

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        Minipass Email RFC Compliance Verification              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if dig is installed
if ! command -v dig &> /dev/null; then
    echo "⚠️  WARNING: 'dig' command not found"
    echo "   This script requires dnsutils package"
    echo "   Install with: sudo pacman -S bind (Arch) or sudo apt install dnsutils (Ubuntu)"
    echo ""
    echo "   Alternative: Run this script on your production server where dig is installed"
    echo ""
    exit 1
fi

# SPF Check (RFC 7208)
echo "📋 [RFC 7208] SPF (Sender Policy Framework)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
SPF=$(dig minipass.me TXT +short 2>/dev/null | grep "v=spf1")
if [ -z "$SPF" ]; then
    echo "❌ FAIL: No SPF record found"
    echo "   Action: Add SPF record to DNS"
else
    echo "✅ PASS: $SPF"
fi
echo ""

# DKIM Check (RFC 6376)
echo "🔐 [RFC 6376] DKIM (DomainKeys Identified Mail)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
DKIM=$(dig mail._domainkey.minipass.me TXT +short 2>/dev/null)
if [ -z "$DKIM" ]; then
    echo "❌ FAIL: No DKIM record found"
    echo "   Action: Check OpenDKIM configuration"
else
    echo "✅ PASS: DKIM record exists"
    echo "   Record: ${DKIM:0:80}..."
fi
echo ""

# DMARC Check (RFC 7489)
echo "📊 [RFC 7489] DMARC (Authentication & Reporting)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
DMARC=$(dig _dmarc.minipass.me TXT +short 2>/dev/null)
if [ -z "$DMARC" ]; then
    echo "⚠️  WARN: No DMARC record found"
    echo "   Action: Create DMARC record with RUA email"
    echo "   Recommended: v=DMARC1; p=quarantine; rua=mailto:dmarc@minipass.me"
else
    echo "✅ PASS: $DMARC"
fi
echo ""

# MX Record Check
echo "📬 MX Records (Mail Servers)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
dig minipass.me MX +short 2>/dev/null || echo "⚠️  Could not query MX records"
echo ""

# PTR Record Check (Reverse DNS)
echo "🔄 PTR Record (Reverse DNS)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
IP="138.199.152.128"
PTR=$(dig -x $IP +short 2>/dev/null)
if [ -z "$PTR" ]; then
    echo "⚠️  WARN: No PTR record for $IP"
    echo "   Action: Contact VPS provider to set PTR record"
else
    echo "✅ PASS: $PTR"
fi
echo ""

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                      Verification Complete                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"

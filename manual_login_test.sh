#!/bin/bash

echo "🧪 Manual Login Test - Simulating Browser Behavior"
echo "=================================================="

# Step 1: Get login page and extract CSRF token
echo "1️⃣ Getting login page and CSRF token..."
CSRF_TOKEN=$(curl -c cookies.txt -b cookies.txt -s https://kiteguru.minipass.me/login | grep -o 'csrf_token.*value="[^"]*"' | sed 's/.*value="//; s/".*//')

if [ -n "$CSRF_TOKEN" ]; then
    echo "✅ CSRF Token: ${CSRF_TOKEN:0:30}..."
else
    echo "❌ Could not extract CSRF token"
    exit 1
fi

# Step 2: Submit login form
echo ""
echo "2️⃣ Submitting login form..."
RESPONSE=$(curl -c cookies.txt -b cookies.txt -s -i -X POST https://kiteguru.minipass.me/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -H "Referer: https://kiteguru.minipass.me/login" \
    -d "csrf_token=${CSRF_TOKEN}&email=kdresdell@gmail.com&password=ci_wp6drHtsa1G5T")

echo "Response headers:"
echo "$RESPONSE" | head -20

if echo "$RESPONSE" | grep -q "Location: /dashboard"; then
    echo ""
    echo "✅ LOGIN SUCCESSFUL - Redirected to dashboard"
elif echo "$RESPONSE" | grep -q "Location: /login"; then
    echo ""
    echo "❌ LOGIN FAILED - Redirected back to login"
elif echo "$RESPONSE" | grep -q "Invalid"; then
    echo ""
    echo "❌ LOGIN FAILED - Invalid credentials message"
else
    echo ""
    echo "⚠️ Unclear result - check response"
fi

# Step 3: Follow redirect if successful
if echo "$RESPONSE" | grep -q "Location: /dashboard"; then
    echo ""
    echo "3️⃣ Following redirect to dashboard..."
    DASHBOARD_RESPONSE=$(curl -c cookies.txt -b cookies.txt -s -i https://kiteguru.minipass.me/dashboard)
    
    if echo "$DASHBOARD_RESPONSE" | grep -q "HTTP.*200"; then
        echo "✅ Dashboard loaded successfully"
    else
        echo "❌ Dashboard failed to load"
    fi
fi

# Cleanup
rm -f cookies.txt

echo ""
echo "=================================================="
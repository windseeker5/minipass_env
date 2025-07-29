#!/bin/bash

echo "🛡️ Setting up Fail2Ban Manager..."

# Check if fail2ban is installed
if ! command -v fail2ban-client &> /dev/null; then
    echo "❌ fail2ban-client not found. Please install fail2ban first:"
    echo "   sudo apt update && sudo apt install fail2ban"
    exit 1
fi

# Check if fail2ban service is running
if ! systemctl is-active --quiet fail2ban; then
    echo "⚠️ fail2ban service is not running. Starting it..."
    sudo systemctl start fail2ban
    sudo systemctl enable fail2ban
fi

# Add user to adm group for log file access
echo "📋 Adding user to 'adm' group for log file access..."
sudo usermod -a -G adm $(whoami)

# Check if user has sudo privileges
if ! sudo -n true 2>/dev/null; then
    echo "⚠️ This script requires sudo privileges to manage fail2ban."
    echo "   Please make sure your user is in the sudo group."
fi

echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Log out and log back in (or run 'newgrp adm') to apply group changes"
echo "   2. Run the fail2ban manager: ./fail2ban_manager.py"
echo ""
echo "💡 If you see permission errors:"
echo "   - Make sure you can run 'sudo fail2ban-client status'"
echo "   - Check that you're in the 'adm' group: groups \$(whoami)"
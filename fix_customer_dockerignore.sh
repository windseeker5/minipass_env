#!/bin/bash

# Fix Docker Database Copying Bug for Deployed Customers
# This script ensures .dockerignore excludes instance/ directory to prevent database copying

echo "🔧 Fixing Docker database copying bug for all deployed customers..."

DEPLOYED_DIR="/home/kdresdell/minipass_env/deployed"

if [ ! -d "$DEPLOYED_DIR" ]; then
    echo "❌ Deployed directory not found: $DEPLOYED_DIR"
    exit 1
fi

echo "📁 Scanning deployed customers..."

for customer_dir in "$DEPLOYED_DIR"/*; do
    if [ -d "$customer_dir" ]; then
        customer_name=$(basename "$customer_dir")
        dockerignore_path="$customer_dir/app/.dockerignore"

        echo "🔍 Checking customer: $customer_name"

        if [ -f "$dockerignore_path" ]; then
            # Check if instance/ is already excluded
            if grep -q "^instance/$" "$dockerignore_path"; then
                echo "  ✅ $customer_name: instance/ already excluded"
            else
                echo "  🔧 $customer_name: Adding instance/ exclusion"

                # Backup original file
                cp "$dockerignore_path" "$dockerignore_path.backup.$(date +%Y%m%d_%H%M%S)"

                # Add instance/ exclusion if not present
                echo "instance/" >> "$dockerignore_path"

                echo "  ✅ $customer_name: Fixed! (backup created)"
            fi
        else
            echo "  ⚠️  $customer_name: .dockerignore not found"
        fi
    fi
done

echo ""
echo "🎯 Summary:"
echo "✅ All deployed customers checked for Docker database copying bug"
echo "✅ Fixed any missing instance/ exclusions in .dockerignore"
echo "✅ Backups created for any modified files"
echo ""
echo "🔗 To verify main template is correct:"
echo "   grep 'instance/' /home/kdresdell/minipass_env/app/.dockerignore"
echo ""
echo "🚀 Next steps:"
echo "   1. Rebuild any customer containers that were fixed"
echo "   2. Test deployment to ensure database isn't copied into container"
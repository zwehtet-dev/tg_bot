#!/bin/bash

# Upload Currency Exchange Bot to VPS
# Usage: ./upload_to_vps.sh user@vps-ip

set -e

if [ -z "$1" ]; then
    echo "❌ Error: VPS address required"
    echo "Usage: $0 user@vps-ip"
    echo "Example: $0 root@192.168.1.100"
    exit 1
fi

VPS_ADDRESS=$1
PROJECT_NAME="currency-exchange-bot"

echo "📦 Preparing project for upload..."

# Create tarball excluding unnecessary files
tar -czf exchange-bot.tar.gz \
    --exclude='venv' \
    --exclude='env' \
    --exclude='*.db' \
    --exclude='*.db-journal' \
    --exclude='receipts/*' \
    --exclude='admin_receipts/*' \
    --exclude='logs/*' \
    --exclude='data/*' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='.vscode' \
    --exclude='.idea' \
    --exclude='backup_*.tar.gz' \
    --exclude='exchange-bot.tar.gz' \
    .

echo "📤 Uploading to VPS..."
scp exchange-bot.tar.gz $VPS_ADDRESS:~/

echo "🔧 Setting up on VPS..."
ssh $VPS_ADDRESS << 'ENDSSH'
    # Create project directory
    mkdir -p currency-exchange-bot
    cd currency-exchange-bot
    
    # Extract files
    tar -xzf ../exchange-bot.tar.gz
    
    # Make scripts executable
    chmod +x deploy.sh docker-commands.sh
    
    echo ""
    echo "✅ Upload complete!"
    echo ""
    echo "📝 Next steps:"
    echo "1. Configure .env file:"
    echo "   nano .env"
    echo ""
    echo "2. Deploy the bot:"
    echo "   ./deploy.sh"
    echo ""
ENDSSH

# Clean up local tarball
rm exchange-bot.tar.gz

echo ""
echo "🎉 Project uploaded successfully!"
echo ""
echo "To connect to VPS and deploy:"
echo "  ssh $VPS_ADDRESS"
echo "  cd currency-exchange-bot"
echo "  nano .env          # Configure environment"
echo "  ./deploy.sh        # Deploy bot"

#!/bin/bash

# Admin Receipt Workflow Upgrade Deployment Script

echo "🚀 Deploying Admin Receipt Workflow Upgrade"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Backup database
echo "📦 Step 1: Backing up database..."
if [ -f "exchange_bot.db" ]; then
    BACKUP_FILE="exchange_bot.db.backup.$(date +%Y%m%d_%H%M%S)"
    cp exchange_bot.db "$BACKUP_FILE"
    echo -e "${GREEN}✅ Database backed up to: $BACKUP_FILE${NC}"
else
    echo -e "${YELLOW}⚠️  No existing database found${NC}"
fi
echo ""

# Step 2: Run migration
echo "🔄 Step 2: Running database migration..."
if python3 migrate_admin_receipt.py; then
    echo -e "${GREEN}✅ Migration completed successfully${NC}"
else
    echo -e "${RED}❌ Migration failed!${NC}"
    echo "Please check the error and try again."
    exit 1
fi
echo ""

# Step 3: Create admin_receipts directory
echo "📁 Step 3: Creating admin_receipts directory..."
if mkdir -p admin_receipts; then
    echo -e "${GREEN}✅ Directory created/verified${NC}"
else
    echo -e "${RED}❌ Failed to create directory${NC}"
    exit 1
fi
echo ""

# Step 4: Run tests
echo "🧪 Step 4: Running tests..."
if python3 test_admin_receipt_flow.py; then
    echo -e "${GREEN}✅ All tests passed${NC}"
else
    echo -e "${RED}❌ Tests failed!${NC}"
    echo "Please review the errors before deploying."
    exit 1
fi
echo ""

# Step 5: Check if bot is running
echo "🔍 Step 5: Checking bot status..."
if pgrep -f "python.*main.py" > /dev/null; then
    echo -e "${YELLOW}⚠️  Bot is currently running${NC}"
    echo ""
    read -p "Do you want to restart the bot now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🔄 Restarting bot..."
        if [ -f "restart_bot_clean.sh" ]; then
            ./restart_bot_clean.sh
            echo -e "${GREEN}✅ Bot restarted${NC}"
        else
            echo -e "${YELLOW}⚠️  restart_bot_clean.sh not found${NC}"
            echo "Please restart the bot manually:"
            echo "  pkill -f 'python.*main.py'"
            echo "  python3 main.py &"
        fi
    else
        echo -e "${YELLOW}⚠️  Please restart the bot manually when ready${NC}"
    fi
else
    echo -e "${GREEN}✅ Bot is not running${NC}"
    echo ""
    read -p "Do you want to start the bot now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🚀 Starting bot..."
        if [ -f "bot_manager.sh" ]; then
            ./bot_manager.sh start
            echo -e "${GREEN}✅ Bot started${NC}"
        else
            nohup python3 main.py > logs/bot.log 2>&1 &
            echo -e "${GREEN}✅ Bot started${NC}"
        fi
    fi
fi
echo ""

# Step 6: Summary
echo "=========================================="
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo "=========================================="
echo ""
echo "📝 What was deployed:"
echo "   • Database migration (admin_receipt_path column)"
echo "   • Admin receipt upload handler"
echo "   • Dynamic MMK bank selection"
echo "   • Simplified workflow (Cancel button only)"
echo ""
echo "📚 Documentation:"
echo "   • ADMIN_RECEIPT_WORKFLOW_UPGRADE.md - Technical details"
echo "   • ADMIN_NEW_WORKFLOW_GUIDE.md - Admin user guide"
echo ""
echo "🧪 Testing:"
echo "   1. Submit a test transaction as a user"
echo "   2. In admin group, reply to transaction with a photo"
echo "   3. Select MMK bank from buttons"
echo "   4. Verify transaction is confirmed"
echo ""
echo "📊 Monitoring:"
echo "   • Check logs: tail -f logs/bot.log"
echo "   • View transactions: /transactions"
echo "   • Check balances: /balance"
echo ""
echo "🆘 Rollback (if needed):"
echo "   • Restore database: cp $BACKUP_FILE exchange_bot.db"
echo "   • Restore code from git"
echo "   • Restart bot"
echo ""
echo -e "${GREEN}Happy exchanging! 💱${NC}"

#!/bin/bash

echo "🔄 Restarting Bot with Updates..."
echo ""

# Stop all running instances
echo "1️⃣ Stopping all bot instances..."
pkill -f "python.*main.py"
sleep 2

# Verify all stopped
if pgrep -f "python.*main.py" > /dev/null; then
    echo "⚠️  Some processes still running, force killing..."
    pkill -9 -f "python.*main.py"
    sleep 1
fi

if pgrep -f "python.*main.py" > /dev/null; then
    echo "❌ Failed to stop bot. Please check manually:"
    echo "   ps aux | grep python"
    exit 1
fi

echo "✅ All bot instances stopped"
echo ""

# Start the bot
echo "2️⃣ Starting bot with updates..."
./bot_manager.sh start
sleep 3

# Verify bot is running
if pgrep -f "python.*main.py" > /dev/null; then
    echo "✅ Bot started successfully"
    
    # Show running process
    echo ""
    echo "📊 Running process:"
    ps aux | grep "python.*main.py" | grep -v grep
else
    echo "❌ Bot failed to start. Check logs:"
    echo "   tail -f logs/bot.log"
    exit 1
fi

echo ""
echo "=" * 70
echo "✅ DEPLOYMENT COMPLETE!"
echo "=" * 70
echo ""
echo "📋 Updates Applied:"
echo "   ✅ Balance tracking for receiver banks"
echo "   ✅ SCB recognized as SiamCommercialBank"
echo "   ✅ Enhanced bank alias support (SCB, KTB, KBank, BBL)"
echo "   ✅ Improved balance update messages"
echo ""
echo "🧪 Test the Updates:"
echo "   1. Send a receipt with 'SCB' as the bank"
echo "   2. Verify receiver account is validated"
echo "   3. Check balance update shows 'SiamCommercialBank'"
echo "   4. Confirm balances are adjusted correctly"
echo ""
echo "📊 Monitor Bot:"
echo "   tail -f logs/bot.log"
echo ""
echo "📚 Documentation:"
echo "   - FINAL_UPDATE_SUMMARY.md (comprehensive overview)"
echo "   - BALANCE_FIX_QUICK_GUIDE.md (quick reference)"
echo "   - SCB_ALIAS_UPDATE.md (SCB alias details)"

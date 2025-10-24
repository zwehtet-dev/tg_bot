#!/bin/bash

echo "🔄 Deploying Balance Fix..."
echo ""

# Stop the bot
echo "1️⃣ Stopping bot..."
./bot_manager.sh stop
sleep 2

# Verify bot is stopped
if pgrep -f "python.*main.py" > /dev/null; then
    echo "❌ Bot is still running. Please stop it manually."
    exit 1
fi

echo "✅ Bot stopped"
echo ""

# Start the bot
echo "2️⃣ Starting bot with updated code..."
./bot_manager.sh start
sleep 3

# Verify bot is running
if pgrep -f "python.*main.py" > /dev/null; then
    echo "✅ Bot started successfully"
else
    echo "❌ Bot failed to start. Check logs:"
    echo "   tail -f logs/bot.log"
    exit 1
fi

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 What was fixed:"
echo "   - Admin THB bank is now properly tracked in transactions"
echo "   - Balance update messages show correct bank names"
echo "   - Receiver bank validation works for all admin accounts"
echo "   - SCB is now recognized as SiamCommercialBank"
echo "   - Enhanced bank alias support (SCB, KTB, KBank, BBL)"
echo "   - Fuzzy matching handles OCR errors (e.g., MWE vs NWE)"
echo ""
echo "🧪 Test the fix:"
echo "   1. Send a test receipt to any admin bank (e.g., SiamCommercialBank)"
echo "   2. Check that balance update message shows the correct bank name"
echo "   3. Verify balances are adjusted correctly"
echo "   4. Test with OCR errors (e.g., 'MIN MYAT MWE' should match 'MIN MYAT NWE')"
echo ""
echo "📊 Monitor logs:"
echo "   tail -f logs/bot.log"

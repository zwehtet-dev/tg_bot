#!/bin/bash

echo "=================================================="
echo "INSUFFICIENT FUNDS PROTECTION - DEPLOYMENT"
echo "=================================================="
echo ""

# Check if bot is running
if pgrep -f "python.*main.py" > /dev/null; then
    echo "✅ Bot is currently running"
    BOT_RUNNING=true
else
    echo "⚠️  Bot is not running"
    BOT_RUNNING=false
fi

echo ""
echo "📋 Deployment Steps:"
echo "1. Test the insufficient funds logic"
echo "2. Stop the bot (if running)"
echo "3. Restart the bot with new code"
echo ""

read -p "Continue with deployment? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

echo ""
echo "=================================================="
echo "STEP 1: Testing Insufficient Funds Logic"
echo "=================================================="
python3 test_insufficient_funds.py

echo ""
read -p "Tests look good? Continue? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

if [ "$BOT_RUNNING" = true ]; then
    echo ""
    echo "=================================================="
    echo "STEP 2: Stopping Bot"
    echo "=================================================="
    pkill -f "python.*main.py"
    sleep 2
    
    if pgrep -f "python.*main.py" > /dev/null; then
        echo "⚠️  Bot still running, force killing..."
        pkill -9 -f "python.*main.py"
        sleep 1
    fi
    
    echo "✅ Bot stopped"
fi

echo ""
echo "=================================================="
echo "STEP 3: Starting Bot"
echo "=================================================="

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
    
    # Verify dependencies
    python3 -c "import telegram" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "⚠️  Installing dependencies..."
        pip install -r requirements.txt
    fi
else
    echo "⚠️  Virtual environment not found, using system Python"
fi

# Start bot in background
nohup python3 main.py > logs/bot.log 2>&1 &
BOT_PID=$!

echo "✅ Bot started (PID: $BOT_PID)"
sleep 3

# Check if bot is running
if pgrep -f "python.*main.py" > /dev/null; then
    echo "✅ Bot is running successfully"
else
    echo "❌ Bot failed to start"
    echo "Check logs/bot.log for details"
    exit 1
fi

echo ""
echo "=================================================="
echo "DEPLOYMENT COMPLETE"
echo "=================================================="
echo ""
echo "✅ Insufficient Funds Protection is now active!"
echo ""
echo "📊 Features:"
echo "  • Automatic balance checking before MMK transfers"
echo "  • Admin notification when funds insufficient"
echo "  • Transaction blocked until funds available"
echo "  • Clear shortage amount displayed"
echo ""
echo "📖 Documentation: INSUFFICIENT_FUNDS_FEATURE.md"
echo ""
echo "🔍 Monitor bot:"
echo "  tail -f logs/bot.log"
echo ""
echo "💰 Check balances:"
echo "  /balance"
echo ""
echo "=================================================="

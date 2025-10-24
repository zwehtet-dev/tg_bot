#!/bin/bash

echo "=================================================="
echo "STARTING EXCHANGE BOT"
echo "=================================================="
echo ""

# Check if bot is already running
if pgrep -f "python.*main.py" > /dev/null; then
    echo "⚠️  Bot is already running!"
    echo ""
    echo "To stop it first, run:"
    echo "  pkill -f 'python.*main.py'"
    echo ""
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Run: ./fix_dependencies.sh"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
python3 -c "import telegram" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Dependencies not installed!"
    echo "Run: ./fix_dependencies.sh"
    exit 1
fi

echo "✅ Virtual environment activated"
echo ""

# Create logs directory if it doesn't exist
mkdir -p logs

# Start bot in background
echo "Starting bot..."
nohup python3 main.py > logs/bot.log 2>&1 &
BOT_PID=$!

sleep 2

# Check if bot is running
if pgrep -f "python.*main.py" > /dev/null; then
    echo "✅ Bot started successfully (PID: $BOT_PID)"
    echo ""
    echo "📊 Monitor logs:"
    echo "   tail -f logs/bot.log"
    echo ""
    echo "🛑 Stop bot:"
    echo "   pkill -f 'python.*main.py'"
    echo ""
else
    echo "❌ Bot failed to start"
    echo ""
    echo "Check logs:"
    echo "   tail -20 logs/bot.log"
    echo ""
    exit 1
fi

echo "=================================================="
echo "BOT IS RUNNING"
echo "=================================================="

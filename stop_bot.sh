#!/bin/bash

echo "=================================================="
echo "STOPPING EXCHANGE BOT"
echo "=================================================="
echo ""

# Check if bot is running
if ! pgrep -f "python.*main.py" > /dev/null; then
    echo "⚠️  Bot is not running"
    exit 0
fi

# Get PID
BOT_PID=$(pgrep -f "python.*main.py")
echo "Found bot process (PID: $BOT_PID)"

# Stop bot gracefully
echo "Stopping bot..."
pkill -f "python.*main.py"

sleep 2

# Check if stopped
if pgrep -f "python.*main.py" > /dev/null; then
    echo "⚠️  Bot still running, force killing..."
    pkill -9 -f "python.*main.py"
    sleep 1
fi

# Verify stopped
if pgrep -f "python.*main.py" > /dev/null; then
    echo "❌ Failed to stop bot"
    exit 1
else
    echo "✅ Bot stopped successfully"
fi

echo ""
echo "=================================================="
echo "BOT STOPPED"
echo "=================================================="

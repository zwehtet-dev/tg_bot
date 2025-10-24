#!/bin/bash

# Bot Manager Script

case "$1" in
    start)
        echo "🚀 Starting bot..."
        # Check if already running
        if pgrep -f "python.*main.py" > /dev/null; then
            echo "⚠️  Bot is already running!"
            echo "Use: ./bot_manager.sh stop (to stop it first)"
            exit 1
        fi
        python main.py
        ;;
    
    stop)
        echo "🛑 Stopping bot..."
        pkill -f "python.*main.py"
        sleep 2
        if pgrep -f "python.*main.py" > /dev/null; then
            echo "⚠️  Bot still running, force killing..."
            pkill -9 -f "python.*main.py"
        fi
        echo "✅ Bot stopped"
        ;;
    
    restart)
        echo "🔄 Restarting bot..."
        $0 stop
        sleep 2
        $0 start
        ;;
    
    status)
        if pgrep -f "python.*main.py" > /dev/null; then
            echo "✅ Bot is running"
            echo ""
            echo "Process details:"
            ps aux | grep "python.*main.py" | grep -v grep
        else
            echo "❌ Bot is not running"
        fi
        ;;
    
    logs)
        if [ -f "bot.log" ]; then
            tail -f bot.log
        else
            echo "No log file found. Start bot with: python main.py 2>&1 | tee bot.log"
        fi
        ;;
    
    *)
        echo "Bot Manager - Usage:"
        echo ""
        echo "  ./bot_manager.sh start    - Start the bot"
        echo "  ./bot_manager.sh stop     - Stop the bot"
        echo "  ./bot_manager.sh restart  - Restart the bot"
        echo "  ./bot_manager.sh status   - Check bot status"
        echo "  ./bot_manager.sh logs     - View bot logs"
        echo ""
        exit 1
        ;;
esac

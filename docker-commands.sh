#!/bin/bash

# Currency Exchange Bot - Docker Management Commands

case "$1" in
    start)
        echo "🚀 Starting bot..."
        docker-compose up -d
        ;;
    stop)
        echo "🛑 Stopping bot..."
        docker-compose down
        ;;
    restart)
        echo "🔄 Restarting bot..."
        docker-compose restart
        ;;
    logs)
        echo "📝 Showing logs (Ctrl+C to exit)..."
        docker-compose logs -f
        ;;
    status)
        echo "📊 Container status:"
        docker-compose ps
        ;;
    rebuild)
        echo "🔨 Rebuilding and restarting..."
        docker-compose down
        docker-compose build
        docker-compose up -d
        ;;
    shell)
        echo "🐚 Opening shell in container..."
        docker-compose exec exchange-bot /bin/bash
        ;;
    clean)
        echo "🧹 Cleaning up (keeps data)..."
        docker-compose down
        docker system prune -f
        ;;
    backup)
        echo "💾 Creating backup..."
        timestamp=$(date +%Y%m%d_%H%M%S)
        tar -czf "backup_${timestamp}.tar.gz" data/ receipts/ admin_receipts/ .env
        echo "✅ Backup created: backup_${timestamp}.tar.gz"
        ;;
    *)
        echo "Currency Exchange Bot - Docker Commands"
        echo ""
        echo "Usage: $0 {command}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the bot"
        echo "  stop     - Stop the bot"
        echo "  restart  - Restart the bot"
        echo "  logs     - View bot logs (live)"
        echo "  status   - Check container status"
        echo "  rebuild  - Rebuild and restart"
        echo "  shell    - Open shell in container"
        echo "  clean    - Clean up Docker resources"
        echo "  backup   - Backup data and config"
        echo ""
        exit 1
        ;;
esac

#!/bin/bash

echo "================================================"
echo "Exchange Bot - New Features Setup"
echo "================================================"
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not activated!"
    echo "Please run: source venv/bin/activate"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Step 1: Running database migration..."
python migrate_db.py

if [ $? -ne 0 ]; then
    echo "❌ Migration failed!"
    exit 1
fi

echo ""
echo "================================================"
echo "✅ Setup Complete!"
echo "================================================"
echo ""
echo "Next Steps:"
echo ""
echo "1. Start your bot:"
echo "   python main.py"
echo ""
echo "2. In your Telegram admin group, configure settings:"
echo "   /settings admin_topic_id YOUR_TOPIC_ID"
echo "   /settings balance_topic_id YOUR_BALANCE_TOPIC_ID"
echo ""
echo "3. Add your real bank accounts:"
echo "   /addbank THB KBank 1234567890 YOUR COMPANY NAME"
echo "   /addbank MMK KBZ 9876543210 YOUR COMPANY NAME"
echo ""
echo "4. Verify setup:"
echo "   /listbanks"
echo "   /settings"
echo ""
echo "📖 Read ADMIN_GUIDE.md for detailed instructions"
echo ""

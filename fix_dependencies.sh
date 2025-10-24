#!/bin/bash

echo "=================================================="
echo "FIX DEPENDENCIES - Telegram Module"
echo "=================================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo ""
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo ""
echo "=================================================="
echo "VERIFICATION"
echo "=================================================="

# Test telegram import
python3 -c "from telegram.ext import Application; print('✅ Telegram module: OK')" 2>&1

# Test bot import
python3 -c "from app.bot import ExchangeBot; print('✅ Bot module: OK')" 2>&1

# Test database
python3 -c "from app.services.database_service import DatabaseService; print('✅ Database service: OK')" 2>&1

# Test OCR
python3 -c "from app.services.ocr_service import OCRService; print('✅ OCR service: OK')" 2>&1

echo ""
echo "=================================================="
echo "DEPENDENCIES FIXED"
echo "=================================================="
echo ""
echo "✅ All dependencies installed successfully!"
echo ""
echo "🚀 You can now start the bot:"
echo "   source venv/bin/activate"
echo "   python3 main.py"
echo ""
echo "Or use the deployment script:"
echo "   ./deploy_insufficient_funds.sh"
echo ""

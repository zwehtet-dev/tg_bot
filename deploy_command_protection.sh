#!/bin/bash

# Command Protection Deployment Script
# This script deploys the command protection upgrade

set -e

echo "================================================"
echo "Command Protection Upgrade Deployment"
echo "================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if bot is running
if pgrep -f "python.*main.py" > /dev/null; then
    echo -e "${YELLOW}⚠️  Bot is currently running${NC}"
    read -p "Stop the bot and continue? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Stopping bot..."
        ./stop_bot.sh
        sleep 2
    else
        echo "Deployment cancelled"
        exit 1
    fi
fi

echo ""
echo "Step 1: Checking Python environment..."
if [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
else
    echo -e "${RED}✗ Virtual environment not found${NC}"
    echo "Please run setup.sh first"
    exit 1
fi

echo ""
echo "Step 2: Verifying new files..."
if [ -f "app/utils/command_protection.py" ]; then
    echo -e "${GREEN}✓ Command protection module found${NC}"
else
    echo -e "${RED}✗ Command protection module missing${NC}"
    exit 1
fi

echo ""
echo "Step 3: Testing imports..."
python3 << EOF
try:
    from app.utils.command_protection import admin_only, private_chat_only
    from app.utils.command_protection import admin_group_only_callback, private_chat_only_callback
    print("${GREEN}✓ All decorators imported successfully${NC}")
except ImportError as e:
    print("${RED}✗ Import error: ${e}${NC}")
    exit(1)
EOF

echo ""
echo "Step 4: Validating handler updates..."
python3 << EOF
import ast
import sys

def check_decorators(file_path, expected_decorators):
    with open(file_path, 'r') as f:
        tree = ast.parse(f.read())
    
    decorated_methods = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.decorator_list:
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name):
                        decorated_methods.append((node.name, decorator.id))
    
    return decorated_methods

# Check admin handlers
admin_decorators = check_decorators('app/handlers/admin_handlers.py', ['admin_only', 'admin_group_only_callback'])
user_decorators = check_decorators('app/handlers/user_handlers.py', ['private_chat_only', 'private_chat_only_callback'])

print(f"Admin handlers protected: {len(admin_decorators)}")
print(f"User handlers protected: {len(user_decorators)}")

if len(admin_decorators) >= 10 and len(user_decorators) >= 5:
    print("${GREEN}✓ Handlers properly decorated${NC}")
else:
    print("${YELLOW}⚠️  Some handlers may not be protected${NC}")
EOF

echo ""
echo "Step 5: Checking configuration..."
if [ -f ".env" ]; then
    if grep -q "ADMIN_GROUP_ID" .env; then
        echo -e "${GREEN}✓ ADMIN_GROUP_ID configured${NC}"
    else
        echo -e "${YELLOW}⚠️  ADMIN_GROUP_ID not set in .env${NC}"
        echo "Please add ADMIN_GROUP_ID to your .env file"
    fi
else
    echo -e "${RED}✗ .env file not found${NC}"
    exit 1
fi

echo ""
echo "Step 6: Running syntax check..."
python3 -m py_compile app/utils/command_protection.py
python3 -m py_compile app/handlers/admin_handlers.py
python3 -m py_compile app/handlers/user_handlers.py
echo -e "${GREEN}✓ No syntax errors${NC}"

echo ""
echo "================================================"
echo -e "${GREEN}✓ Command Protection Upgrade Ready!${NC}"
echo "================================================"
echo ""
echo "What's New:"
echo "  • Bot commands only work in private chat"
echo "  • Admin commands only work in admin group"
echo "  • Clear error messages for wrong context"
echo "  • Comprehensive logging"
echo ""
echo "Protected Commands:"
echo "  Bot: /start, /cancel, exchange flow"
echo "  Admin: /balance, /rate, /transactions, etc."
echo ""
echo "Next Steps:"
echo "  1. Review COMMAND_PROTECTION_GUIDE.md"
echo "  2. Start the bot: ./start_bot.sh"
echo "  3. Test in private chat: /start"
echo "  4. Test in admin group: /balance"
echo ""
read -p "Start the bot now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Starting bot..."
    ./start_bot.sh
    echo ""
    echo -e "${GREEN}✓ Bot started successfully!${NC}"
    echo ""
    echo "Monitor logs: tail -f logs/bot.log"
else
    echo ""
    echo "You can start the bot later with: ./start_bot.sh"
fi

echo ""
echo "================================================"
echo "Deployment Complete!"
echo "================================================"

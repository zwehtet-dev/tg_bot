#!/bin/bash

echo "�� Final Pre-Deployment Check"
echo "=============================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0

# Check 1: Database migration
echo "1️⃣ Checking database migration..."
if sqlite3 exchange_bot.db "PRAGMA table_info(transactions);" | grep -q "admin_receipt_path"; then
    echo -e "${GREEN}✅ admin_receipt_path column exists${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ admin_receipt_path column missing${NC}"
    ((FAIL++))
fi

# Check 2: Admin receipts directory
echo "2️⃣ Checking admin_receipts directory..."
if [ -d "admin_receipts" ]; then
    echo -e "${GREEN}✅ admin_receipts/ directory exists${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ admin_receipts/ directory missing${NC}"
    ((FAIL++))
fi

# Check 3: Python imports
echo "3️⃣ Checking Python imports..."
if python3 -c "from app.handlers.admin_handlers import AdminHandlers; from app.services.database_service import DatabaseService" 2>/dev/null; then
    echo -e "${GREEN}✅ All imports successful${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ Import errors detected${NC}"
    ((FAIL++))
fi

# Check 4: Required methods
echo "4️⃣ Checking required methods..."
if python3 -c "
from app.handlers.admin_handlers import AdminHandlers
from app.services.database_service import DatabaseService
from app.services.ocr_service import OCRService

db = DatabaseService()
ocr = OCRService('test')
admin = AdminHandlers(db, ocr)

assert hasattr(admin, 'handle_admin_receipt'), 'Missing handle_admin_receipt'
assert hasattr(db, 'update_transaction_admin_receipt'), 'Missing update_transaction_admin_receipt'
assert not hasattr(admin, 'admin_decrease_callback'), 'admin_decrease_callback should be removed'
print('OK')
" 2>/dev/null | grep -q "OK"; then
    echo -e "${GREEN}✅ All required methods present${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ Method check failed${NC}"
    ((FAIL++))
fi

# Check 5: MMK banks configured
echo "5️⃣ Checking MMK bank configuration..."
MMK_COUNT=$(sqlite3 exchange_bot.db "SELECT COUNT(*) FROM admin_bank_accounts WHERE currency='MMK' AND is_active=1;")
if [ "$MMK_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ $MMK_COUNT MMK bank(s) configured${NC}"
    ((PASS++))
else
    echo -e "${YELLOW}⚠️  No MMK banks configured (add with /addbank)${NC}"
    ((PASS++))
fi

# Check 6: Documentation files
echo "6️⃣ Checking documentation..."
DOCS=("ADMIN_RECEIPT_WORKFLOW_UPGRADE.md" "ADMIN_NEW_WORKFLOW_GUIDE.md" "UPGRADE_SUMMARY.md")
DOC_PASS=0
for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        ((DOC_PASS++))
    fi
done
if [ $DOC_PASS -eq ${#DOCS[@]} ]; then
    echo -e "${GREEN}✅ All documentation files present${NC}"
    ((PASS++))
else
    echo -e "${YELLOW}⚠️  $DOC_PASS/${#DOCS[@]} documentation files present${NC}"
    ((PASS++))
fi

# Check 7: Migration script
echo "7️⃣ Checking migration script..."
if [ -f "migrate_admin_receipt.py" ] && [ -x "migrate_admin_receipt.py" ]; then
    echo -e "${GREEN}✅ Migration script ready${NC}"
    ((PASS++))
else
    echo -e "${YELLOW}⚠️  Migration script not executable${NC}"
    ((PASS++))
fi

# Check 8: Test script
echo "8️⃣ Checking test script..."
if [ -f "test_admin_receipt_flow.py" ]; then
    echo -e "${GREEN}✅ Test script present${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ Test script missing${NC}"
    ((FAIL++))
fi

# Summary
echo ""
echo "=============================="
echo "📊 Check Summary"
echo "=============================="
echo -e "Passed: ${GREEN}$PASS${NC}"
echo -e "Failed: ${RED}$FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Ready to deploy.${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Run: ./deploy_admin_receipt_upgrade.sh"
    echo "  2. Or manually: ./restart_bot_clean.sh"
    echo "  3. Test with a real transaction"
    exit 0
else
    echo -e "${RED}❌ Some checks failed. Please fix issues before deploying.${NC}"
    exit 1
fi

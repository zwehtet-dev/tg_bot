#!/usr/bin/env python3
"""
Test script for admin receipt workflow
"""
import sys
from app.services.database_service import DatabaseService

def test_admin_receipt_flow():
    """Test the admin receipt workflow components"""
    print("🧪 Testing Admin Receipt Workflow Components\n")
    
    # Initialize database
    db = DatabaseService('exchange_bot.db')
    
    # Test 1: Check if admin_receipt_path column exists
    print("1️⃣ Checking database schema...")
    try:
        import sqlite3
        conn = sqlite3.connect('exchange_bot.db')
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(transactions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'admin_receipt_path' in columns:
            print("   ✅ admin_receipt_path column exists")
        else:
            print("   ❌ admin_receipt_path column missing")
            print("   Run: python3 migrate_admin_receipt.py")
            return False
        conn.close()
    except Exception as e:
        print(f"   ❌ Database check failed: {e}")
        return False
    
    # Test 2: Check if update_transaction_admin_receipt method exists
    print("\n2️⃣ Checking database service methods...")
    if hasattr(db, 'update_transaction_admin_receipt'):
        print("   ✅ update_transaction_admin_receipt() method exists")
    else:
        print("   ❌ update_transaction_admin_receipt() method missing")
        return False
    
    # Test 3: Check MMK banks configuration
    print("\n3️⃣ Checking MMK bank accounts...")
    mmk_accounts = db.get_admin_bank_accounts('MMK')
    if mmk_accounts:
        print(f"   ✅ Found {len(mmk_accounts)} MMK bank account(s):")
        for acc_id, currency, bank_name, account_number, account_name, is_active in mmk_accounts:
            status = "✅" if is_active else "❌"
            print(f"      {status} {bank_name} - {account_number}")
    else:
        print("   ⚠️  No MMK bank accounts configured")
        print("   Add banks using: /addbank MMK BankName AccountNumber AccountName")
    
    # Test 4: Check admin_receipts directory
    print("\n4️⃣ Checking directories...")
    import os
    if os.path.exists('admin_receipts'):
        print("   ✅ admin_receipts/ directory exists")
    else:
        print("   ⚠️  admin_receipts/ directory missing")
        print("   Creating directory...")
        os.makedirs('admin_receipts', exist_ok=True)
        print("   ✅ Directory created")
    
    # Test 5: Test admin receipt update
    print("\n5️⃣ Testing admin receipt update...")
    try:
        # Create a test transaction
        test_txn_id = db.create_transaction(
            user_id=123456789,
            username="test_user",
            thb_amount=1000.0,
            mmk_amount=121500.0,
            rate=121.5,
            user_bank_name="KBZ",
            user_account_number="1234567890",
            user_account_name="TEST USER",
            from_bank="KBank",
            receipt_path="receipts/test.jpg",
            admin_thb_bank="KrungthaiBank"
        )
        
        if test_txn_id:
            print(f"   ✅ Test transaction created: #{test_txn_id}")
            
            # Update with admin receipt
            db.update_transaction_admin_receipt(test_txn_id, "admin_receipts/test_admin.jpg")
            print("   ✅ Admin receipt path updated")
            
            # Verify update
            txn = db.get_transaction(test_txn_id)
            if txn and len(txn) > 18 and txn[18] == "admin_receipts/test_admin.jpg":  # admin_receipt_path column at index 18
                print("   ✅ Admin receipt path verified in database")
            else:
                print(f"   ❌ Admin receipt path not saved correctly (got: {txn[18] if txn and len(txn) > 18 else 'N/A'})")
                return False
            
            # Clean up test transaction
            import sqlite3
            conn = sqlite3.connect('exchange_bot.db')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE id = ?", (test_txn_id,))
            conn.commit()
            conn.close()
            print("   ✅ Test transaction cleaned up")
        else:
            print("   ❌ Failed to create test transaction")
            return False
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False
    
    print("\n" + "="*50)
    print("✅ All tests passed! Admin receipt workflow is ready.")
    print("="*50)
    print("\n📝 Next steps:")
    print("   1. Restart bot: ./restart_bot_clean.sh")
    print("   2. Test with a real transaction")
    print("   3. Reply to transaction message with a photo")
    print("   4. Select MMK bank from buttons")
    
    return True

if __name__ == "__main__":
    success = test_admin_receipt_flow()
    sys.exit(0 if success else 1)

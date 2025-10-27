#!/usr/bin/env python3
"""
Migration script to copy balances from balances table to admin_bank_accounts table
"""
import sqlite3
import sys

def migrate_balances():
    """Copy balances from balances table to admin_bank_accounts"""
    
    db_path = 'exchange_bot.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all balances from old table
        cursor.execute("SELECT currency, bank, balance FROM balances")
        old_balances = cursor.fetchall()
        
        print("Balances from old 'balances' table:")
        for currency, bank, balance in old_balances:
            print(f"  {currency} - {bank}: {balance:,.2f}")
        
        print("\nMigrating balances to admin_bank_accounts...")
        
        updated_count = 0
        not_found = []
        
        for currency, bank, balance in old_balances:
            # Try to find matching account in admin_bank_accounts
            cursor.execute("""
                SELECT id FROM admin_bank_accounts 
                WHERE currency = ? AND bank_name = ?
            """, (currency, bank))
            
            result = cursor.fetchone()
            
            if result:
                account_id = result[0]
                cursor.execute("""
                    UPDATE admin_bank_accounts 
                    SET balance = ? 
                    WHERE id = ?
                """, (balance, account_id))
                print(f"  ✓ Updated {currency} - {bank}: {balance:,.2f}")
                updated_count += 1
            else:
                not_found.append((currency, bank, balance))
                print(f"  ⚠️  No matching account for {currency} - {bank}")
        
        conn.commit()
        
        print(f"\n✅ Updated {updated_count} account(s)")
        
        if not_found:
            print(f"\n⚠️  {len(not_found)} balance(s) not migrated (no matching account):")
            for currency, bank, balance in not_found:
                print(f"  - {currency} - {bank}: {balance:,.2f}")
        
        # Show final balances in admin_bank_accounts
        cursor.execute("""
            SELECT currency, bank_name, display_name, balance 
            FROM admin_bank_accounts 
            WHERE is_active = 1
            ORDER BY currency, bank_name
        """)
        accounts = cursor.fetchall()
        
        print("\nFinal balances in admin_bank_accounts:")
        for currency, bank_name, display_name, balance in accounts:
            display = display_name if display_name else bank_name
            print(f"  {currency} - {display}: {balance:,.2f}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    print("Database Migration: Copy balances to admin_bank_accounts")
    print("=" * 60)
    print()
    
    migrate_balances()
    
    print("\n✅ Migration complete!")
    print("\nNote: The old 'balances' table is still there.")
    print("You can drop it later if everything works correctly.")

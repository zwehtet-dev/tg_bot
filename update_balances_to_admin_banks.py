#!/usr/bin/env python3
"""
Update existing balances to match admin bank accounts
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = "exchange_bot.db"


def update_balances():
    """Update balances to match admin bank accounts"""
    print("Updating balances to match admin bank accounts...")
    
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found. Run the bot first to create it.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Get current balances
        cursor.execute("SELECT currency, bank, balance FROM balances")
        current_balances = cursor.fetchall()
        
        print("\n📊 Current Balances:")
        for currency, bank, balance in current_balances:
            print(f"  {currency} - {bank}: {balance:,.2f}")
        
        # Define new balance structure matching admin banks
        new_balances = [
            # THB Admin Banks
            ('THB', 'KrungthaiBank', 150000),
            ('THB', 'PromptPay', 150000),
            ('THB', 'SiamCommercialBank', 150000),
            # MMK Admin Banks
            ('MMK', 'KBZ', 1500000),
            ('MMK', 'AYA', 1500000),
            ('MMK', 'KPay', 1500000),
            ('MMK', 'Wave', 1500000),
            # USDT
            ('USDT', 'Binance', 1500)
        ]
        
        print("\n🔄 Updating to new structure...")
        
        # Delete old balances that don't match admin banks
        old_banks_to_remove = [
            ('THB', 'KBank'),
            ('THB', 'KTB'),
            ('THB', 'SCB'),
            ('THB', 'Bangkok Bank'),
            ('MMK', 'CB Bank'),
        ]
        
        for currency, bank in old_banks_to_remove:
            cursor.execute(
                "DELETE FROM balances WHERE currency = ? AND bank = ?",
                (currency, bank)
            )
            print(f"  ❌ Removed: {currency} - {bank}")
        
        # Insert or update new balances
        for currency, bank, balance in new_balances:
            cursor.execute("""
                INSERT INTO balances (currency, bank, balance, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(currency, bank) DO UPDATE SET 
                balance = ?, updated_at = ?
            """, (currency, bank, balance, datetime.now(), balance, datetime.now()))
            print(f"  ✅ Set: {currency} - {bank} = {balance:,.2f}")
        
        conn.commit()
        
        # Show final balances
        cursor.execute("SELECT currency, bank, balance FROM balances ORDER BY currency, bank")
        final_balances = cursor.fetchall()
        
        print("\n💰 Final Balances:")
        current_currency = None
        for currency, bank, balance in final_balances:
            if currency != current_currency:
                if current_currency is not None:
                    print()
                print(f"{currency}:")
                current_currency = currency
            print(f"  • {bank}: {balance:,.2f}")
        
        print("\n✅ Balances updated successfully!")
        print("\n📋 Your admin bank accounts now match the balance structure!")
        
    except Exception as e:
        print(f"❌ Error updating balances: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    update_balances()

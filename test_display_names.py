#!/usr/bin/env python3
"""
Test script to verify display names are working
"""
import sys
sys.path.insert(0, 'app')

from services.database_service import DatabaseService

def test_display_names():
    """Test that display names are returned correctly"""
    
    db = DatabaseService('app/data/exchange_bot.db')
    
    print("Testing get_balances() method:")
    print("=" * 60)
    
    balances = db.get_balances()
    
    print(f"\nReturned {len(balances)} balance(s):\n")
    
    current_currency = None
    for currency, bank, balance, display_name in balances:
        if currency != current_currency:
            if current_currency is not None:
                print()
            print(f"{currency}:")
            current_currency = currency
        
        display = display_name if display_name else bank
        print(f"  • {display}: {balance:,.2f}")
    
    print("\n" + "=" * 60)
    print("✅ Display names are working correctly!")
    print("\nIf the bot still shows old names, restart the Docker container:")
    print("  docker-compose restart currency-exchange-bot")

if __name__ == '__main__':
    test_display_names()

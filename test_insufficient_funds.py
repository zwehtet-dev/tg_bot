#!/usr/bin/env python3
"""
Test script for insufficient funds validation
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.services.database_service import DatabaseService

def test_insufficient_funds():
    """Test insufficient funds checking logic"""
    db = DatabaseService("exchange_bot.db")
    
    print("=" * 60)
    print("INSUFFICIENT FUNDS TEST")
    print("=" * 60)
    
    # Get current balances
    balances = db.get_balances()
    print("\n📊 Current Balances:")
    for currency, bank, balance in balances:
        print(f"  {currency} - {bank}: {balance:,.2f}")
    
    # Test scenarios
    print("\n" + "=" * 60)
    print("TEST SCENARIOS")
    print("=" * 60)
    
    # Scenario 1: Sufficient funds
    print("\n✅ Scenario 1: Sufficient Funds")
    mmk_bank = "AYA"
    mmk_balance = db.get_balance('MMK', mmk_bank)
    test_amount = 100000
    result_balance = mmk_balance - test_amount
    
    print(f"  Bank: {mmk_bank}")
    print(f"  Current Balance: {mmk_balance:,.2f} MMK")
    print(f"  Transaction Amount: {test_amount:,.2f} MMK")
    print(f"  Result Balance: {result_balance:,.2f} MMK")
    
    if result_balance < 0:
        print(f"  ❌ INSUFFICIENT FUNDS - Shortage: {abs(result_balance):,.2f} MMK")
    else:
        print(f"  ✅ SUFFICIENT FUNDS - Transaction can proceed")
    
    # Scenario 2: Insufficient funds
    print("\n❌ Scenario 2: Insufficient Funds")
    test_amount_large = mmk_balance + 500000
    result_balance_large = mmk_balance - test_amount_large
    
    print(f"  Bank: {mmk_bank}")
    print(f"  Current Balance: {mmk_balance:,.2f} MMK")
    print(f"  Transaction Amount: {test_amount_large:,.2f} MMK")
    print(f"  Result Balance: {result_balance_large:,.2f} MMK")
    
    if result_balance_large < 0:
        print(f"  ❌ INSUFFICIENT FUNDS - Shortage: {abs(result_balance_large):,.2f} MMK")
    else:
        print(f"  ✅ SUFFICIENT FUNDS - Transaction can proceed")
    
    # Scenario 3: Exact balance
    print("\n⚖️  Scenario 3: Exact Balance")
    test_amount_exact = mmk_balance
    result_balance_exact = mmk_balance - test_amount_exact
    
    print(f"  Bank: {mmk_bank}")
    print(f"  Current Balance: {mmk_balance:,.2f} MMK")
    print(f"  Transaction Amount: {test_amount_exact:,.2f} MMK")
    print(f"  Result Balance: {result_balance_exact:,.2f} MMK")
    
    if result_balance_exact < 0:
        print(f"  ❌ INSUFFICIENT FUNDS - Shortage: {abs(result_balance_exact):,.2f} MMK")
    else:
        print(f"  ✅ SUFFICIENT FUNDS - Transaction can proceed")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_insufficient_funds()

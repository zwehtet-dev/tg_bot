#!/usr/bin/env python3
"""
Initialize admin bank accounts
Run this once to set up your receiving accounts
"""
import sqlite3
import sys

# Database path (auto-detect Docker or local)
import os
if os.path.exists('/app/data/exchange_bot.db'):
    DB_PATH = '/app/data/exchange_bot.db'  # Inside Docker
else:
    DB_PATH = 'data/exchange_bot.db'  # Local

# Admin bank accounts to add with initial balances
ADMIN_ACCOUNTS = [
    # THB Accounts (Thai Baht receiving accounts)
    {
        'currency': 'THB',
        'bank_name': 'KrungthaiBank',
        'account_number': '123-4-56789-0',
        'account_name': 'MissThinZarHtet',
        'balance': 150000.0
    },
    {
        'currency': 'THB',
        'bank_name': 'PromptPay',
        'account_number': '123-45678901-4093',
        'account_name': 'ThuKhaZaw',
        'balance': 150000.0
    },
    {
        'currency': 'THB',
        'bank_name': 'SiamCommercialBank',
        'account_number': '884-2-123935',
        'account_name': 'MinMyatNwe',
        'balance': 150000.0
    },
    
    # MMK Accounts (Myanmar Kyat sending accounts)
    {
        'currency': 'MMK',
        'bank_name': 'KBZ',
        'account_number': '12345678901234',
        'account_name': 'AdminKBZ',
        'balance': 1500000.0
    },
    {
        'currency': 'MMK',
        'bank_name': 'AYA',
        'account_number': '12345678901234',
        'account_name': 'AdminAYA',
        'balance': 1500000.0
    },
    {
        'currency': 'MMK',
        'bank_name': 'KPay',
        'account_number': '09123456789',
        'account_name': 'AdminKPay',
        'balance': 1500000.0
    },
    {
        'currency': 'MMK',
        'bank_name': 'Wave',
        'account_number': '09123456789',
        'account_name': 'AdminWave',
        'balance': 1500000.0
    },
]

def init_accounts():
    """Initialize admin bank accounts"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("🏦 Initializing admin bank accounts...")
        print()
        
        for account in ADMIN_ACCOUNTS:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO admin_bank_accounts 
                    (currency, bank_name, account_number, account_name, balance)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    account['currency'],
                    account['bank_name'],
                    account['account_number'],
                    account['account_name'],
                    account.get('balance', 0.0)
                ))
                
                if cursor.rowcount > 0:
                    print(f"✅ Added: {account['currency']} | {account['bank_name']} | {account['account_name']}")
                else:
                    print(f"⏭️  Exists: {account['currency']} | {account['bank_name']} | {account['account_name']}")
                    
            except Exception as e:
                print(f"❌ Error adding {account['bank_name']}: {e}")
        
        conn.commit()
        
        # Verify
        print()
        print("📋 Current admin accounts:")
        cursor.execute("""
            SELECT id, currency, bank_name, account_number, account_name, balance 
            FROM admin_bank_accounts 
            WHERE is_active = 1
            ORDER BY currency, bank_name
        """)
        
        accounts = cursor.fetchall()
        for acc in accounts:
            print(f"  ID:{acc[0]} | {acc[1]} | {acc[2]} | {acc[3]} | {acc[4]} | Balance: {acc[5]:,.2f}")
        
        print()
        print(f"✅ Total: {len(accounts)} accounts initialized")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_accounts()

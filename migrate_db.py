#!/usr/bin/env python3
"""
Database migration script to add new tables and features
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = "exchange_bot.db"


def migrate_database():
    """Run database migrations"""
    print("Starting database migration...")
    
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found. Will be created on first run.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if bot_settings table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bot_settings'")
        if not cursor.fetchone():
            print("Creating bot_settings table...")
            cursor.execute("""
                CREATE TABLE bot_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ bot_settings table created")
        
        # Check if admin_bank_accounts table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='admin_bank_accounts'")
        if not cursor.fetchone():
            print("Creating admin_bank_accounts table...")
            cursor.execute("""
                CREATE TABLE admin_bank_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    currency TEXT NOT NULL,
                    bank_name TEXT NOT NULL,
                    account_number TEXT NOT NULL,
                    account_name TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(currency, bank_name, account_number)
                )
            """)
            print("✅ admin_bank_accounts table created")
        
        # Check if admin_thb_bank column exists in transactions
        cursor.execute("PRAGMA table_info(transactions)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'admin_thb_bank' not in columns:
            print("Adding admin_thb_bank column to transactions table...")
            cursor.execute("ALTER TABLE transactions ADD COLUMN admin_thb_bank TEXT")
            print("✅ admin_thb_bank column added")
        
        # Add admin bank accounts
        print("\nAdding admin bank accounts...")
        sample_accounts = [
            ('THB', 'KrungthaiBank', '6612340987', 'MissThinZarHtet'),
            ('THB', 'PromptPay', '123-45678901-4093', 'ThuKhaZaw'),
            ('THB', 'SiamCommercialBank', '884-2-123935', 'MinMyatNwe'),
            ('MMK', 'KBZ', '1122334455', 'YOUR COMPANY NAME'),
            ('MMK', 'AYA', '5544332211', 'YOUR COMPANY NAME'),
            ('MMK', 'KPay', '09123456789', 'YOUR COMPANY NAME'),
        ]
        
        for currency, bank_name, account_number, account_name in sample_accounts:
            try:
                cursor.execute("""
                    INSERT INTO admin_bank_accounts 
                    (currency, bank_name, account_number, account_name)
                    VALUES (?, ?, ?, ?)
                """, (currency, bank_name, account_number, account_name))
                print(f"  ✅ Added: {currency} - {bank_name} - {account_number}")
            except sqlite3.IntegrityError:
                print(f"  ⏭️  Skipped (already exists): {currency} - {bank_name}")
        
        conn.commit()
        print("\n✅ Database migration completed successfully!")
        print("\n⚠️  IMPORTANT: Update the sample bank accounts with your real account details!")
        print("   Use: /addbank command or edit the database directly")
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate_database()

#!/usr/bin/env python3
"""
Migration script to add balance and updated_at columns to admin_bank_accounts table
"""
import sqlite3
import sys

def migrate_database():
    """Add balance and updated_at columns to admin_bank_accounts table"""
    
    db_path = 'exchange_bot.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current columns
        cursor.execute("PRAGMA table_info(admin_bank_accounts)")
        columns = [col[1] for col in cursor.fetchall()]
        
        changes_made = False
        
        # Add balance column if it doesn't exist
        if 'balance' not in columns:
            print("Adding 'balance' column to admin_bank_accounts table...")
            cursor.execute("ALTER TABLE admin_bank_accounts ADD COLUMN balance REAL DEFAULT 0.0")
            conn.commit()
            print("✅ Successfully added 'balance' column!")
            changes_made = True
        else:
            print("✅ Column 'balance' already exists!")
        
        # Add updated_at column if it doesn't exist
        if 'updated_at' not in columns:
            print("Adding 'updated_at' column to admin_bank_accounts table...")
            cursor.execute("ALTER TABLE admin_bank_accounts ADD COLUMN updated_at TIMESTAMP")
            conn.commit()
            print("✅ Successfully added 'updated_at' column!")
            changes_made = True
        else:
            print("✅ Column 'updated_at' already exists!")
        
        if not changes_made:
            print("\n✅ All columns already exist, no migration needed!")
        
        # Verify
        cursor.execute("PRAGMA table_info(admin_bank_accounts)")
        columns = cursor.fetchall()
        
        print("\nCurrent table structure:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    print("Database Migration: Add balance and updated_at columns")
    print("=" * 50)
    print()
    
    migrate_database()
    
    print("\n✅ Migration complete!")

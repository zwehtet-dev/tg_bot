#!/usr/bin/env python3
"""
Migration script to add display_name column to admin_bank_accounts table
"""
import sqlite3
import sys

def migrate_database():
    """Add display_name column to admin_bank_accounts table"""
    
    db_path = 'exchange_bot.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(admin_bank_accounts)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'display_name' in columns:
            print("✅ Column 'display_name' already exists!")
            conn.close()
            return True
        
        print("Adding 'display_name' column to admin_bank_accounts table...")
        
        # Add the column
        cursor.execute("ALTER TABLE admin_bank_accounts ADD COLUMN display_name TEXT")
        conn.commit()
        
        print("✅ Successfully added 'display_name' column!")
        
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
    print("Database Migration: Add display_name column")
    print("=" * 50)
    print()
    
    migrate_database()
    
    print("\n✅ Migration complete!")
    print("\nYou can now run: python update_display_names.py")

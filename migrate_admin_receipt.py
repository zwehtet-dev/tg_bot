#!/usr/bin/env python3
"""
Migration script to add admin_receipt_path column to transactions table
"""
import sqlite3
import sys

def migrate_database(db_path='exchange_bot.db'):
    """Add admin_receipt_path column if it doesn't exist"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(transactions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'admin_receipt_path' not in columns:
            print("Adding admin_receipt_path column to transactions table...")
            cursor.execute("""
                ALTER TABLE transactions 
                ADD COLUMN admin_receipt_path TEXT
            """)
            conn.commit()
            print("✅ Migration completed successfully!")
        else:
            print("✅ Column admin_receipt_path already exists. No migration needed.")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'exchange_bot.db'
    print(f"Migrating database: {db_path}")
    migrate_database(db_path)

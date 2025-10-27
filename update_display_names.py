#!/usr/bin/env python3
"""
Script to update display names for existing bank accounts
"""
import sqlite3
import sys

def update_display_names():
    """Update display names for existing bank accounts"""
    
    # Mappings based on your requirements
    display_name_mappings = {
        'KrungthaiBank': 'TZH (K Bank)',
        'PromptPay': 'TKZ (PP)',
        'SiamCommercialBank': 'MMN (SCB)',
        'AYA': 'AYA',
        'KBZ': 'KBZ',
        'KPay': 'KPay',
        'Wave': 'Wave',
    }
    
    db_path = 'exchange_bot.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all bank accounts
        cursor.execute("SELECT id, bank_name, display_name FROM admin_bank_accounts")
        accounts = cursor.fetchall()
        
        print("Current bank accounts:")
        for acc_id, bank_name, display_name in accounts:
            print(f"  ID {acc_id}: {bank_name} -> {display_name or '(no display name)'}")
        
        print("\nUpdating display names...")
        
        updated_count = 0
        for acc_id, bank_name, current_display in accounts:
            if bank_name in display_name_mappings:
                new_display = display_name_mappings[bank_name]
                cursor.execute(
                    "UPDATE admin_bank_accounts SET display_name = ? WHERE id = ?",
                    (new_display, acc_id)
                )
                print(f"  ✓ Updated ID {acc_id}: {bank_name} -> {new_display}")
                updated_count += 1
        
        conn.commit()
        print(f"\n✅ Updated {updated_count} account(s)")
        
        # Show updated accounts
        cursor.execute("SELECT id, bank_name, display_name FROM admin_bank_accounts")
        accounts = cursor.fetchall()
        
        print("\nUpdated bank accounts:")
        for acc_id, bank_name, display_name in accounts:
            print(f"  ID {acc_id}: {bank_name} -> {display_name or '(no display name)'}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    print("Bank Account Display Name Updater")
    print("=" * 50)
    print("\nThis script will update display names for your bank accounts.")
    print("Edit the 'display_name_mappings' dictionary in this script first!\n")
    
    response = input("Continue? (y/n): ")
    if response.lower() == 'y':
        update_display_names()
    else:
        print("Cancelled.")

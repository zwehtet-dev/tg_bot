#!/usr/bin/env python3
"""
Test receiver account validation with case-insensitive matching
"""
import sys
sys.path.insert(0, '.')

from app.services.database_service import DatabaseService

# Initialize database service
db = DatabaseService("exchange_bot.db")

print("Testing Receiver Account Validation")
print("=" * 70)

# Test cases with different name formats
test_cases = [
    # (input_name, input_bank, should_match)
    ("MIN MYAT NWE", "SiamCommercialBank", True),
    ("MinMyatNwe", "Siam Commercial", True),
    ("minmyatnwe", "SCB", True),
    ("Miss Thin Zar Htet", "KrungthaiBank", True),
    ("MISSTHINZARHTET", "Krung Thai", True),
    ("ThuKhaZaw", "PromptPay", True),
    ("THU KHA ZAW", "Prompt Pay", True),
    ("Wrong Name", "KrungthaiBank", False),
    ("MinMyatNwe", "WrongBank", False),
]

print("\nTesting THB Admin Accounts:")
print("-" * 70)

for input_name, input_bank, should_match in test_cases:
    result = db.validate_receiver_account(input_name, input_bank, 'THB')
    matched = result is not None
    
    status = "✅" if matched == should_match else "❌"
    
    print(f"\n{status} Input: '{input_name}' at '{input_bank}'")
    print(f"   Expected: {'Match' if should_match else 'No Match'}")
    print(f"   Got: {'Match' if matched else 'No Match'}")
    
    if matched and result:
        print(f"   Matched: {result[3]} at {result[1]}")

print("\n" + "=" * 70)
print("✅ Validation test completed!")

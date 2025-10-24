#!/usr/bin/env python3
"""
Test name normalization for case-insensitive matching
"""

def normalize_name(name: str) -> str:
    """Normalize name for comparison (remove spaces, lowercase)"""
    if not name:
        return ""
    # Remove all spaces and convert to lowercase
    return ''.join(name.split()).lower()


# Test cases
test_cases = [
    ("MIN MYAT NWE", "MinMyatNwe"),
    ("MissThinZarHtet", "Miss Thin Zar Htet"),
    ("ThuKhaZaw", "THU KHA ZAW"),
    ("AUNG AUNG", "aung aung"),
    ("John Doe", "JOHNDOE"),
]

print("Testing Name Normalization:")
print("=" * 60)

for name1, name2 in test_cases:
    norm1 = normalize_name(name1)
    norm2 = normalize_name(name2)
    matches = norm1 == norm2
    
    print(f"\nOriginal 1: '{name1}'")
    print(f"Original 2: '{name2}'")
    print(f"Normalized 1: '{norm1}'")
    print(f"Normalized 2: '{norm2}'")
    print(f"Match: {'✅ YES' if matches else '❌ NO'}")

print("\n" + "=" * 60)
print("✅ All test cases completed!")

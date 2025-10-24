"""
Test script to verify all imports work correctly
"""
import sys


def test_imports():
    """Test all module imports"""
    print("🧪 Testing imports...\n")
    
    errors = []
    
    # Test config
    try:
        from app.config.settings import Config
        print("✓ Config imported successfully")
    except Exception as e:
        errors.append(f"Config import failed: {e}")
        print(f"✗ Config import failed: {e}")
    
    # Test services
    try:
        from app.services.database_service import DatabaseService
        print("✓ DatabaseService imported successfully")
    except Exception as e:
        errors.append(f"DatabaseService import failed: {e}")
        print(f"✗ DatabaseService import failed: {e}")
    
    try:
        from app.services.ocr_service import OCRService
        print("✓ OCRService imported successfully")
    except Exception as e:
        errors.append(f"OCRService import failed: {e}")
        print(f"✗ OCRService import failed: {e}")
    
    # Test handlers
    try:
        from app.handlers.user_handlers import UserHandlers
        print("✓ UserHandlers imported successfully")
    except Exception as e:
        errors.append(f"UserHandlers import failed: {e}")
        print(f"✗ UserHandlers import failed: {e}")
    
    try:
        from app.handlers.admin_handlers import AdminHandlers
        print("✓ AdminHandlers imported successfully")
    except Exception as e:
        errors.append(f"AdminHandlers import failed: {e}")
        print(f"✗ AdminHandlers import failed: {e}")
    
    # Test utils
    try:
        from app.utils.validators import Validators
        from app.utils.formatters import Formatters
        print("✓ Utils imported successfully")
    except Exception as e:
        errors.append(f"Utils import failed: {e}")
        print(f"✗ Utils import failed: {e}")
    
    # Test main bot
    try:
        from app.bot import ExchangeBot
        print("✓ ExchangeBot imported successfully")
    except Exception as e:
        errors.append(f"ExchangeBot import failed: {e}")
        print(f"✗ ExchangeBot import failed: {e}")
    
    print("\n" + "="*50)
    
    if errors:
        print(f"\n❌ {len(errors)} import error(s) found:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("\n✅ All imports successful!")
        return True


def test_database():
    """Test database initialization"""
    print("\n🧪 Testing database...\n")
    
    try:
        from app.services.database_service import DatabaseService
        
        # Create test database
        db = DatabaseService("test_exchange.db")
        print("✓ Database created successfully")
        
        # Test rate operations
        db.initialize_exchange_rate(121.5)
        rate = db.get_current_rate()
        print(f"✓ Exchange rate: {rate}")
        
        # Test balance initialization
        test_balances = [
            ('THB', 'Test Bank', 100000),
            ('MMK', 'Test Bank', 1000000)
        ]
        db.initialize_balances(test_balances)
        balances = db.get_balances()
        print(f"✓ Balances initialized: {len(balances)} entries")
        
        # Cleanup
        import os
        os.remove("test_exchange.db")
        print("✓ Test database cleaned up")
        
        return True
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False


def test_validators():
    """Test validator functions"""
    print("\n🧪 Testing validators...\n")
    
    try:
        from app.utils.validators import Validators
        
        # Test amount validation
        assert Validators.validate_amount("1000") == 1000.0
        assert Validators.validate_amount("1,000.50") == 1000.50
        assert Validators.validate_amount("-100") is None
        assert Validators.validate_amount("invalid") is None
        print("✓ Amount validation works")
        
        # Test bank info validation
        result = Validators.validate_bank_info("AYA | 123456 | John Doe")
        assert result == ("AYA", "123456", "John Doe")
        assert Validators.validate_bank_info("Invalid") is None
        print("✓ Bank info validation works")
        
        # Test bank support check
        assert Validators.is_supported_bank("KBZ Bank", ["KBZ", "AYA"]) is True
        assert Validators.is_supported_bank("Unknown Bank", ["KBZ", "AYA"]) is False
        print("✓ Bank support check works")
        
        return True
    except Exception as e:
        print(f"✗ Validator test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("="*50)
    print("Telegram Exchange Bot - Test Suite")
    print("="*50)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Database", test_database()))
    results.append(("Validators", test_validators()))
    
    # Summary
    print("\n" + "="*50)
    print("Test Summary")
    print("="*50)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "="*50)
    if all_passed:
        print("✅ All tests passed! Bot is ready to run.")
        print("\nTo start the bot, run:")
        print("  python main.py")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()

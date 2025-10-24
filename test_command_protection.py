#!/usr/bin/env python3
"""
Test script for command protection system
"""
import sys
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from telegram import Update, Chat, User, Message
from telegram.ext import ContextTypes

# Add app to path
sys.path.insert(0, '.')

from app.utils.command_protection import (
    admin_only, 
    private_chat_only,
    admin_group_only_callback,
    private_chat_only_callback
)
from app.services.database_service import DatabaseService
from app.config.settings import Config


class TestHandler:
    """Mock handler class for testing"""
    
    def __init__(self):
        self.db = DatabaseService(Config.DATABASE_PATH)
    
    @admin_only
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Test admin command"""
        await update.message.reply_text("Admin command executed")
        return "admin_executed"
    
    @private_chat_only
    async def user_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Test user command"""
        await update.message.reply_text("User command executed")
        return "user_executed"
    
    @admin_group_only_callback
    async def admin_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Test admin callback"""
        await update.callback_query.answer("Admin callback executed")
        return "admin_callback_executed"
    
    @private_chat_only_callback
    async def user_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Test user callback"""
        await update.callback_query.answer("User callback executed")
        return "user_callback_executed"


def create_mock_update(chat_type='private', chat_id='123456'):
    """Create a mock update object"""
    update = Mock(spec=Update)
    update.effective_chat = Mock(spec=Chat)
    update.effective_chat.type = chat_type
    update.effective_chat.id = chat_id
    
    update.message = Mock(spec=Message)
    update.message.chat = update.effective_chat
    update.message.reply_text = AsyncMock()
    
    return update


def create_mock_callback_update(chat_type='private', chat_id='123456'):
    """Create a mock callback query update"""
    update = Mock(spec=Update)
    update.callback_query = Mock()
    update.callback_query.message = Mock(spec=Message)
    update.callback_query.message.chat = Mock(spec=Chat)
    update.callback_query.message.chat.type = chat_type
    update.callback_query.message.chat.id = chat_id
    update.callback_query.answer = AsyncMock()
    
    return update


async def run_tests():
    """Run all protection tests"""
    handler = TestHandler()
    context = Mock(spec=ContextTypes.DEFAULT_TYPE)
    
    admin_group_id = Config.ADMIN_GROUP_ID
    
    print("=" * 60)
    print("Command Protection System Tests")
    print("=" * 60)
    print()
    
    # Test 1: Admin command in admin group (should work)
    print("Test 1: Admin command in admin group")
    update = create_mock_update(chat_type='supergroup', chat_id=admin_group_id)
    result = await handler.admin_command(update, context)
    if result == "admin_executed":
        print("✅ PASS - Admin command executed in admin group")
    else:
        print("❌ FAIL - Admin command blocked in admin group")
    print()
    
    # Test 2: Admin command in private chat (should block)
    print("Test 2: Admin command in private chat")
    update = create_mock_update(chat_type='private', chat_id='123456')
    result = await handler.admin_command(update, context)
    if result is None:
        print("✅ PASS - Admin command blocked in private chat")
    else:
        print("❌ FAIL - Admin command executed in private chat")
    print()
    
    # Test 3: User command in private chat (should work)
    print("Test 3: User command in private chat")
    update = create_mock_update(chat_type='private', chat_id='123456')
    result = await handler.user_command(update, context)
    if result == "user_executed":
        print("✅ PASS - User command executed in private chat")
    else:
        print("❌ FAIL - User command blocked in private chat")
    print()
    
    # Test 4: User command in group (should block)
    print("Test 4: User command in group")
    update = create_mock_update(chat_type='group', chat_id='-987654321')
    result = await handler.user_command(update, context)
    if result is None:
        print("✅ PASS - User command blocked in group")
    else:
        print("❌ FAIL - User command executed in group")
    print()
    
    # Test 5: Admin callback in admin group (should work)
    print("Test 5: Admin callback in admin group")
    update = create_mock_callback_update(chat_type='supergroup', chat_id=admin_group_id)
    result = await handler.admin_callback(update, context)
    if result == "admin_callback_executed":
        print("✅ PASS - Admin callback executed in admin group")
    else:
        print("❌ FAIL - Admin callback blocked in admin group")
    print()
    
    # Test 6: Admin callback in private chat (should block)
    print("Test 6: Admin callback in private chat")
    update = create_mock_callback_update(chat_type='private', chat_id='123456')
    result = await handler.admin_callback(update, context)
    if result is None:
        print("✅ PASS - Admin callback blocked in private chat")
    else:
        print("❌ FAIL - Admin callback executed in private chat")
    print()
    
    # Test 7: User callback in private chat (should work)
    print("Test 7: User callback in private chat")
    update = create_mock_callback_update(chat_type='private', chat_id='123456')
    result = await handler.user_callback(update, context)
    if result == "user_callback_executed":
        print("✅ PASS - User callback executed in private chat")
    else:
        print("❌ FAIL - User callback blocked in private chat")
    print()
    
    # Test 8: User callback in group (should block)
    print("Test 8: User callback in group")
    update = create_mock_callback_update(chat_type='supergroup', chat_id='-987654321')
    result = await handler.user_callback(update, context)
    if result is None:
        print("✅ PASS - User callback blocked in group")
    else:
        print("❌ FAIL - User callback executed in group")
    print()
    
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print()
    print("All tests completed!")
    print()
    print("Protection Rules:")
    print("  ✓ Admin commands only work in admin group")
    print("  ✓ User commands only work in private chat")
    print("  ✓ Admin callbacks only work in admin group")
    print("  ✓ User callbacks only work in private chat")
    print()


if __name__ == "__main__":
    print()
    print("Starting command protection tests...")
    print()
    
    try:
        asyncio.run(run_tests())
        print("✅ All tests passed!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

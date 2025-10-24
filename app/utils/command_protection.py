"""
Command protection utilities to ensure commands run in correct contexts
"""
import logging
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

from app.config.settings import Config

logger = logging.getLogger(__name__)


def admin_only(func):
    """
    Decorator to ensure command only runs in admin group
    Blocks execution in private chats
    """
    @wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = str(update.effective_chat.id)
        chat_type = update.effective_chat.type
        
        # Get admin group ID from database or config
        admin_group_id = self.db.get_setting('admin_group_id') or Config.ADMIN_GROUP_ID
        
        # Check if command is in admin group
        if chat_id != admin_group_id:
            logger.warning(
                f"Admin command '{func.__name__}' blocked in chat {chat_id} "
                f"(type: {chat_type}). Only allowed in admin group."
            )
            await update.message.reply_text(
                "⚠️ This command can only be used in the admin group."
            )
            return
        
        # Execute the command
        return await func(self, update, context)
    
    return wrapper


def private_chat_only(func):
    """
    Decorator to ensure command only runs in private chat with bot
    Blocks execution in groups
    """
    @wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_type = update.effective_chat.type
        
        # Check if command is in private chat
        if chat_type != 'private':
            logger.warning(
                f"User command '{func.__name__}' blocked in {chat_type} chat. "
                f"Only allowed in private chat."
            )
            await update.message.reply_text(
                "⚠️ This command can only be used in private chat with the bot.\n\n"
                "Please message me directly: @balance_transfer_tg_bot"
            )
            return
        
        # Execute the command
        return await func(self, update, context)
    
    return wrapper


def admin_group_only_callback(func):
    """
    Decorator for callback queries that should only work in admin group
    """
    @wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        chat_id = str(query.message.chat.id)
        chat_type = query.message.chat.type
        
        # Get admin group ID from database or config
        admin_group_id = self.db.get_setting('admin_group_id') or Config.ADMIN_GROUP_ID
        
        # Check if callback is in admin group
        if chat_id != admin_group_id:
            logger.warning(
                f"Admin callback '{func.__name__}' blocked in chat {chat_id} "
                f"(type: {chat_type}). Only allowed in admin group."
            )
            await query.answer("⚠️ This action can only be performed in the admin group.", show_alert=True)
            return
        
        # Execute the callback
        return await func(self, update, context)
    
    return wrapper


def private_chat_only_callback(func):
    """
    Decorator for callback queries that should only work in private chat
    """
    @wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        chat_type = query.message.chat.type
        
        # Check if callback is in private chat
        if chat_type != 'private':
            logger.warning(
                f"User callback '{func.__name__}' blocked in {chat_type} chat. "
                f"Only allowed in private chat."
            )
            await query.answer("⚠️ This action can only be performed in private chat with the bot.", show_alert=True)
            return
        
        # Execute the callback
        return await func(self, update, context)
    
    return wrapper

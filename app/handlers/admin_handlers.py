"""
Admin handlers for receipt verification and transaction management
"""
import os
import logging
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TimedOut, NetworkError

from app.config.settings import Config
from app.services.database_service import DatabaseService
from app.services.ocr_service import OCRService
from app.utils.command_protection import admin_only, admin_group_only_callback

logger = logging.getLogger(__name__)


class AdminHandlers:
    """Handle admin operations for transaction verification"""
    
    def __init__(self, db_service: DatabaseService, ocr_service: OCRService):
        """
        Initialize admin handlers
        
        Args:
            db_service: Database service instance
            ocr_service: OCR service instance
        """
        self.db = db_service
        self.ocr = ocr_service
        self.config = Config
        logger.info("Admin handlers initialized")
    
    @admin_only
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show current balances (admin only)"""
        balances = self.db.get_balances()
        
        message = "💰 **Current Bank Balances:**\n\n"
        
        current_currency = None
        for currency, bank, balance, display_name in balances:
            if currency != current_currency:
                if current_currency is not None:
                    message += "\n"
                message += f"**{currency}:**\n"
                current_currency = currency
            # Use display_name if available, otherwise fall back to bank name
            display = display_name if display_name else 'No Display Name'
            message += f"• {display}: {balance:,.2f}\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    @admin_only
    async def rate_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View or set exchange rate (admin only)"""
        if context.args:
            try:
                new_rate = float(context.args[0])
                self.db.update_rate(new_rate)
                await update.message.reply_text(
                    f"✅ **Exchange rate updated**\n\n"
                    f"New rate: 1 THB = {new_rate} MMK",
                    parse_mode='Markdown'
                )
            except ValueError:
                await update.message.reply_text("❌ Invalid rate value. Use: /rate 121.5")
        else:
            rate = self.db.get_current_rate()
            await update.message.reply_text(
                f"📊 **Current Exchange Rate**\n\n"
                f"1 THB = {rate} MMK\n\n"
                f"To update: `/rate <new_rate>`\n"
                f"Example: `/rate 122.0`",
                parse_mode='Markdown'
            )
    
    @admin_only
    async def transactions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show today's transactions (admin only)"""
        transactions = self.db.get_today_transactions()
        
        if not transactions:
            await update.message.reply_text("📊 No transactions today.")
            return
        
        message = "📊 **Today's Transactions:**\n\n"
        total_thb = 0
        total_mmk = 0
        confirmed_count = 0
        pending_count = 0
        
        for txn in transactions:
            status_emoji = "✅" if txn[13] == 'confirmed' else "⏳" if txn[13] == 'pending' else "❌"
            message += f"{status_emoji} **#{txn[0]}** - {txn[6]} THB → {txn[7]:,.0f} MMK - `{txn[13]}`\n"
            
            if txn[13] == 'confirmed':
                total_thb += txn[6]
                total_mmk += txn[7]
                confirmed_count += 1
            elif txn[13] == 'pending':
                pending_count += 1
        
        message += f"\n**Summary:**\n"
        message += f"Total Confirmed: {confirmed_count}\n"
        message += f"Pending: {pending_count}\n"
        message += f"Total Volume: {total_thb:,.0f} THB → {total_mmk:,.0f} MMK"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    @admin_only
    async def handle_admin_receipt(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin receipt photo upload"""
        # Check if this is a reply to a transaction message
        if not update.message.reply_to_message:
            logger.debug("No reply_to_message found, skipping")
            return
        
        # Extract transaction ID from the replied message (could be text or caption)
        replied_text = update.message.reply_to_message.text or update.message.reply_to_message.caption
        logger.info(f"Admin receipt handler triggered. Replied text: {replied_text[:100] if replied_text else 'None'}")
        
        if not replied_text or ("Transaction ID:" not in replied_text and "Buy" not in replied_text):
            logger.debug("Message doesn't contain transaction markers, skipping")
            return
        
        # Try to extract transaction ID from message
        transaction_id = None
        
        # Method 1: Try to extract from inline keyboard (Cancel button)
        if hasattr(update.message.reply_to_message, 'reply_markup') and update.message.reply_to_message.reply_markup:
            # Extract from cancel button callback data
            for row in update.message.reply_to_message.reply_markup.inline_keyboard:
                for button in row:
                    if button.callback_data and button.callback_data.startswith('cancel_'):
                        transaction_id = int(button.callback_data.split('_')[1])
                        break
        
        # Method 2: If not found in keyboard, try to extract from message text
        # Look for pattern like "Transaction ID: #123" or just find the user ID and timestamp
        if not transaction_id and replied_text:
            # Try to find user ID in the message (format: "ID: 123456")
            import re
            user_id_match = re.search(r'ID:\s*(\d+)', replied_text)
            if user_id_match:
                user_id = int(user_id_match.group(1))
                # Get the most recent pending transaction for this user
                recent_txn = self.db.get_user_recent_pending_transaction(user_id)
                if recent_txn:
                    transaction_id = recent_txn[0]  # transaction ID is first column
                    logger.info(f"Found transaction #{transaction_id} for user {user_id} from message text")
        
        if not transaction_id:
            await update.message.reply_text("❌ Could not identify transaction. Please reply to the transaction message.")
            return
        
        # Get transaction to verify it exists and is pending
        transaction = self.db.get_transaction(transaction_id)
        if not transaction:
            await update.message.reply_text("❌ Transaction not found.")
            return
        
        # Check if transaction is already confirmed (not just pending)
        # Column indices: 0=id, 1=user_id, 2=username, 3=receipt_path, 4=admin_receipt_path,
        # 5=from_bank, 6=to_bank, 7=thb_amount, 8=mmk_amount, 9=rate, 10=user_bank_name,
        # 11=user_account_number, 12=user_account_name, 13=admin_bank, 14=admin_thb_bank, 15=status
        status = transaction[15]  # status column (16th column, index 15)
        if status == 'confirmed':
            await update.message.reply_text(f"❌ Transaction #{transaction_id} is already confirmed.")
            return
        elif status == 'cancelled':
            await update.message.reply_text(f"❌ Transaction #{transaction_id} has been cancelled.")
            return
        
        # Download admin receipt photo with retry logic for network timeouts
        photo = update.message.photo[-1]
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                file = await context.bot.get_file(photo.file_id)
                admin_receipt_path = f"{self.config.ADMIN_RECEIPTS_DIR}/admin_{transaction_id}_{datetime.now().timestamp()}.jpg"
                await file.download_to_drive(admin_receipt_path)
                break
            except (TimedOut, NetworkError) as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Network timeout on attempt {attempt + 1}, retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Failed to download admin receipt after {max_retries} attempts: {e}")
                    await update.message.reply_text(
                        f"❌ **Network Error**\n\n"
                        f"Unable to download receipt for transaction #{transaction_id} due to network issues.\n\n"
                        f"Please try uploading again in a moment."
                    )
                    return
        
        # Save admin receipt path to database
        self.db.update_transaction_admin_receipt(transaction_id, admin_receipt_path)
        
        logger.info(f"Admin receipt saved for transaction #{transaction_id}: {admin_receipt_path}")
        
        # Get MMK banks from database dynamically
        mmk_accounts = self.db.get_admin_bank_accounts('MMK')
        
        if not mmk_accounts:
            await update.message.reply_text(
                "❌ No MMK bank accounts configured. Please add MMK banks using /addbank command."
            )
            return
        
        # Build dynamic keyboard from database
        keyboard = []
        for acc_id, currency, bank_name, account_number, account_name, is_active, display_name in mmk_accounts:
            display = display_name if display_name else bank_name
            keyboard.append([InlineKeyboardButton(
                f"{display}", 
                callback_data=f"bank_{bank_name}_{transaction_id}"
            )])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Get transaction details for display
        thb_amount = transaction[7]  # thb_amount at index 7
        mmk_amount = transaction[8]  # mmk_amount at index 8
        user_bank = transaction[10]  # user_bank_name at index 10
        
        await update.message.reply_text(
            f"✅ **Receipt saved for Transaction #{transaction_id}**\n\n"
            f"💰 Amount: {thb_amount} THB → {mmk_amount:,.0f} MMK\n"
            f"🏦 User's Bank: {user_bank}\n\n"
            f"📤 **Select which MMK bank you used for transfer:**",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    @admin_group_only_callback
    async def admin_bank_selection_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle bank selection for manual confirmation"""
        query = update.callback_query
        await query.answer()
        
        parts = query.data.split('_')
        bank = parts[1]
        transaction_id = int(parts[2])
        
        # Get transaction details
        transaction = self.db.get_transaction(transaction_id)
        
        if not transaction:
            await query.edit_message_text("❌ Transaction not found.")
            return
        
        # Correct column indices based on actual schema
        user_id = transaction[1]
        thb_amount = transaction[7]  # thb_amount column (index 7)
        mmk_amount = transaction[8]  # mmk_amount column (index 8)
        admin_thb_bank = transaction[14]  # admin_thb_bank column (index 14)
        
        # Get balances before update
        balances_before = self.db.get_balances()
        mmk_before = next((b[2] for b in balances_before if b[0] == 'MMK' and b[1] == bank), 0)
        
        # Check for insufficient funds
        mmk_after = mmk_before - mmk_amount
        if mmk_after < 0:
            # Insufficient funds - notify admin
            await query.edit_message_text(
                f"{query.message.text}\n\n"
                f"⚠️ **INSUFFICIENT FUNDS - Transaction #{transaction_id}**\n\n"
                f"❌ Cannot process transaction\n"
                f"MMK Bank: {bank}\n"
                f"Current Balance: {mmk_before:,.2f} MMK\n"
                f"Required Amount: {mmk_amount:,.2f} MMK\n"
                f"Shortage: {abs(mmk_after):,.2f} MMK\n\n"
                f"⚠️ Please top up the {bank} account before confirming this transaction."
            )
            
            # Send alert to admin group
            try:
                admin_group_id = self.db.get_setting('admin_group_id') or self.config.ADMIN_GROUP_ID
                admin_topic_id = self.db.get_setting('admin_topic_id')
                
                alert_message = f"""🚨 **INSUFFICIENT FUNDS ALERT**

Transaction #{transaction_id} cannot be processed

💰 **MMK Account ({bank}):**
• Current Balance: {mmk_before:,.2f} MMK
• Required Amount: {mmk_amount:,.2f} MMK
• Shortage: {abs(mmk_after):,.2f} MMK

⚠️ Please top up the account and try again.

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
                
                if admin_topic_id:
                    await context.bot.send_message(
                        chat_id=admin_group_id,
                        text=alert_message,
                        message_thread_id=int(admin_topic_id),
                        parse_mode='Markdown'
                    )
                else:
                    await context.bot.send_message(
                        chat_id=admin_group_id,
                        text=alert_message,
                        parse_mode='Markdown'
                    )
            except Exception as e:
                logger.error(f"Error sending insufficient funds alert: {e}")
            
            return
        
        # Get THB balance (already updated when receipt was submitted)
        if admin_thb_bank:
            thb_current = next((b[2] for b in balances_before if b[0] == 'THB' and b[1] == admin_thb_bank), None)
            thb_before = thb_current - thb_amount if thb_current is not None else None
            thb_after = thb_current
        else:
            thb_before = None
            thb_after = None
        
        # Update MMK balance
        self.db.update_balance('MMK', bank, -mmk_amount)
        
        # Get balances after update
        balances_after = self.db.get_balances()
        mmk_after = next((b[2] for b in balances_after if b[0] == 'MMK' and b[1] == bank), 0)
        
        # Update transaction status with both banks
        self.db.update_transaction_with_admin_bank(transaction_id, 'confirmed', bank, admin_thb_bank)
        
        await query.edit_message_text(
            f"{query.message.text}\n\n"
            f"✅ **Transaction #{transaction_id} Confirmed**\n"
            f"MMK Bank: {bank}\n"
            f"Amount: {mmk_amount:,.0f} MMK"
        )
        
        # Send balance update to balance topic
        await self._send_balance_update(
            context, transaction_id, thb_amount, mmk_amount,
            admin_thb_bank, bank, thb_before, thb_after, mmk_before, mmk_after
        )
        
        # Notify user
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ **Payment Confirmed!**\n\n"
                     f"Transaction ID: #{transaction_id}\n"
                     f"Amount: {thb_amount} THB → {mmk_amount:,.0f} MMK\n\n"
                     f"The money has been transferred to your account.\n"
                     f"Thank you for using our service! 💚",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error notifying user: {e}")
    
    async def _send_balance_update(self, context, transaction_id, thb_amount, mmk_amount,
                                   thb_bank, mmk_bank, thb_before, thb_after, mmk_before, mmk_after):
        """Send balance update to balance topic"""
        balance_message = f"""💰 **Balance Update - Transaction #{transaction_id}**

"""
        
        # Add THB section if bank info is available
        if thb_bank and thb_before is not None and thb_after is not None:
            balance_message += f"""📊 **THB Account ({thb_bank}):**
• Before: {thb_before:,.2f} THB
• Change: +{thb_amount:,.2f} THB
• After: {thb_after:,.2f} THB

"""
        elif thb_bank:
            balance_message += f"""📊 **THB Account ({thb_bank}):**
• Change: +{thb_amount:,.2f} THB (already applied when receipt submitted)

"""
        
        balance_message += f"""📊 **MMK Account ({mmk_bank}):**
• Before: {mmk_before:,.2f} MMK
• Change: -{mmk_amount:,.2f} MMK
• After: {mmk_after:,.2f} MMK

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        try:
            # Get balance topic from database
            admin_group_id = self.db.get_setting('admin_group_id') or self.config.ADMIN_GROUP_ID
            balance_topic_id = self.db.get_setting('balance_topic_id')
            
            if balance_topic_id:
                await context.bot.send_message(
                    chat_id=admin_group_id,
                    text=balance_message,
                    message_thread_id=int(balance_topic_id),
                    parse_mode='Markdown'
                )
                logger.info(f"Balance update sent to topic {balance_topic_id}")
            else:
                # Send to main admin group if no balance topic configured
                logger.warning("Balance topic ID not configured, sending to main admin group")
                await context.bot.send_message(
                    chat_id=admin_group_id,
                    text=balance_message,
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Error sending balance update: {e}")
    

    
    @admin_group_only_callback
    async def admin_cancel_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle transaction cancellation"""
        query = update.callback_query
        await query.answer()
        
        transaction_id = int(query.data.split('_')[1])
        
        # Update transaction status
        self.db.update_transaction_status(transaction_id, 'cancelled')
        
        await query.edit_message_text(
            f"{query.message.text}\n\n"
            f"❌ Transaction #{transaction_id} cancelled."
        )
        
        # Notify user
        transaction = self.db.get_transaction(transaction_id)
        if transaction:
            user_id = transaction[1]
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"❌ Your transaction #{transaction_id} has been cancelled.\n"
                         f"Please contact support if you have questions."
                )
            except Exception as e:
                logger.error(f"Error notifying user: {e}")

    @admin_only
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View or update bot settings (admin only)"""
        if not context.args:
            # Show current settings
            admin_group_id = self.db.get_setting('admin_group_id') or self.config.ADMIN_GROUP_ID
            admin_topic_id = self.db.get_setting('admin_topic_id') or self.config.ADMIN_TOPIC_ID or "Not set"
            balance_topic_id = self.db.get_setting('balance_topic_id') or "Not set"
            
            message = f"""⚙️ **Bot Settings:**

📱 **Admin Group ID:** `{admin_group_id}`
💬 **Admin Topic ID:** `{admin_topic_id}`
💰 **Balance Topic ID:** `{balance_topic_id}`

**Update Settings:**
`/settings admin_group_id <value>`
`/settings admin_topic_id <value>`
`/settings balance_topic_id <value>`

**Example:**
`/settings balance_topic_id 12345`
"""
            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            # Update setting
            if len(context.args) < 2:
                await update.message.reply_text("❌ Usage: /settings <key> <value>")
                return
            
            key = context.args[0]
            value = context.args[1]
            
            valid_keys = ['admin_group_id', 'admin_topic_id', 'balance_topic_id']
            if key not in valid_keys:
                await update.message.reply_text(f"❌ Invalid key. Valid keys: {', '.join(valid_keys)}")
                return
            
            self.db.set_setting(key, value)
            await update.message.reply_text(f"✅ Setting updated: {key} = {value}")
    
    @admin_only
    async def add_bank_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add admin bank account (admin only)"""
        if len(context.args) < 4:
            message = """🏦 **Add Admin Bank Account**

**Usage:**
`/addbank <currency> <bank_name> <account_number> <account_name> [display_name]`

**Example:**
`/addbank THB KrungthaiBank 1234567890 COMPANY_NAME TZH_(K_Bank)`
`/addbank MMK KBZ 0987654321 COMPANY_NAME`

**Note:** Display name is optional and will be shown in balance reports
**Supported Currencies:** THB, MMK
"""
            await update.message.reply_text(message, parse_mode='Markdown')
            return
        
        currency = context.args[0].upper()
        bank_name = context.args[1]
        account_number = context.args[2]
        
        # Find where account_name ends and display_name begins
        # Look for a parameter that looks like a display name (contains parentheses or underscores)
        remaining_args = context.args[3:]
        account_name_parts = []
        display_name = None
        
        for i, arg in enumerate(remaining_args):
            # If arg contains parentheses or looks like a code, treat it as display_name
            if '(' in arg or '_' in arg or (len(arg) <= 5 and arg.isupper()):
                display_name = ' '.join(remaining_args[i:])
                break
            account_name_parts.append(arg)
        
        account_name = ' '.join(account_name_parts) if account_name_parts else remaining_args[0]
        
        if currency not in ['THB', 'MMK']:
            await update.message.reply_text("❌ Currency must be THB or MMK")
            return
        
        self.db.add_admin_bank_account(currency, bank_name, account_number, account_name, display_name)
        
        response = f"✅ **Admin Bank Account Added**\n\n"
        response += f"Currency: {currency}\n"
        response += f"Bank: {bank_name}\n"
        response += f"Account: {account_number}\n"
        response += f"Name: {account_name}\n"
        if display_name:
            response += f"Display Name: {display_name}\n"
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    @admin_only
    async def list_banks_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List admin bank accounts (admin only)"""
        currency_filter = context.args[0].upper() if context.args else None
        
        if currency_filter and currency_filter not in ['THB', 'MMK']:
            await update.message.reply_text("❌ Currency must be THB or MMK")
            return
        
        accounts = self.db.get_admin_bank_accounts(currency_filter)
        
        if not accounts:
            await update.message.reply_text("📋 No admin bank accounts found.")
            return
        
        message = "🏦 **Admin Bank Accounts:**\n\n"
        
        current_currency = None
        for acc_id, currency, bank_name, account_number, account_name, is_active, display_name in accounts:
            if currency != current_currency:
                if current_currency is not None:
                    message += "\n"
                message += f"**{currency}:**\n"
                current_currency = currency
            
            status = "✅" if is_active else "❌"
            display = f"{display_name} ({bank_name})" if display_name else bank_name
            message += f"{status} ID:{acc_id} | {display}\n"
            message += f"   {account_number} - {account_name}\n"
        
        message += f"\n**Deactivate:** `/removebank <id>`"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    @admin_only
    async def remove_bank_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Deactivate admin bank account (admin only)"""
        if not context.args:
            await update.message.reply_text("❌ Usage: /removebank <account_id>")
            return
        
        try:
            account_id = int(context.args[0])
            self.db.deactivate_admin_bank_account(account_id)
            await update.message.reply_text(f"✅ Bank account #{account_id} deactivated")
        except ValueError:
            await update.message.reply_text("❌ Invalid account ID")

    @admin_only
    async def adjust_balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Adjust balance for a specific bank (admin only)"""
        if len(context.args) < 3:
            message = """💰 **Adjust Bank Balance**

**Usage:**
`/adjust <currency> <bank_name> <amount>`

**Examples:**
`/adjust THB KrungthaiBank +5000` - Add 5000 THB
`/adjust MMK KBZ -10000` - Subtract 10000 MMK
`/adjust THB PromptPay 150000` - Set to 150000 THB

**Note:** Use + or - for relative changes, or just number for absolute value
"""
            await update.message.reply_text(message, parse_mode='Markdown')
            return
        
        currency = context.args[0].upper()
        bank_name = context.args[1]
        amount_str = context.args[2]
        
        if currency not in ['THB', 'MMK']:
            await update.message.reply_text("❌ Currency must be THB or MMK")
            return
        
        try:
            # Check if it's relative (+/-) or absolute
            if amount_str.startswith('+') or amount_str.startswith('-'):
                # Relative adjustment
                amount_change = float(amount_str)
                old_balance = self.db.get_balance(currency, bank_name)
                self.db.update_balance(currency, bank_name, amount_change)
                new_balance = self.db.get_balance(currency, bank_name)
                
                await update.message.reply_text(
                    f"✅ **Balance Adjusted**\n\n"
                    f"Currency: {currency}\n"
                    f"Bank: {bank_name}\n"
                    f"Old Balance: {old_balance:,.2f}\n"
                    f"Change: {amount_change:+,.2f}\n"
                    f"New Balance: {new_balance:,.2f}",
                    parse_mode='Markdown'
                )
            else:
                # Absolute value
                new_balance = float(amount_str)
                old_balance = self.db.get_balance(currency, bank_name)
                self.db.set_balance(currency, bank_name, new_balance)
                
                await update.message.reply_text(
                    f"✅ **Balance Set**\n\n"
                    f"Currency: {currency}\n"
                    f"Bank: {bank_name}\n"
                    f"Old Balance: {old_balance:,.2f}\n"
                    f"New Balance: {new_balance:,.2f}",
                    parse_mode='Markdown'
                )
                
        except ValueError:
            await update.message.reply_text("❌ Invalid amount format")
    
    @admin_only
    async def init_balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Initialize balance for a new bank (admin only)"""
        if len(context.args) < 3:
            message = """🏦 **Initialize Bank Balance**

**Usage:**
`/initbalance <currency> <bank_name> <initial_amount>`

**Examples:**
`/initbalance THB KrungthaiBank 150000`
`/initbalance MMK KBZ 1500000`

**Note:** This will create or update the balance entry
"""
            await update.message.reply_text(message, parse_mode='Markdown')
            return
        
        currency = context.args[0].upper()
        bank_name = context.args[1]
        initial_amount = context.args[2]
        
        if currency not in ['THB', 'MMK', 'USDT']:
            await update.message.reply_text("❌ Currency must be THB, MMK, or USDT")
            return
        
        try:
            amount = float(initial_amount)
            self.db.set_balance(currency, bank_name, amount)
            
            await update.message.reply_text(
                f"✅ **Balance Initialized**\n\n"
                f"Currency: {currency}\n"
                f"Bank: {bank_name}\n"
                f"Initial Balance: {amount:,.2f}",
                parse_mode='Markdown'
            )
        except ValueError:
            await update.message.reply_text("❌ Invalid amount format")

    @admin_only
    async def update_display_name_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Update display name for a bank account (admin only)"""
        if len(context.args) < 2:
            message = """🏷️ **Update Bank Display Name**

**Usage:**
`/updatedisplay <account_id> <display_name>`

**Examples:**
`/updatedisplay 1 TZH (K Bank)`
`/updatedisplay 2 TKZ (PP)`
`/updatedisplay 3 MMN (SCB)`

**Note:** Use `/listbanks` to see account IDs
"""
            await update.message.reply_text(message, parse_mode='Markdown')
            return
        
        try:
            account_id = int(context.args[0])
            display_name = ' '.join(context.args[1:])
            
            success = self.db.update_bank_display_name(account_id, display_name)
            
            if success:
                await update.message.reply_text(
                    f"✅ **Display Name Updated**\n\n"
                    f"Account ID: {account_id}\n"
                    f"New Display Name: {display_name}",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(f"❌ Account #{account_id} not found")
        except ValueError:
            await update.message.reply_text("❌ Invalid account ID")

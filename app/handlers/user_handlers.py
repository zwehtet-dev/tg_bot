"""
User handlers for exchange operations
"""
import os
import logging
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.error import TimedOut, NetworkError

from app.config.settings import Config
from app.services.database_service import DatabaseService
from app.services.ocr_service import OCRService
from app.utils.command_protection import private_chat_only, private_chat_only_callback

logger = logging.getLogger(__name__)


class UserHandlers:
    """Handle user interactions for currency exchange"""
    
    def __init__(self, db_service: DatabaseService, ocr_service: OCRService):
        """
        Initialize user handlers
        
        Args:
            db_service: Database service instance
            ocr_service: OCR service instance
        """
        self.db = db_service
        self.ocr = ocr_service
        self.config = Config
        logger.info("User handlers initialized")
    
    @private_chat_only
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        rate = self.db.get_current_rate()
        
        # Get THB admin accounts from database
        thb_accounts = self.db.get_admin_bank_accounts('THB')
        
        # Build receiving accounts section
        receiving_accounts = "💳 **Our Receiving Accounts:**\n"
        if thb_accounts:
            for acc_id, currency, bank_name, account_number, account_name, is_active in thb_accounts:
                receiving_accounts += f"• **{bank_name}**\n"
                receiving_accounts += f"  Account: `{account_number}`\n"
                receiving_accounts += f"  Name: {account_name}\n\n"
        else:
            receiving_accounts += "📌 Please contact admin for account details\n\n"
        
        welcome_message = f"""💱 **Welcome to Currency Exchange Service**

Exchange Thai Baht (THB) to Myanmar Kyat (MMK) easily and securely.

📊 **Current Exchange Rate:** 
1 THB = {rate} MMK

{receiving_accounts}⚠️ **Important:**
• Make sure your transfer is successful
• Keep your receipt screenshot ready
• Double-check bank account details
• Transfer to one of our official accounts above

Ready to exchange? Click the button below!
"""
        
        keyboard = [[InlineKeyboardButton("💱 Exchange THB → MMK", callback_data="start_exchange")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')
    
    @private_chat_only_callback
    async def start_exchange_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle exchange button click"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            "📸 **Step 1: Upload Payment Receipt**\n\n"
            "Please upload your payment receipt screenshot from your Thai bank.\n\n"
            "✅ Make sure the receipt shows:\n"
            "• Transfer amount\n"
            "• Bank names (sender and receiver)\n"
            "• Transaction status (successful)\n"
            "• Date and reference number\n\n"
            "📷 Send a clear screenshot now:",
            parse_mode='Markdown'
        )
        
        return self.config.UPLOAD_RECEIPT
    
    @private_chat_only
    async def handle_receipt(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle receipt image upload"""
        photo = update.message.photo[-1]
        
        # Download photo with retry logic for network timeouts
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                file = await context.bot.get_file(photo.file_id)
                file_path = f"{self.config.RECEIPTS_DIR}/{update.message.from_user.id}_{datetime.now().timestamp()}.jpg"
                await file.download_to_drive(file_path)
                break
            except (TimedOut, NetworkError) as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Network timeout on attempt {attempt + 1}, retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Failed to download receipt after {max_retries} attempts: {e}")
                    await update.message.reply_text(
                        "❌ **Network Error**\n\n"
                        "Unable to download your receipt due to network issues.\n\n"
                        "Please try again in a moment. If the problem persists, "
                        "try sending a smaller image or contact support."
                    )
                    return self.config.UPLOAD_RECEIPT
        
        # Store file path in context
        context.user_data['receipt_path'] = file_path
        
        processing_msg = await update.message.reply_text("🔍 Processing your receipt... Please wait.")
        
        # Extract receipt info using Mistral AI
        receipt_info = self.ocr.extract_receipt_info(file_path)
        
        if not receipt_info:
            await self._send_message_with_retry(
                processing_msg.edit_text,
                "❌ Unable to read your receipt clearly.\n\n"
                "Please send a clearer screenshot with all details visible."
            )
            return self.config.UPLOAD_RECEIPT
        
        context.user_data['receipt_info'] = receipt_info
        
        # Validate receipt status
        if receipt_info.get('status') and 'success' not in receipt_info['status'].lower():
            await self._send_message_with_retry(
                processing_msg.edit_text,
                "⚠️ Your transaction doesn't appear to be successful.\n\n"
                "Please check your transaction status and resend a successful receipt."
            )
            return self.config.UPLOAD_RECEIPT
        
        # Validate receiver account name AND bank
        receiver_name = receipt_info.get('receiver_name')
        receiver_bank = receipt_info.get('receiver_bank')
        
        if receiver_name:
            admin_account = self.db.validate_receiver_account(receiver_name, receiver_bank, 'THB')
            if not admin_account:
                error_msg = f"❌ **Invalid Receiver Account**\n\n"
                if receiver_bank:
                    error_msg += f"Receiver: '{receiver_name}'\nBank: '{receiver_bank}'\n\n"
                else:
                    error_msg += f"Receiver: '{receiver_name}'\n\n"
                error_msg += "This doesn't match our official accounts.\n\n"
                error_msg += "Please make sure you transferred to one of our official bank accounts.\n"
                error_msg += "Contact admin if you need the correct account details."
                
                await self._send_message_with_retry(processing_msg.edit_text, error_msg)
                return self.config.UPLOAD_RECEIPT
            
            # Store validated admin bank info
            context.user_data['admin_thb_bank'] = admin_account[1]  # bank_name
            context.user_data['admin_account_validated'] = True
            logger.info(f"Receipt validated: {receiver_name} at {admin_account[1]}")
        
        # Check if amount is detected
        if receipt_info.get('amount'):
            context.user_data['thb_amount'] = float(receipt_info['amount'])
            rate = self.db.get_current_rate()
            mmk_amount = float(receipt_info['amount']) * rate
            
            success_message = (
                f"✅ **Receipt Processed Successfully!**\n\n"
                f"💰 Amount detected: **{receipt_info['amount']} THB**\n"
                f"📊 You will receive: **{mmk_amount:,.0f} MMK**\n"
                f"📈 Rate: 1 THB = {rate} MMK\n\n"
                f"📝 **Step 2: Enter Your MMK Bank Details**\n\n"
                f"Please provide your receiving account information:\n\n"
                f"**Format:**\n"
                f"`Bank Name | Account Number | Account Name`\n\n"
                f"**Example:**\n"
                f"`AYA | 00987654321 | AUNG AUNG`\n\n"
                f"**Supported Banks:** KBZ, AYA, CB Bank, KPay, Wave Money"
            )
            
            # Try to edit message with retry logic
            await self._send_message_with_retry(
                processing_msg.edit_text,
                success_message,
                parse_mode='Markdown'
            )
            return self.config.ENTER_BANK_INFO
        else:
            amount_message = (
                "✅ Receipt uploaded successfully!\n\n"
                "💰 Please enter the amount in THB you have transferred:\n\n"
                "Example: 1000"
            )
            
            # Try to edit message with retry logic
            await self._send_message_with_retry(
                processing_msg.edit_text,
                amount_message
            )
            return self.config.ENTER_AMOUNT
    
    @private_chat_only
    async def handle_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle manual amount entry"""
        try:
            amount = float(update.message.text.replace(',', ''))
            if amount <= 0:
                raise ValueError("Amount must be positive")
                
            context.user_data['thb_amount'] = amount
            rate = self.db.get_current_rate()
            mmk_amount = amount * rate
            
            await update.message.reply_text(
                f"✅ **Amount Confirmed**\n\n"
                f"💰 Amount: **{amount} THB**\n"
                f"📊 You will receive: **{mmk_amount:,.0f} MMK**\n"
                f"📈 Rate: 1 THB = {rate} MMK\n\n"
                f"📝 **Step 2: Enter Your MMK Bank Details**\n\n"
                f"Please provide your receiving account information:\n\n"
                f"**Format:**\n"
                f"`Bank Name | Account Number | Account Name`\n\n"
                f"**Example:**\n"
                f"`AYA | 00987654321 | AUNG AUNG`",
                parse_mode='Markdown'
            )
            return self.config.ENTER_BANK_INFO
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid amount. Please enter a valid number:\n\n"
                "Example: 1000"
            )
            return self.config.ENTER_AMOUNT
    
    @private_chat_only
    async def handle_bank_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle MMK bank information"""
        bank_info = update.message.text.split('|')
        
        if len(bank_info) != 3:
            await update.message.reply_text(
                "❌ Invalid format.\n\n"
                "Please use this format:\n"
                "`Bank Name | Account Number | Account Name`\n\n"
                "Example:\n"
                "`AYA | 00987654321 | AUNG AUNG`",
                parse_mode='Markdown'
            )
            return self.config.ENTER_BANK_INFO
        
        bank_name = bank_info[0].strip()
        account_number = bank_info[1].strip()
        account_name = bank_info[2].strip()
        
        # Validate bank name
        if not any(bank.lower() in bank_name.lower() for bank in self.config.MMK_BANKS):
            await update.message.reply_text(
                f"⚠️ Please use one of the supported banks:\n\n"
                f"• KBZ Bank\n• AYA Bank\n• CB Bank\n• KPay\n• Wave Money\n\n"
                f"Please resend in correct format."
            )
            return self.config.ENTER_BANK_INFO
        
        context.user_data['mmk_bank_name'] = bank_name
        context.user_data['mmk_account_number'] = account_number
        context.user_data['mmk_account_name'] = account_name
        
        # Calculate MMK amount
        thb_amount = context.user_data['thb_amount']
        rate = self.db.get_current_rate()
        mmk_amount = thb_amount * rate
        
        # Get sender bank from receipt
        receipt_info = context.user_data.get('receipt_info', {})
        from_bank = receipt_info.get('sender_bank', 'Unknown')
        
        # Get admin THB bank from validated receipt
        admin_thb_bank = context.user_data.get('admin_thb_bank', receipt_info.get('receiver_bank', 'KBank'))
        
        # Create transaction with admin_thb_bank
        transaction_id = self.db.create_transaction(
            user_id=update.message.from_user.id,
            username=update.message.from_user.username,
            thb_amount=thb_amount,
            mmk_amount=mmk_amount,
            rate=rate,
            user_bank_name=bank_name,
            user_account_number=account_number,
            user_account_name=account_name,
            from_bank=from_bank,
            receipt_path=context.user_data.get('receipt_path'),
            admin_thb_bank=admin_thb_bank
        )
        
        # Update THB balance - add to admin account
        self.db.update_balance('THB', admin_thb_bank, thb_amount)
        
        # Notify admin
        await self._notify_admin(context, transaction_id, update.message.from_user, 
                                thb_amount, mmk_amount, rate, bank_name, 
                                account_number, account_name, from_bank)
        
        await update.message.reply_text(
            f"✅ **Request Submitted Successfully!**\n\n"
            f"📋 **Transaction ID:** #{transaction_id}\n\n"
            f"💰 **Amount:** {thb_amount} THB → {mmk_amount:,.0f} MMK\n"
            f"📈 **Rate:** {rate}\n"
            f"🏦 **Your Bank:** {bank_name}\n\n"
            f"⏳ Our team is processing your request.\n"
            f"You will receive a confirmation once the transfer is complete.\n\n"
            f"Thank you for using our service! 💚",
            parse_mode='Markdown'
        )
        
        # Clear user data
        context.user_data.clear()
        
        return ConversationHandler.END
    
    async def _send_message_with_retry(self, send_func, *args, **kwargs):
        """
        Send or edit a message with retry logic for network timeouts
        
        Args:
            send_func: The function to call (e.g., message.edit_text, message.reply_text)
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
        """
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                return await send_func(*args, **kwargs)
            except (TimedOut, NetworkError) as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Network timeout on attempt {attempt + 1}, retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Failed to send message after {max_retries} attempts: {e}")
                    # Don't raise, just log - the user will see the previous message
                    return None
    
    async def _notify_admin(self, context, transaction_id, user, thb_amount, 
                           mmk_amount, rate, bank_name, account_number, 
                           account_name, from_bank):
        """Notify admin group about new transaction"""
        admin_message = f"""Buy {thb_amount} × {rate} = **{mmk_amount:,.0f}**

👤 **User:** @{user.username or user.first_name} (ID: {user.id})

🏦 **User's MMK Bank:**
Bank: {bank_name}
Account: {account_number}
Name: {account_name}

📤 **From Bank:** {from_bank}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📸 **Please reply to this message with your transfer receipt**
"""
        
        keyboard = [
            [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{transaction_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            # Get admin group and topic from database
            admin_group_id = self.db.get_setting('admin_group_id') or self.config.ADMIN_GROUP_ID
            admin_topic_id = self.db.get_setting('admin_topic_id') or self.config.ADMIN_TOPIC_ID
            
            if admin_topic_id:
                await self._send_message_with_retry(
                    context.bot.send_message,
                    chat_id=admin_group_id,
                    text=admin_message,
                    message_thread_id=int(admin_topic_id),
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                await self._send_message_with_retry(
                    context.bot.send_message,
                    chat_id=admin_group_id,
                    text=admin_message,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Error sending to admin: {e}")
    
    @private_chat_only
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel the conversation"""
        await update.message.reply_text(
            "❌ Operation cancelled.\n\n"
            "Use /start to begin again."
        )
        context.user_data.clear()
        return ConversationHandler.END

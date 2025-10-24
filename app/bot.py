"""
Main bot application
"""
import logging
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters
)

from app.config.settings import Config
from app.services.database_service import DatabaseService
from app.services.ocr_service import OCRService
from app.handlers.user_handlers import UserHandlers
from app.handlers.admin_handlers import AdminHandlers

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class ExchangeBot:
    """Main bot application class"""
    
    def __init__(self):
        """Initialize the bot"""
        logger.info("Initializing Exchange Bot...")
        
        # Validate configuration
        try:
            Config.validate()
            Config.create_directories()
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            raise
        
        # Initialize services
        self.db_service = DatabaseService(Config.DATABASE_PATH)
        self.db_service.initialize_balances(Config.INITIAL_BALANCES)
        self.db_service.initialize_exchange_rate(Config.DEFAULT_EXCHANGE_RATE)
        
        self.ocr_service = OCRService(Config.MISTRAL_API_KEY)
        
        # Initialize handlers
        self.user_handlers = UserHandlers(self.db_service, self.ocr_service)
        self.admin_handlers = AdminHandlers(self.db_service, self.ocr_service)
        
        # Create application with increased timeout settings
        self.application = (
            Application.builder()
            .token(Config.TELEGRAM_BOT_TOKEN)
            .connect_timeout(30.0)  # Connection timeout: 30 seconds
            .read_timeout(30.0)     # Read timeout: 30 seconds
            .write_timeout(30.0)    # Write timeout: 30 seconds
            .pool_timeout(30.0)     # Pool timeout: 30 seconds
            .build()
        )
        
        # Register handlers
        self._register_handlers()
        
        logger.info("Exchange Bot initialized successfully!")
    
    def _register_handlers(self):
        """Register all bot handlers"""
        
        # Conversation handler for exchange flow
        conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(
                    self.user_handlers.start_exchange_callback, 
                    pattern="^start_exchange$"
                )
            ],
            states={
                Config.UPLOAD_RECEIPT: [
                    MessageHandler(filters.PHOTO, self.user_handlers.handle_receipt)
                ],
                Config.ENTER_AMOUNT: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, 
                        self.user_handlers.handle_amount
                    )
                ],
                Config.ENTER_BANK_INFO: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, 
                        self.user_handlers.handle_bank_info
                    )
                ],
            },
            fallbacks=[CommandHandler("cancel", self.user_handlers.cancel)],
        )
        
        # User commands
        self.application.add_handler(CommandHandler("start", self.user_handlers.start))
        self.application.add_handler(conv_handler)
        
        # Admin commands
        self.application.add_handler(CommandHandler("balance", self.admin_handlers.balance_command))
        self.application.add_handler(CommandHandler("rate", self.admin_handlers.rate_command))
        self.application.add_handler(CommandHandler("transactions", self.admin_handlers.transactions_command))
        self.application.add_handler(CommandHandler("settings", self.admin_handlers.settings_command))
        self.application.add_handler(CommandHandler("addbank", self.admin_handlers.add_bank_command))
        self.application.add_handler(CommandHandler("listbanks", self.admin_handlers.list_banks_command))
        self.application.add_handler(CommandHandler("removebank", self.admin_handlers.remove_bank_command))
        self.application.add_handler(CommandHandler("adjust", self.admin_handlers.adjust_balance_command))
        self.application.add_handler(CommandHandler("initbalance", self.admin_handlers.init_balance_command))
        
        # Admin photo handler for receipts (must be before callback handlers)
        self.application.add_handler(
            MessageHandler(filters.PHOTO & filters.REPLY, self.admin_handlers.handle_admin_receipt)
        )
        
        # Admin callback handlers
        self.application.add_handler(
            CallbackQueryHandler(self.admin_handlers.admin_bank_selection_callback, pattern="^bank_")
        )
        self.application.add_handler(
            CallbackQueryHandler(self.admin_handlers.admin_cancel_callback, pattern="^cancel_")
        )
        
        logger.info("All handlers registered successfully")
    
    def run(self):
        """Start the bot"""
        logger.info("Starting bot polling...")
        logger.info(f"Admin Group ID: {Config.ADMIN_GROUP_ID}")
        self.application.run_polling(allowed_updates=["message", "callback_query"])

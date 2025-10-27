"""
Configuration management for the Telegram Exchange Bot
"""
import os
from typing import List, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Bot configuration"""
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    ADMIN_GROUP_ID: str = os.getenv("ADMIN_GROUP_ID", "")
    ADMIN_TOPIC_ID: str = os.getenv("ADMIN_TOPIC_ID", "")
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Database Configuration
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "exchange_bot.db")
    
    # Supported Banks
    THAI_BANKS: List[str] = ["KBank", "SCB", "KTB", "Bangkok Bank", "Kasikorn", "Siam Commercial"]
    COMPANY_RECEIVING_BANKS: List[str] = ["KBank", "SCB"]
    MMK_BANKS: List[str] = ["KBZ", "AYA", "CB Bank", "KPay", "Wave Money"]
    
    # Initial Balances - Matching Admin Bank Accounts
    INITIAL_BALANCES: List[Tuple[str, str, float]] = [
        # THB Admin Banks
        ('THB', 'KrungthaiBank', 150000),
        ('THB', 'PromptPay', 150000),
        ('THB', 'SiamCommercialBank', 150000),
        # MMK Admin Banks
        ('MMK', 'KBZ', 1500000),
        ('MMK', 'AYA', 1500000),
        ('MMK', 'KPay', 1500000),
        ('MMK', 'Wave', 1500000),
        # USDT
        ('USDT', 'Binance', 1500)
    ]
    
    # Default Exchange Rate
    DEFAULT_EXCHANGE_RATE: float = 121.5
    
    # File Paths
    RECEIPTS_DIR: str = "receipts"
    ADMIN_RECEIPTS_DIR: str = "admin_receipts"
    
    # Conversation States
    UPLOAD_RECEIPT: int = 0
    ENTER_AMOUNT: int = 1
    ENTER_BANK_INFO: int = 2
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        errors = []
        
        if not cls.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is not set in .env file")
        
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is not set in .env file")
        
        if not cls.ADMIN_GROUP_ID:
            errors.append("ADMIN_GROUP_ID is not set in .env file")
        
        if errors:
            error_msg = "Configuration errors:\n" + "\n".join(f"- {e}" for e in errors)
            raise ValueError(error_msg)
        
        return True
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories"""
        os.makedirs(cls.RECEIPTS_DIR, exist_ok=True)
        os.makedirs(cls.ADMIN_RECEIPTS_DIR, exist_ok=True)

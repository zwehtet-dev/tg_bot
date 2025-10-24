"""
Main entry point for the Telegram Exchange Bot
"""
import sys
import logging

logger = logging.getLogger(__name__)


def main():
    """Main function to start the bot"""
    try:
        from app.bot import ExchangeBot
        
        # Create and run bot
        bot = ExchangeBot()
        bot.run()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

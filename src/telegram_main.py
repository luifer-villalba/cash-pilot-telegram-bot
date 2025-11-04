"""
CashPilot Telegram Bot entrypoint.

Connects to Telegram API and CashPilot backend API.
"""

import logging
import os

from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Start the Telegram bot."""
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    api_url = os.getenv("CASHPILOT_API_URL")

    if not telegram_token:
        raise ValueError("TELEGRAM_TOKEN not set in .env")
    if not api_url:
        raise ValueError("CASHPILOT_API_URL not set in .env")

    logger.info("🤖 Starting CashPilot Telegram Bot...")
    logger.info(f"📡 API URL: {api_url}")

    # Create application
    app = Application.builder().token(telegram_token).build()

    # Import handlers
    from src.telegram_bot.bot import (
        start_handler,
        help_handler,
        mi_farmacia_handler,
        error_handler,
    )

    # Register handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("mi_farmacia", mi_farmacia_handler))

    # Error handler
    app.add_error_handler(error_handler)

    logger.info("✅ Bot handlers registered")

    # Start polling (blocking call)
    logger.info("🚀 Bot running (polling mode)...")
    app.run_polling()


if __name__ == "__main__":
    main()

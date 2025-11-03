"""
CashPilot Telegram Bot entrypoint.

Connects to Telegram API and CashPilot backend API.
"""

import logging
import os

from dotenv import load_dotenv

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

    logger.info("Starting CashPilot Telegram Bot...")
    logger.info(f"API URL: {api_url}")
    # Bot logic will go here
    logger.info("Bot running...")


if __name__ == "__main__":
    main()

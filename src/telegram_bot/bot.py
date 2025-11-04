"""Telegram bot handlers and state management."""

import logging
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class UserState:
    """In-memory user state (MVP only, use DB in production)."""

    def __init__(self):
        self.users: dict[int, dict] = {}

    def register_user(self, user_id: int, business_id: str, business_name: str) -> None:
        """Register user with their business."""
        self.users[user_id] = {
            "business_id": business_id,
            "business_name": business_name,
            "open_session": None,
        }
        logger.info(f"Registered user {user_id} with business {business_id}")

    def get_user(self, user_id: int) -> Optional[dict]:
        """Get user info."""
        return self.users.get(user_id)

    def set_open_session(self, user_id: int, session_id: str) -> None:
        """Mark session as open for user."""
        if user_id in self.users:
            self.users[user_id]["open_session"] = session_id

    def clear_open_session(self, user_id: int) -> None:
        """Clear open session for user."""
        if user_id in self.users:
            self.users[user_id]["open_session"] = None


# Global state (MVP only)
user_state = UserState()


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command - register user."""
    from src.telegram_bot.messages import START_MESSAGE

    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    business_id = "550e8400-e29b-41d4-a716-446655440000"
    business_name = "Farmacia Central"

    user_state.register_user(user_id, business_id, business_name)

    await update.message.reply_text(START_MESSAGE, entities=[])
    logger.info(f"User {user_name} (ID: {user_id}) started the bot")


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command - show available commands."""
    from src.telegram_bot.messages import HELP_MESSAGE

    await update.message.reply_text(HELP_MESSAGE, entities=[])


async def mi_farmacia_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /mi_farmacia command - show business info."""
    from src.telegram_bot.messages import BUSINESS_INFO_MESSAGE, NO_BUSINESS_MESSAGE

    user_id = update.effective_user.id
    user = user_state.get_user(user_id)

    if not user:
        await update.message.reply_text(NO_BUSINESS_MESSAGE, entities=[])
        return

    status = "Activa"
    message = BUSINESS_INFO_MESSAGE.format(
        name="Farmacia Central",
        address="Av. Mariscal Lopez 1234, Asuncion",
        phone="+595 21 123-4567",
        status=status,
    )

    await update.message.reply_text(message, entities=[])


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors."""
    from src.telegram_bot.messages import ERROR_MESSAGE

    logger.error(f"Update {update} caused error {context.error}")

    if update and update.effective_message:
        await update.effective_message.reply_text(
            ERROR_MESSAGE.format(error="Internal error occurred. Try again later."),
            entities=[],
        )

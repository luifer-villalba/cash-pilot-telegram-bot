"""Tests for Telegram bot handlers."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram import Update, User, Chat, Message
from telegram.ext import ContextTypes

from src.telegram_bot.bot import (
    start_handler,
    help_handler,
    mi_farmacia_handler,
    user_state,
)


@pytest.fixture
def mock_update():
    """Create a mock Telegram Update."""
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 12345
    update.effective_user.first_name = "Test User"
    update.message = AsyncMock(spec=Message)
    return update


@pytest.fixture
def mock_context():
    """Create a mock Telegram Context."""
    return MagicMock(spec=ContextTypes.DEFAULT_TYPE)


class TestStartHandler:
    """Test /start command handler."""

    @pytest.mark.asyncio
    async def test_start_registers_user(self, mock_update, mock_context):
        """Test /start registers user with business."""
        # Reset state
        user_state.users.clear()

        await start_handler(mock_update, mock_context)

        # Verify user was registered
        user = user_state.get_user(12345)
        assert user is not None
        assert user["business_name"] == "Farmacia Central"

    @pytest.mark.asyncio
    async def test_start_sends_welcome_message(self, mock_update, mock_context):
        """Test /start sends welcome message."""
        await start_handler(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "CashPilot" in call_args[0][0]


class TestHelpHandler:
    """Test /help command handler."""

    @pytest.mark.asyncio
    async def test_help_shows_commands(self, mock_update, mock_context):
        """Test /help returns command list."""
        await help_handler(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        message = call_args[0][0]
        assert "/start" in message
        assert "/help" in message
        assert "/mi_farmacia" in message


class TestMiFarmaciaHandler:
    """Test /mi_farmacia command handler."""

    @pytest.mark.asyncio
    async def test_mi_farmacia_shows_business_info(self, mock_update, mock_context):
        """Test /mi_farmacia shows registered business."""
        # Register user first
        user_state.users.clear()
        user_state.register_user(12345, "test-id", "Farmacia Central")

        await mi_farmacia_handler(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        message = call_args[0][0]
        assert "Farmacia Central" in message
        assert "Av. Mariscal Lopez" in message

    @pytest.mark.asyncio
    async def test_mi_farmacia_unregistered_user(self, mock_update, mock_context):
        """Test /mi_farmacia for unregistered user."""
        user_state.users.clear()

        await mi_farmacia_handler(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        message = call_args[0][0]
        assert "no tienes una farmacia" in message.lower() or "no farmacia" in message.lower()


class TestUserState:
    """Test user state management."""

    def test_register_user(self):
        """Test registering a user."""
        user_state.users.clear()
        user_state.register_user(123, "biz-id", "Test Biz")

        user = user_state.get_user(123)
        assert user is not None
        assert user["business_id"] == "biz-id"
        assert user["business_name"] == "Test Biz"

    def test_set_open_session(self):
        """Test setting open session."""
        user_state.users.clear()
        user_state.register_user(123, "biz-id", "Test Biz")
        user_state.set_open_session(123, "session-id")

        user = user_state.get_user(123)
        assert user["open_session"] == "session-id"

    def test_clear_open_session(self):
        """Test clearing open session."""
        user_state.users.clear()
        user_state.register_user(123, "biz-id", "Test Biz")
        user_state.set_open_session(123, "session-id")
        user_state.clear_open_session(123)

        user = user_state.get_user(123)
        assert user["open_session"] is None

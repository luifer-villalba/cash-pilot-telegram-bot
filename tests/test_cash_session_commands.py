"""
Integration tests for cash session bot commands.

Tests /abrir_caja and /cerrar_caja with mocked CashPilot API.
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from telegram import Update, User, Chat, Message
from telegram.ext import ContextTypes

from src.cashpilot_client import CashPilotClient, CashPilotAPIError
from src.handlers.cash_session import CashSessionManager


class TestCashSessionHandlers:
    """Test suite for cash session handlers."""

    @pytest.fixture
    def mock_client(self):
        """Create mock CashPilot client."""
        client = AsyncMock(spec=CashPilotClient)
        return client

    @pytest.fixture
    def session_manager(self, mock_client):
        """Create session manager with mock client."""
        return CashSessionManager(mock_client)

    @pytest.fixture
    def mock_update(self):
        """Create mock Telegram update."""
        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(spec=User)
        update.effective_user.id = 123456789
        update.effective_user.first_name = "María"
        update.effective_chat = MagicMock(spec=Chat)
        update.effective_chat.id = 123456789
        update.message = MagicMock(spec=Message)
        return update

    @pytest.fixture
    def mock_context(self):
        """Create mock Telegram context."""
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.bot = AsyncMock()
        context.user_data = {}
        context.user_data["business_id"] = "biz-uuid-123"
        return context

    @pytest.mark.asyncio
    async def test_open_session_success(self, session_manager, mock_client, mock_update, mock_context):
        """Test successful cash session opening."""
        # Setup
        mock_context.args = ["500000"]
        mock_client.open_cash_session.return_value = {
            "id": "session-uuid-123",
            "business_id": "biz-uuid-123",
            "status": "OPEN",
            "cashier_name": "María",
            "initial_cash": "500000.00",
            "opened_at": "2025-11-03T08:00:00",
        }

        # Execute
        await session_manager.handle_open_session(mock_update, mock_context)

        # Assert
        mock_client.open_cash_session.assert_called_once_with(
            business_id="biz-uuid-123",
            cashier_name="María",
            initial_cash=Decimal("500000"),
            shift_hours=None,
        )
        mock_context.bot.send_message.assert_called_once()
        call_args = mock_context.bot.send_message.call_args
        assert "✅" in call_args.kwargs["text"]
        assert "session-uuid-123" in call_args.kwargs["text"]
        assert mock_context.user_data["current_session_id"] == "session-uuid-123"

    @pytest.mark.asyncio
    async def test_open_session_with_shift_hours(
        self, session_manager, mock_client, mock_update, mock_context
    ):
        """Test opening session with shift hours."""
        mock_context.args = ["500000", "08:00-16:00"]
        mock_client.open_cash_session.return_value = {
            "id": "session-uuid-123",
            "status": "OPEN",
            "initial_cash": "500000.00",
            "opened_at": "2025-11-03T08:00:00",
        }

        await session_manager.handle_open_session(mock_update, mock_context)

        mock_client.open_cash_session.assert_called_once_with(
            business_id="biz-uuid-123",
            cashier_name="María",
            initial_cash=Decimal("500000"),
            shift_hours="08:00-16:00",
        )

    @pytest.mark.asyncio
    async def test_open_session_invalid_amount(self, session_manager, mock_context, mock_update):
        """Test opening session with invalid amount."""
        mock_context.args = ["invalid"]

        await session_manager.handle_open_session(mock_update, mock_context)

        mock_context.bot.send_message.assert_called_once()
        call_args = mock_context.bot.send_message.call_args
        assert "❌" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_open_session_negative_amount(self, session_manager, mock_context, mock_update):
        """Test opening session with negative amount."""
        mock_context.args = ["-500000"]

        await session_manager.handle_open_session(mock_update, mock_context)

        mock_context.bot.send_message.assert_called_once()
        call_args = mock_context.bot.send_message.call_args
        assert "❌" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_open_session_no_args(self, session_manager, mock_context, mock_update):
        """Test opening session without arguments."""
        mock_context.args = []

        await session_manager.handle_open_session(mock_update, mock_context)

        mock_context.bot.send_message.assert_called_once()
        call_args = mock_context.bot.send_message.call_args
        assert "❌" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_open_session_conflict_error(
        self, session_manager, mock_client, mock_update, mock_context
    ):
        """Test opening session when one already exists (409 Conflict)."""
        mock_context.args = ["500000"]
        mock_client.open_cash_session.side_effect = CashPilotAPIError(
            status=409,
            message="Session already open for this business",
            code="CONFLICT",
        )

        await session_manager.handle_open_session(mock_update, mock_context)

        mock_context.bot.send_message.assert_called_once()
        call_args = mock_context.bot.send_message.call_args
        assert "⚠️" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_close_session_success(
        self, session_manager, mock_client, mock_update, mock_context
    ):
        """Test successful cash session closing."""
        mock_context.args = ["1200000", "300000"]
        mock_context.user_data["current_session_id"] = "session-uuid-123"
        mock_client.close_cash_session.return_value = {
            "id": "session-uuid-123",
            "status": "CLOSED",
            "final_cash": "1200000.00",
            "envelope_amount": "300000.00",
            "closed_at": "2025-11-03T16:00:00",
            "cash_sales": "1000000.00",
            "total_sales": "1000000.00",
            "difference": "0.00",
        }

        await session_manager.handle_close_session(mock_update, mock_context)

        mock_client.close_cash_session.assert_called_once_with(
            session_id="session-uuid-123",
            final_cash=Decimal("1200000"),
            envelope_amount=Decimal("300000"),
        )
        mock_context.bot.send_message.assert_called_once()
        call_args = mock_context.bot.send_message.call_args
        assert "✅" in call_args.kwargs["text"]
        assert "Cuadre perfecto" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_close_session_with_shortage(
        self, session_manager, mock_client, mock_update, mock_context
    ):
        """Test closing session with shortage detected."""
        mock_context.args = ["1000000", "300000"]
        mock_context.user_data["current_session_id"] = "session-uuid-123"
        mock_client.close_cash_session.return_value = {
            "id": "session-uuid-123",
            "status": "CLOSED",
            "final_cash": "1000000.00",
            "envelope_amount": "300000.00",
            "closed_at": "2025-11-03T16:00:00",
            "cash_sales": "800000.00",
            "total_sales": "1500000.00",
            "difference": "700000.00",  # Shortage
        }

        await session_manager.handle_close_session(mock_update, mock_context)

        call_args = mock_context.bot.send_message.call_args
        assert "⚠️" in call_args.kwargs["text"]
        assert "Faltante" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_close_session_with_overage(
        self, session_manager, mock_client, mock_update, mock_context
    ):
        """Test closing session with overage detected."""
        mock_context.args = ["1400000", "300000"]
        mock_context.user_data["current_session_id"] = "session-uuid-123"
        mock_client.close_cash_session.return_value = {
            "id": "session-uuid-123",
            "status": "CLOSED",
            "final_cash": "1400000.00",
            "envelope_amount": "300000.00",
            "closed_at": "2025-11-03T16:00:00",
            "cash_sales": "1200000.00",
            "total_sales": "1200000.00",
            "difference": "-500000.00",  # Overage
        }

        await session_manager.handle_close_session(mock_update, mock_context)

        call_args = mock_context.bot.send_message.call_args
        assert "📦" in call_args.kwargs["text"]
        assert "Sobrante" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_close_session_no_open_session(
        self, session_manager, mock_context, mock_update
    ):
        """Test closing when no session is open."""
        mock_context.args = ["1200000", "300000"]
        mock_context.user_data = {}  # No session ID

        await session_manager.handle_close_session(mock_update, mock_context)

        mock_context.bot.send_message.assert_called_once()
        call_args = mock_context.bot.send_message.call_args
        assert "❌" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_close_session_invalid_args(
        self, session_manager, mock_context, mock_update
    ):
        """Test closing with invalid arguments."""
        mock_context.args = ["invalid", "300000"]
        mock_context.user_data["current_session_id"] = "session-uuid-123"

        await session_manager.handle_close_session(mock_update, mock_context)

        mock_context.bot.send_message.assert_called_once()
        call_args = mock_context.bot.send_message.call_args
        assert "❌" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_close_session_not_found(
        self, session_manager, mock_client, mock_update, mock_context
    ):
        """Test closing non-existent session (404)."""
        mock_context.args = ["1200000", "300000"]
        mock_context.user_data["current_session_id"] = "invalid-session-id"
        mock_client.close_cash_session.side_effect = CashPilotAPIError(
            status=404,
            message="CashSession not found",
            code="NOT_FOUND",
        )

        await session_manager.handle_close_session(mock_update, mock_context)

        mock_context.bot.send_message.assert_called_once()
        call_args = mock_context.bot.send_message.call_args
        assert "❌" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_status_open_session(
        self, session_manager, mock_client, mock_update, mock_context
    ):
        """Test status command with open session."""
        mock_context.user_data["current_session_id"] = "session-uuid-123"
        mock_client.get_session.return_value = {
            "id": "session-uuid-123",
            "status": "OPEN",
            "initial_cash": "500000.00",
            "opened_at": "2025-11-03T08:00:00",
        }

        await session_manager.handle_status(mock_update, mock_context)

        mock_context.bot.send_message.assert_called_once()
        call_args = mock_context.bot.send_message.call_args
        assert "ABIERTA" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_status_closed_session(
        self, session_manager, mock_client, mock_update, mock_context
    ):
        """Test status command with closed session."""
        mock_context.user_data["current_session_id"] = "session-uuid-123"
        mock_client.get_session.return_value = {
            "id": "session-uuid-123",
            "status": "CLOSED",
            "initial_cash": "500000.00",
            "final_cash": "1200000.00",
            "opened_at": "2025-11-03T08:00:00",
            "closed_at": "2025-11-03T16:00:00",
        }

        await session_manager.handle_status(mock_update, mock_context)

        mock_context.bot.send_message.assert_called_once()
        call_args = mock_context.bot.send_message.call_args
        assert "CERRADA" in call_args.kwargs["text"]

    def test_format_currency(self, session_manager):
        """Test currency formatting."""
        assert session_manager._format_currency(Decimal("500000")) == "500.000 Gs"
        assert session_manager._format_currency(Decimal("1200000")) == "1.200.000 Gs"
        assert session_manager._format_currency(Decimal("150")) == "150 Gs"
        assert session_manager._format_currency(Decimal("1000000.50")) == "1.000.000.50 Gs"

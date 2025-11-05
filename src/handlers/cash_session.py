"""
Cash session command handlers for Telegram bot.

Handles /abrir_caja and /cerrar_caja commands.
"""

import logging
from decimal import Decimal
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from src.cashpilot_client import CashPilotClient, CashPilotAPIError

logger = logging.getLogger(__name__)


class CashSessionManager:
    """Manager for cash session operations via bot."""

    def __init__(self, client: CashPilotClient):
        self.client = client

    def _format_currency(self, amount: Decimal) -> str:
        """
        Format currency for display.

        Args:
            amount: Amount in Gs

        Returns:
            Formatted string (e.g., "1.500.000 Gs")
        """
        # Convert to int if whole number
        if amount == int(amount):
            amount_int = int(amount)
        else:
            amount_int = amount

        # Add thousands separator
        formatted = f"{amount_int:,}".replace(",", ".")
        return f"{formatted} Gs"

    async def handle_open_session(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /abrir_caja command.

        Usage: /abrir_caja <initial_cash_gs> [shift_hours]
        Example: /abrir_caja 500000
                 /abrir_caja 500000 08:00-16:00

        Args:
            update: Telegram update
            context: Telegram context
        """
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        try:
            # Parse arguments
            if not context.args or len(context.args) < 1:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ *Uso incorrecto*\n\n"
                    "/abrir_caja <monto_inicial>\n\n"
                    "Ejemplo: `/abrir_caja 500000`",
                    parse_mode="Markdown",
                )
                return

            try:
                initial_cash = Decimal(context.args[0])
            except ValueError:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ El monto debe ser un número válido.\n\n"
                    "Ejemplo: `/abrir_caja 500000`",
                    parse_mode="Markdown",
                )
                return

            if initial_cash <= 0:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ El monto inicial debe ser mayor a 0.",
                )
                return

            shift_hours = context.args[1] if len(context.args) > 1 else None

            # TODO: Get business_id from user context (store in user_data or DB)
            # For now, using a placeholder - in production, query from DB
            business_id = context.user_data.get("business_id") or "375bfd5c-4c96-48a1-aef8-f6b7e61b4eeb"

            if not business_id:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ Debes configurar tu sucursal primero.\n\n"
                    "Usa: `/configurar_sucursal <id_sucursal>`",
                    parse_mode="Markdown",
                )
                return

            # Call API
            logger.info(f"User {user_id} opening cash session with {initial_cash} Gs")

            response = await self.client.open_cash_session(
                business_id=business_id,
                cashier_name=update.effective_user.first_name or "Unknown",
                initial_cash=initial_cash,
                shift_hours=shift_hours,
            )

            session_id = response["id"]
            opened_at = response["opened_at"]

            # Store session ID in context for later use
            context.user_data["current_session_id"] = session_id

            # Format response
            message = (
                "✅ *Caja abierta*\n\n"
                f"🆔 ID: `{session_id}`\n"
                f"💰 Monto inicial: {self._format_currency(Decimal(response['initial_cash']))}\n"
                f"🕐 Hora: {opened_at.split('T')[1][:5]}\n\n"
                "_Cuando cierres la caja, usa /cerrar_caja_"
            )

            await context.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="Markdown",
            )

        except CashPilotAPIError as e:
            if e.code == "CONFLICT":
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="⚠️ *Ya existe una caja abierta* para esta sucursal.\n\n"
                    "Ciérrala primero con `/cerrar_caja`",
                    parse_mode="Markdown",
                )
            else:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ Error: {e.message}",
                )
            logger.error(f"API error opening session: {e}")

        except Exception as e:
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Error al abrir caja. Intenta más tarde.",
            )
            logger.error(f"Error opening session: {e}", exc_info=True)

    async def handle_close_session(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /cerrar_caja command.

        Usage: /cerrar_caja <final_cash_gs> <envelope_amount_gs>
        Example: /cerrar_caja 1200000 300000

        Args:
            update: Telegram update
            context: Telegram context
        """
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        try:
            # Parse arguments
            if not context.args or len(context.args) < 2:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ *Uso incorrecto*\n\n"
                    "/cerrar_caja <monto_final> <monto_sobre>\n\n"
                    "Ejemplo: `/cerrar_caja 1200000 300000`",
                    parse_mode="Markdown",
                )
                return

            try:
                final_cash = Decimal(context.args[0])
                envelope_amount = Decimal(context.args[1])
            except ValueError:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ Los montos deben ser números válidos.\n\n"
                    "Ejemplo: `/cerrar_caja 1200000 300000`",
                    parse_mode="Markdown",
                )
                return

            if final_cash <= 0 or envelope_amount < 0:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ Los montos deben ser válidos (>= 0).",
                )
                return

            # Get session ID from context
            session_id = context.user_data.get("current_session_id")

            if not session_id:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ No hay caja abierta.\n\n"
                    "Usa `/abrir_caja` primero.",
                    parse_mode="Markdown",
                )
                return

            # Call API
            logger.info(f"User {user_id} closing session {session_id}")

            response = await self.client.close_cash_session(
                session_id=session_id,
                final_cash=final_cash,
                envelope_amount=envelope_amount,
            )

            # Extract key data
            cash_sales = Decimal(response.get("cash_sales", 0))
            total_sales = Decimal(response.get("total_sales", 0))
            difference = Decimal(response.get("difference", 0))

            # Determine status emoji
            if difference == 0:
                status_emoji = "✅"
                status_text = "Cuadre perfecto"
            elif difference > 0:
                status_emoji = "⚠️"
                status_text = "Faltante"
            else:
                status_emoji = "📦"
                status_text = "Sobrante"

            # Format response
            message = (
                "✅ *Caja cerrada*\n\n"
                f"{status_emoji} *{status_text}*: {self._format_currency(abs(difference))}\n"
                f"💰 Total efectivo: {self._format_currency(Decimal(response['final_cash']))}\n"
                f"📊 Ventas totales: {self._format_currency(total_sales)}\n"
                f"🕐 Cerrada a: {response['closed_at'].split('T')[1][:5]}\n\n"
                "_Caja lista para nueva sesión._"
            )

            await context.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="Markdown",
            )

            # Clear session ID from context
            context.user_data.pop("current_session_id", None)

        except CashPilotAPIError as e:
            if e.code == "NOT_FOUND":
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ Caja no encontrada.",
                )
            elif e.code == "INVALID_STATE":
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="⚠️ La caja no está abierta o ya fue cerrada.",
                )
            else:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ Error: {e.message}",
                )
            logger.error(f"API error closing session: {e}")

        except Exception as e:
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Error al cerrar caja. Intenta más tarde.",
            )
            logger.error(f"Error closing session: {e}", exc_info=True)

    async def handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /estado command - show current session status.

        Args:
            update: Telegram update
            context: Telegram context
        """
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        try:
            session_id = context.user_data.get("current_session_id")

            if not session_id:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ No hay caja abierta actualmente.",
                )
                return

            response = await self.client.get_session(session_id)

            status = response["status"]
            initial_cash = Decimal(response["initial_cash"])
            final_cash = response.get("final_cash")
            opened_at = response["opened_at"]

            if status == "OPEN":
                message = (
                    "📖 *Estado de Caja (ABIERTA)*\n\n"
                    f"🆔 ID: `{session_id}`\n"
                    f"💰 Monto inicial: {self._format_currency(initial_cash)}\n"
                    f"🕐 Abierta desde: {opened_at.split('T')[1][:5]}\n\n"
                    "_Cierra con /cerrar_caja_"
                )
            else:
                final_cash = Decimal(final_cash) if final_cash else Decimal(0)
                closed_at = response.get("closed_at", "")
                message = (
                    "📖 *Estado de Caja (CERRADA)*\n\n"
                    f"🆔 ID: `{session_id}`\n"
                    f"💰 Monto final: {self._format_currency(final_cash)}\n"
                    f"🕐 Cerrada a: {closed_at.split('T')[1][:5] if closed_at else 'N/A'}\n\n"
                    "_Abre una nueva con /abrir_caja_"
                )

            await context.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="Markdown",
            )

        except CashPilotAPIError as e:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Error: {e.message}",
            )
            logger.error(f"API error getting status: {e}")
        except Exception as e:
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Error al obtener estado.",
            )
            logger.error(f"Error getting status: {e}", exc_info=True)

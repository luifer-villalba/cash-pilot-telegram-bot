"""
CashPilot Telegram Bot entrypoint.

Connects to Telegram API and CashPilot backend API.
Implements cash session management commands.
"""

import logging
import os
import sys

from dotenv import load_dotenv
from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from src.cashpilot_client import CashPilotClient
from src.handlers.cash_session import CashSessionManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global client instance
cashpilot_client: CashPilotClient | None = None
session_manager: CashSessionManager | None = None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command handler."""
    user = update.effective_user
    message_text = (
        f"Hola {user.first_name}! 👋\n\n"
        "Bienvenido a *CashPilot Bot*.\n\n"
        "📋 *Comandos disponibles:*\n"
        "/abrir_caja - Abrir caja registradora\n"
        "/cerrar_caja - Cerrar caja y reconciliar\n"
        "/estado - Ver estado actual\n"
        "/ayuda - Mostrar esta ayuda"
    )
    await update.message.reply_text(message_text, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Help command handler."""
    help_text = (
        "📚 *Ayuda - CashPilot Bot*\n\n"
        "💡 *Cómo usar:*\n\n"
        "1️⃣ *Abrir Caja*\n"
        "/abrir_caja <monto_inicial>\n"
        "Ejemplo: /abrir_caja 500000\n\n"
        "2️⃣ *Cerrar Caja*\n"
        "/cerrar_caja <monto_final> <monto_sobre>\n"
        "Ejemplo: /cerrar_caja 1200000 300000\n\n"
        "3️⃣ *Ver Estado*\n"
        "/estado\n"
        "Muestra el estado actual de la caja.\n\n"
        "📊 *Detalles de la Reconciliación:*\n"
        "• Efectivo esperado = (monto_final + monto_sobre) - monto_inicial\n"
        "• Diferencia = Ventas totales - Efectivo esperado\n"
        "• ✅ Si diferencia = 0 → Cuadre perfecto\n"
        "• ⚠️ Si diferencia > 0 → Faltante\n"
        "• 📦 Si diferencia < 0 → Sobrante"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def post_init(application: Application) -> None:
    """Post-init hook: set commands menu."""
    commands = [
        BotCommand("start", "Iniciar bot"),
        BotCommand("abrir_caja", "Abrir caja registradora"),
        BotCommand("cerrar_caja", "Cerrar caja y reconciliar"),
        BotCommand("estado", "Ver estado actual"),
        BotCommand("ayuda", "Mostrar ayuda"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Bot commands set")


async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Health check endpoint for debugging."""
    try:
        health = await cashpilot_client.health_check()
        status = health.get("status", "unknown")
        uptime = health.get("uptime_seconds", "N/A")
        message = f"✅ API Status: {status}\nUptime: {uptime}s"
        await update.message.reply_text(message)
    except Exception as e:
        await update.message.reply_text(f"❌ API Error: {str(e)}")


def main() -> None:
    """Main entrypoint - start bot."""
    global cashpilot_client, session_manager

    # Load environment
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    api_url = os.getenv("CASHPILOT_API_URL")
    api_key = os.getenv("CASHPILOT_API_KEY")

    # Validate environment
    if not telegram_token:
        raise ValueError("TELEGRAM_TOKEN not set in .env")
    if not api_url:
        raise ValueError("CASHPILOT_API_URL not set in .env")

    logger.info("Starting CashPilot Telegram Bot...")
    logger.info(f"API URL: {api_url}")

    # Initialize client (but don't connect yet)
    cashpilot_client = CashPilotClient(api_url=api_url, api_key=api_key)
    session_manager = CashSessionManager(cashpilot_client)

    # Create application
    application = Application.builder().token(telegram_token).post_init(post_init).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ayuda", help_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(
        CommandHandler("abrir_caja", session_manager.handle_open_session)
    )
    application.add_handler(
        CommandHandler("cerrar_caja", session_manager.handle_close_session)
    )
    application.add_handler(CommandHandler("estado", session_manager.handle_status))
    application.add_handler(CommandHandler("health", health_check))

    logger.info("Handlers registered")

    # Start bot - connection happens on first use
    application.run_polling(allowed_updates=[])


if __name__ == "__main__":
    main()

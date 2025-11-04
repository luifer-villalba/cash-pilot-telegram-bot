"""Telegram bot response message templates."""

START_MESSAGE = "👋 Bienvenido a CashPilot\n\nSoy tu asistente para reconciliación de caja.\n\n🏪 Registra tu farmacia y comienza a trackear tus ventas.\n\nEscribe /help para ver los comandos disponibles."

HELP_MESSAGE = "📖 Comandos disponibles:\n\n/start - Iniciar y registrar tu farmacia\n/help - Ver este mensaje\n/mi_farmacia - Ver info de tu farmacia\n/nueva_sesion - Abrir nueva sesión de caja\n/cerrar_sesion - Cerrar sesión de caja\n\n¿Preguntas? Escribe /help nuevamente."

BUSINESS_INFO_MESSAGE = "🏪 Tu Farmacia\n\nNombre: {name}\nDirección: {address}\nTeléfono: {phone}\nEstado: {status}"

SESSION_OPENED_MESSAGE = "✅ Sesión de caja abierta\n\n💰 Caja inicial: ₲{initial_cash:,.2f}\n🕐 Hora: {opened_at}\n👤 Cajero: {cashier_name}\n\nCuando termines tu turno, usa /cerrar_sesion"

ERROR_MESSAGE = "❌ Algo salió mal\n\n{error}\n\nIntenta nuevamente o contacta al soporte."

NO_BUSINESS_MESSAGE = "⚠️ No tienes una farmacia registrada.\n\nUsa /start para registrar tu farmacia primero."
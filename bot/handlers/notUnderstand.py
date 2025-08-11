from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

async def not_understood(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle messages that don't match any command."""
    await update.message.reply_text("Iltimos, to'g'ri buyruqni kiriting. Bot buyruqlarini bilish uchun /help ni bosing")
    return ConversationHandler.END

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from bot.utils.keyboards import get_main_menu_keyboard

async def not_understood(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle messages that don't match any command."""
    await update.message.reply_text(
        "Iltimos, to'g'ri buyruqni kiriting. Bot buyruqlarini bilish uchun /help ni bosing",
        reply_markup=get_main_menu_keyboard()
    )
    return ConversationHandler.END

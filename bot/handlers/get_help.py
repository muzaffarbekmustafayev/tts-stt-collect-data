from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

async def get_bot_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get the bot help."""
    await update.message.reply_text("Bot buyruqlar\n\n"
        "/start - Botni (qayta) ishga tushirish\n"
        "/help - Bot buyruqlarini bilish\n"
        "/info - Bot haqida ma'lumot\n"
        "/statistics - Bot statistikasi\n" 
    )
    return ConversationHandler.END
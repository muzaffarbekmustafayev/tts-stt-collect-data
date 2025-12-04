from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from bot.utils.keyboards import get_main_menu_keyboard

async def get_bot_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get the bot info."""
    await update.message.reply_text("Bot haqida ma'lumot:\n"
        "Uzbek tilidagi TTS-STT modulini yaratish uchun ma'lumot to'plovchi bot. Siz bu module yaratilishiga o'z hissangizni qo'shishingiz mumkin. Bot buyruqlarini bilish uchun /help ni bosing",
        reply_markup=get_main_menu_keyboard()
    )
    return ConversationHandler.END

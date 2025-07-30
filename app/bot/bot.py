import logging
from telegram.ext import ApplicationBuilder
from app.bot.handlers import register_handlers
from app.config import settings
from app.core.logging import get_logger
# from app.db.session import engine

logger = get_logger("bot")

async def run_bot():
    try:
        application = ApplicationBuilder().token(settings.BOT_API_TOKEN).build()
        register_handlers(application)
        
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        logger.info("🤖 Telegram bot is running.")
    except Exception as e:
        logger.exception("❌ Telegram botni ishga tushirishda xatolik yuz berdi: %s", e)
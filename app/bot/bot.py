import logging
from telegram.ext import ApplicationBuilder
from app.bot.handlers import register_handlers
from app.config import settings
from app.core.logging import get_logger
# from app.db.session import engine

logger = get_logger("bot")

# Bot application global variable
bot_application = None

async def run_bot():
    try:
        global bot_application
        bot_application = ApplicationBuilder().token(settings.BOT_API_TOKEN).build()
        register_handlers(bot_application)
        await bot_application.initialize()
        await bot_application.start()
        await bot_application.updater.start_polling()
        logger.info("🤖 Telegram bot is running.")
    except Exception as e:
        logger.exception("❌ Error starting bot: %s", e)
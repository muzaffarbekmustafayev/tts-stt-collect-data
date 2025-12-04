from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters
)
from app.config import settings
from app.core.logging import get_logger
import asyncio

from bot.handlers.registration import register_handlers
from bot.handlers.get_information import get_bot_info
from bot.handlers.notUnderstand import not_understood
from bot.handlers.getStatisticHandler import get_bot_statisticHandler
from bot.handlers.get_help import get_bot_help
from bot.handlers.getAudioHandler import get_audio_handler
from bot.handlers.checkAudioHanler import check_audio_handler
from bot.utils.config import KEYBOARD_NAMES

# Configure logging
logger = get_logger("bot")

# Set up the telegram bot
def create_bot_application():
    """Create and configure the bot application."""
    application = Application.builder().token(settings.BOT_API_TOKEN).build()
    
    # Register ConversationHandlers first (they have higher priority)
    register_handlers(application)
    get_audio_handler(application)
    check_audio_handler(application)
    
    # Add command handlers
    application.add_handler(CommandHandler("info", get_bot_info))
    application.add_handler(MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['INFO']}$"), get_bot_info))
    application.add_handler(CommandHandler("help", get_bot_help))
    application.add_handler(CommandHandler("statistics", get_bot_statisticHandler))
    application.add_handler(MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['STATISTICS']}$"), get_bot_statisticHandler))
    
    # Add fallback handler for unrecognized messages LAST (lowest priority)
    application.add_handler(MessageHandler(filters.TEXT, not_understood))

    return application

# Bot ishga tushirish funksiyasi
async def run_bot():
    """Run the telegram bot in the background"""
    application = create_bot_application()
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    try:
        # Keep the bot running
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.info("Bot task cancelled")
    except Exception as e:
        logger.error(f"Error in bot: {str(e)}")
        raise e
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()
        logger.info("Bot stopped")

     
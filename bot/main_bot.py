from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.error import Conflict, NetworkError, TimedOut
from app.config import settings
from app.core.logging import get_logger

from bot.handlers.registration import register_handlers
from bot.handlers.get_information import get_bot_info
from bot.handlers.notUnderstand import not_understood
from bot.handlers.getStatisticHandler import get_bot_statisticHandler
from bot.handlers.changeProfileHandler import change_profile_handler
from bot.handlers.get_help import get_bot_help
from bot.handlers.getAudioHandler import get_audio_handler
from bot.handlers.checkAudioHanler import check_audio_handler
from bot.utils.config import KEYBOARD_NAMES

logger = get_logger("bot")


async def error_handler(update: object, context) -> None:
    """Global error handler for the bot."""
    error = context.error

    if isinstance(error, Conflict):
        logger.warning("Bot conflict: another instance is running. Stopping polling.")
        if context.application.updater:
            await context.application.updater.stop()
        return

    if isinstance(error, (NetworkError, TimedOut)):
        logger.warning(f"Network error (will retry): {error}")
        return

    logger.error(f"Unhandled bot error: {error}", exc_info=error)


def create_bot_application() -> Application:
    """Create and configure the bot application."""
    application = (
        Application.builder()
        .token(settings.BOT_API_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .build()
    )

    # Global error handler
    application.add_error_handler(error_handler)

    # ConversationHandlers (higher priority - register first)
    register_handlers(application)
    get_audio_handler(application)
    check_audio_handler(application)
    change_profile_handler(application)

    # Command handlers
    application.add_handler(CommandHandler("info", get_bot_info))
    application.add_handler(CommandHandler("help", get_bot_help))
    application.add_handler(CommandHandler("statistics", get_bot_statisticHandler))

    # Keyboard button handlers
    application.add_handler(MessageHandler(
        filters.Regex(f"^{KEYBOARD_NAMES['INFO']}$"), get_bot_info
    ))
    application.add_handler(MessageHandler(
        filters.Regex(f"^{KEYBOARD_NAMES['STATISTICS']}$"), get_bot_statisticHandler
    ))

    # Fallback - lowest priority
    application.add_handler(MessageHandler(filters.TEXT, not_understood))

    return application

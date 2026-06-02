from datetime import timedelta

from fastapi import HTTPException
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.services.user_service import get_user_statistic
from bot.utils.keyboards import get_main_menu_keyboard

logger = get_logger("handlers")


def format_duration(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining_seconds = seconds % 60
    return f"{hours} soat {minutes} daqiqa {remaining_seconds} sekund"


def format_elapsed(delta: timedelta) -> str:
    total_seconds = int(delta.total_seconds())
    if total_seconds < 0:
        total_seconds = 0
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{days} kun {hours} soat {minutes} daqiqa {seconds} sekund"


async def get_bot_statisticHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get bot statistics"""
    try:
        user_telegram_id = str(update.effective_user.id)
        async with AsyncSessionLocal() as db:
            regis_time, sent_audio_count, sent_audio_duration, checked_audio_count, checked_audio_duration = await get_user_statistic(
                user_telegram_id, db
            )

        sent_audio_duration = int(sent_audio_duration or 0)
        checked_audio_duration = int(checked_audio_duration or 0)

        stats_text = (
            "<b>📊 Sizning statistikangiz</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"🆔 <b>Telegram ID:</b> <code>{user_telegram_id}</code>\n"
            f"⏳ <b>Ro'yxatdan o'tganiga:</b> {format_elapsed(regis_time)}\n\n"
            "🎤 <b>Yuborilgan ovozlar</b>\n"
            f"• Soni: <b>{sent_audio_count} ta</b>\n"
            f"• Umumiy davomiyligi: <b>{format_duration(sent_audio_duration)}</b>\n\n"
            "🎧 <b>Tekshirgan ovozlar</b>\n"
            f"• Soni: <b>{checked_audio_count} ta</b>\n"
            f"• Umumiy davomiyligi: <b>{format_duration(checked_audio_duration)}</b>"
        )

        await update.message.reply_text(
            stats_text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_menu_keyboard(),
        )
    except HTTPException as e:
        await update.message.reply_text(f"Xato: {e.detail}")
    except Exception as e:
        logger.error(f"Statistics error: {e}")
        await update.message.reply_text("Statistika olishda xatolik yuz berdi.")

from telegram import Update
from telegram.ext import ContextTypes
from app.services.user_service import get_user_statistic
from bot.utils.keyboards import get_main_menu_keyboard
from app.core.logging import get_logger
from fastapi import HTTPException

logger = get_logger("handlers")

async def get_bot_statisticHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get user statistics for the bot"""
    try:
        user_telegram_id = str(update.effective_user.id)
        
        stats = await get_user_statistic(user_telegram_id)
        regisTime, sentAudioCount, sentAudioDuration, checkedAudioCount, checkedAudioDuration = stats
        
        sentAudioDuration = int(sentAudioDuration or 0)
        checkedAudioDuration = int(checkedAudioDuration or 0)

        days = regisTime.days
        hours = regisTime.seconds // 3600
        minutes = (regisTime.seconds % 3600) // 60
        seconds = regisTime.seconds % 60

        await update.message.reply_text(
            f"📊 Statistika:\n\n"
            f"👤 Telegram ID: {user_telegram_id}\n"
            f"⏰ Ro'yxatdan o'tganidan beri: {days} kun {hours} soat {minutes} daqiqa\n\n"
            f"🎤 Yuborilgan ovozlar: {sentAudioCount} ta\n"
            f"   ⏱ Davomiyligi: {sentAudioDuration // 3600}s {(sentAudioDuration % 3600) // 60}d {sentAudioDuration % 60}s\n\n"
            f"🎧 Tekshirilgan ovozlar: {checkedAudioCount} ta\n"
            f"   ⏱ Davomiyligi: {checkedAudioDuration // 3600}s {(checkedAudioDuration % 3600) // 60}d {checkedAudioDuration % 60}s\n",
            reply_markup=get_main_menu_keyboard()
        )
    except HTTPException as e:
        await update.message.reply_text(f"❌ {e.detail}", reply_markup=get_main_menu_keyboard())
    except Exception as e:
        logger.error(f"Statistics handler error: {e}", exc_info=True)
        await update.message.reply_text("❌ Statistika olishda xatolik yuz berdi.", reply_markup=get_main_menu_keyboard())
from telegram import Update
from telegram.ext import ContextTypes
from app.services.user_service import get_user_statistic
from app.db.session import AsyncSessionLocal
from bot.utils.keyboards import get_main_menu_keyboard
from app.core.logging import get_logger
from fastapi import HTTPException

logger = get_logger("handlers")

async def get_bot_statisticHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get bot statistics"""
    try:
        user_telegram_id = str(update.effective_user.id)  # Convert to string
        async with AsyncSessionLocal() as db:
            regisTime, sentAudioCount, sentAudioDuration, checkedAudioCount, checkedAudioDuration = await get_user_statistic(user_telegram_id, db)
            
        await update.message.reply_text(f"📊 Statistika:\n\n"
            f"👤 Foydalanuvchi telegram idsi: {user_telegram_id}\n"
            f"⏰ Registratsiya vaqtidan beri: {regisTime.days} kun {regisTime.seconds//3600} soat {(regisTime.seconds%3600)//60} daqiqa {regisTime.seconds%60} sekund o'tdi.\n\n"
            f"🎤 Yuborilgan ovozlar soni: {sentAudioCount} ta / {sentAudioDuration//3600} soat {sentAudioDuration%3600//60} daqiqa {sentAudioDuration%60} sekund\n"
            f"🎧 Tekshirilgan ovozlar soni: {checkedAudioCount} ta / {checkedAudioDuration//3600} soat {checkedAudioDuration%3600//60} daqiqa {checkedAudioDuration%60} sekund\n",
            reply_markup=get_main_menu_keyboard()
        )
    except HTTPException as e:
        await update.message.reply_text(f"❌ {e.detail}")
    except Exception as e:
        logger.error(f"Statistics error: {e}")
        await update.message.reply_text("❌ Statistika olishda xatolik yuz berdi.")


from telegram import Update
from telegram.ext import Application, ContextTypes, ConversationHandler, MessageHandler, filters, CommandHandler
from app.core.logging import get_logger

import asyncio
import requests
import os
import tempfile
from pathlib import Path

from app.db.session import AsyncSessionLocal
from bot.utils.keyboards import get_main_menu_keyboard, get_confirmation_or_retry_keyboard, get_next_or_finish_keyboard, get_back_to_menu_keyboard
from bot.utils.config import KEYBOARD_NAMES
from bot.services.user_services import get_user_by_telegramId
from app.services.user_service import get_user_statistic
from app.services.received_audio_services import get_audio_by_user_id_and_sentence_id, update_received_audio_path_status
from app.services.bot_services import (
    bot_get_available_sentence,
    BotServiceError
)
from app.api.received_audio import ensure_directories_exist, UPLOAD_DIR
from pydub import AudioSegment
import shutil
import uuid

logger = get_logger("handlers")


async def get_sentence_and_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get sentence and handle audio upload"""
    user_telegram_id = str(update.effective_user.id)
    
    try:
        # Get user info using bot service
        async with AsyncSessionLocal() as db:
            user = await get_user_by_telegramId(user_telegram_id, db)
            
        # Get sentence for user using bot service
        async with AsyncSessionLocal() as db:
            sentence = await bot_get_available_sentence(user.id, 0, db)  # sent_audio_count ni hisoblash kerak
            
        context.user_data['current_sentence'] = sentence
        context.user_data['user_id'] = user.id
        
        
        await update.message.reply_text(
            f"📝 Quyidagi gapni o'qing va ovozli xabar shaklida yuboring:\n\n"
            f"<b><i>{sentence.text}</i></b>\n",
            reply_markup=get_back_to_menu_keyboard(),
            parse_mode="HTML"
        )
        return AWAITING_AUDIO
            
    except BotServiceError as e:
        await update.message.reply_text(f"❌ {e.message}", reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Get sentence error: {e}")
        await update.message.reply_text("❌ Server bilan bog'lanishda xatolik.", reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END


async def handle_audio_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle audio file upload"""
    if not update.message.voice and not update.message.audio:
        from bot.utils.keyboards import get_cancel_keyboard
        reply_markup = get_cancel_keyboard()
        await update.message.reply_text(
            f"❌ Iltimos, ovozli xabar yuboring yoki {KEYBOARD_NAMES['CANCEL']} tugmasini bosing.",
            reply_markup=reply_markup
        )
        return AWAITING_AUDIO
    
    try:
        # Papkalarni yaratish
        ensure_directories_exist()
        
        # Yuklash jarayoni haqida xabar
        processing_message = await update.message.reply_text("⏳ Audio yuklanmoqda, iltimos kuting...")
        
        if update.message.voice:
            audio_file = await update.message.voice.get_file()
            file_extension = "ogg"
            context.user_data['duration'] = update.message.voice.duration
        else:
            audio_file = await update.message.audio.get_file()
            file_extension = os.path.splitext(update.message.audio.file_path)[1].lower()
            context.user_data['duration'] = update.message.audio.duration

        user_id = context.user_data['user_id']
        sentence_id = context.user_data['current_sentence'].id
        
        # Mavjud audio borligini tekshirish
        async with AsyncSessionLocal() as db:
            received_audio = await get_audio_by_user_id_and_sentence_id(user_id, sentence_id, db)
        
        
        audio_filename = f"{uuid.uuid4()}.{file_extension}"
        audio_path = os.path.join(UPLOAD_DIR, audio_filename)
        
        # Timeout bilan fayl yuklash (60 soniya)
        try:
            await asyncio.wait_for(
                audio_file.download_to_drive(audio_path),
                timeout=60.0
            )
        except asyncio.TimeoutError:
            await processing_message.delete()
            await update.message.reply_text(
                "❌ Fayl yuklashda vaqt tugadi. Iltimos, qaytadan urinib ko'ring yoki kichikroq fayl yuboring.",
                reply_markup=get_back_to_menu_keyboard()
            )
            return AWAITING_AUDIO

        # received audio update qilish
        relative_path = f"audio/{audio_filename}"
        
        context.user_data['relative_path'] = relative_path
        context.user_data['audio_path'] = audio_path
        context.user_data['received_audio_id'] = received_audio.id
        
        # Yuklash muvaffaqiyatli xabarini o'chirish
        await processing_message.delete()
        
        await update.message.reply_text(
            "✅ Audio yuklandi! Tasdiqlash uchun tugmani bosing.",
            reply_markup=get_confirmation_or_retry_keyboard()
        )
        
        return CONFIRMATION
        
    except asyncio.TimeoutError:
        logger.error(f"Audio upload timeout for user {update.effective_user.id}")
        await update.message.reply_text(
            "❌ Fayl yuklashda vaqt tugadi. Iltimos, qaytadan urinib ko'ring.",
            reply_markup=get_back_to_menu_keyboard()
        )
        return AWAITING_AUDIO
    except Exception as e:
        logger.error(f"Audio upload error: {e}")
        await update.message.reply_text(
            "❌ Ovoz yuklashda xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.",
            reply_markup=get_back_to_menu_keyboard()
        )
        return AWAITING_AUDIO

async def handle_audio_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle audio confirmation"""
    
    confirmation_text = update.message.text.strip()
    
    if confirmation_text not in [KEYBOARD_NAMES["RETRY_RECORDING"], KEYBOARD_NAMES["CONFIRMATION"]]:
        await update.message.reply_text(
            "❌ Iltimos, quyidagi tugmalardan birini tanlang:",
            reply_markup=get_confirmation_or_retry_keyboard()
        )
        return CONFIRMATION
    
    if confirmation_text == KEYBOARD_NAMES["RETRY_RECORDING"]:
        audio_path = context.user_data['audio_path']
        if os.path.exists(audio_path):
            os.remove(audio_path)
        await update.message.reply_text(
            f"🔄 Ovozlarni qaytadan yozib yuborishingiz mumkin. Iltimos, ovoz yozishdan oldin matnni yaxshilab o'qib oling:\n\n"
            f"<b><i>{context.user_data['current_sentence'].text}</i></b>\n",
            reply_markup=get_back_to_menu_keyboard(),
            parse_mode="HTML"
        )
        return AWAITING_AUDIO
        
    else:
        relative_path = context.user_data['relative_path']
        received_audio_id = context.user_data['received_audio_id']
        duration = context.user_data['duration'] or 0
        async with AsyncSessionLocal() as db:
            await update_received_audio_path_status(received_audio_id=received_audio_id, file_path=relative_path, duration=duration, db=db)
        
        await update.message.reply_text(
            "✅ Ovoz muvaffaqiyatli saqlandi!",
            reply_markup=get_next_or_finish_keyboard()
        )
        return NEXT_OR_FINISH


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation"""
    context.user_data.clear()    
    await update.message.reply_text(
        "Bosh menu.",
        reply_markup=get_main_menu_keyboard()
    )
    return ConversationHandler.END


async def handle_finish_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle finish audio"""
    context.user_data.clear()
    user_telegram_id = str(update.effective_user.id)
    async with AsyncSessionLocal() as db:
        [_, sent_audio_count, sent_audio_duration, _, _] = await get_user_statistic(user_telegram_id, db)
    await update.message.reply_text(
        f"Yakunlandi! Siz yuborgan ovozlar soni {sent_audio_count} ta / {sent_audio_duration//3600} soat {sent_audio_duration%3600//60} daqiqa {sent_audio_duration%60} sekund. Yana ovoz yuborish uchun '{KEYBOARD_NAMES['SEND_AUDIO']}' ni bosing.",
        reply_markup=get_main_menu_keyboard()
    )
    return ConversationHandler.END


AWAITING_AUDIO = 1
CONFIRMATION = 2
NEXT_OR_FINISH = 3

def get_audio_handler(app: Application):
    """Get the audio."""
    # Audio upload conversation handler
    audio_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(KEYBOARD_NAMES['SEND_AUDIO']), get_sentence_and_audio)],
        states={
            AWAITING_AUDIO: [
                MessageHandler(filters.VOICE | filters.AUDIO, handle_audio_upload),
                MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['BACK_TO_MENU']}$"), cancel)
            ],
            CONFIRMATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_audio_confirmation),
                MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['CANCEL']}$"), cancel)
            ],
            NEXT_OR_FINISH: [
                MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['NEXT']}$"), get_sentence_and_audio),
                MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['FINISH']}$"), handle_finish_audio)
            ],
        },
        fallbacks=[MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['CANCEL']}$"), cancel)],
        allow_reentry=True
    )
    
    
    app.add_handler(audio_conv_handler)


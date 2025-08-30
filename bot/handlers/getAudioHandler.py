from telegram import Update
from telegram.ext import Application, ContextTypes, ConversationHandler, MessageHandler, filters, CommandHandler
from app.core.logging import get_logger

import requests
import os
import tempfile
from pathlib import Path

from app.db.session import AsyncSessionLocal
from bot.utils.keyboards import get_main_menu_keyboard
from bot.utils.config import KEYBOARD_NAMES
from bot.services.user_services import get_user_by_telegramId
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
        
        from bot.utils.keyboards import get_cancel_keyboard
        reply_markup = get_cancel_keyboard()
        
        await update.message.reply_text(
            f"📝 Quyidagi gapni o'qib, ovoz yozib yuboring:\n\n"
            f"'{sentence.text}'\n\n"
            f"🎤 Ovoz xabar yuboring yoki {KEYBOARD_NAMES['CANCEL']} tugmasini bosib bekor qiling.",
            reply_markup=reply_markup
        )
        return AWAITING_AUDIO
            
    except BotServiceError as e:
        await update.message.reply_text(f"❌ {e.message}")
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Get sentence error: {e}")
        await update.message.reply_text("❌ Server bilan bog'lanishda xatolik.")
        return ConversationHandler.END


async def handle_audio_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle audio file upload"""
    if not update.message.voice and not update.message.audio:
        from bot.utils.keyboards import get_cancel_keyboard
        reply_markup = get_cancel_keyboard()
        await update.message.reply_text(
            f"❌ Iltimos, ovoz xabar yuboring yoki {KEYBOARD_NAMES['CANCEL']} tugmasini bosing.",
            reply_markup=reply_markup
        )
        return AWAITING_AUDIO
    
    try:
        # Papkalarni yaratish
        ensure_directories_exist()
        if update.message.voice:
            audio_file = await update.message.voice.get_file()
            file_extension = "ogg"
        else:
            audio_file = await update.message.audio.get_file()
            file_extension = os.path.splitext(update.message.audio.file_path)[1].lower()

        user_id = context.user_data['user_id']
        sentence_id = context.user_data['current_sentence'].id
        
        # Mavjud audio borligini tekshirish
        async with AsyncSessionLocal() as db:
            received_audio = await get_audio_by_user_id_and_sentence_id(user_id, sentence_id, db)
        
        
        audio_filename = f"{uuid.uuid4()}.{file_extension}"
        audio_path = os.path.join(UPLOAD_DIR, audio_filename)
        
        await audio_file.download_to_drive(audio_path)

        # received audio update qilish
        relative_path = f"audio/{audio_path}"
        async with AsyncSessionLocal() as db:
            await update_received_audio_path_status(received_audio_id=received_audio.id, file_path=relative_path, db=db)
        
        # Success message
        reply_markup = get_main_menu_keyboard()
        await update.message.reply_text(
            "✅ Ovoz muvaffaqiyatli yuklandi!",
            reply_markup=reply_markup
        )
        
        # Clear user data
        context.user_data.clear()
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Audio upload error: {e}")
        await update.message.reply_text("❌ Ovoz yuklashda xatolik yuz berdi.")
        return ConversationHandler.END



async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation"""
    context.user_data.clear()
    
    from bot.utils.keyboards import get_cancel_keyboard
    reply_markup = get_main_menu_keyboard()
    
    await update.message.reply_text(
        "❌ Amal bekor qilindi.",
        reply_markup=reply_markup
    )
    return ConversationHandler.END


AWAITING_AUDIO = 1

def get_audio_handler(app: Application):
    """Get the audio."""
    # Audio upload conversation handler
    audio_conv_handler =    ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(KEYBOARD_NAMES['SEND_AUDIO']), get_sentence_and_audio)],
        states={
            AWAITING_AUDIO: [
                MessageHandler(filters.VOICE | filters.AUDIO, handle_audio_upload),
                MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['CANCEL']}$"), cancel)
            ],
        },
        fallbacks=[MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['CANCEL']}$"), cancel)],
        allow_reentry=True
    )
    
    
    app.add_handler(audio_conv_handler)


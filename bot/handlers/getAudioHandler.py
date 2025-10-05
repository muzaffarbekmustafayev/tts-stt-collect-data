from telegram import Update
from telegram.ext import Application, ContextTypes, ConversationHandler, MessageHandler, filters, CommandHandler
from app.core.logging import get_logger

import requests
import os
import tempfile
from pathlib import Path

from app.db.session import AsyncSessionLocal
from bot.utils.keyboards import get_main_menu_keyboard, get_confirmation_keyboard
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
            f"📝 Quyidagi gapni o'qing va ovozli xabar shaklida yuboring:\n\n"
            f"'_{sentence.text}_'\n\n"
            f"🎤 Ovoz xabar yuboring yoki {KEYBOARD_NAMES['CANCEL']} tugmasini bosib bekor qiling.",
            reply_markup=reply_markup
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
        relative_path = f"audio/{audio_filename}"
        
        context.user_data['relative_path'] = relative_path
        context.user_data['audio_path'] = audio_path
        context.user_data['received_audio_id'] = received_audio.id
        
        await update.message.reply_text(
            "Ovozli xabarni qabul qilish uchun tasdiqlashni bosing!",
            reply_markup=get_confirmation_keyboard()
        )
        
        return CONFIRMATION
        
    except Exception as e:
        logger.error(f"Audio upload error: {e}")
        await update.message.reply_text("❌ Ovoz yuklashda xatolik yuz berdi.", reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END

async def handle_audio_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle audio confirmation"""
    
    confirmation_text = update.message.text.strip()
    
    if confirmation_text not in [KEYBOARD_NAMES["CANCEL"], KEYBOARD_NAMES["CONFIRMATION"]]:
        await update.message.reply_text(
            "❌ Iltimos, quyidagi tugmalardan birini tanlang:",
            reply_markup=get_confirmation_keyboard()
        )
        return CONFIRMATION
    
    if confirmation_text == KEYBOARD_NAMES["CANCEL"]:
        audio_path = context.user_data['audio_path']
        if os.path.exists(audio_path):
            os.remove(audio_path)
        await update.message.reply_text(
            "❌ Amal bekor qilindi.",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END
        
    else:
        relative_path = context.user_data['relative_path']
        received_audio_id = context.user_data['received_audio_id']
        async with AsyncSessionLocal() as db:
            await update_received_audio_path_status(received_audio_id=received_audio_id, file_path=relative_path, db=db)
        
        await update.message.reply_text(
            "✅ Ovoz muvaffaqiyatli saqlandi!",
            reply_markup=get_main_menu_keyboard()
        )
        context.user_data.clear()
        return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation"""
    context.user_data.clear()    
    await update.message.reply_text(
        "❌ Amal bekor qilindi.",
        reply_markup=get_main_menu_keyboard()
    )
    return ConversationHandler.END


async def handle_next_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle next audio"""
    return NEXT_OR_FINISH

async def handle_finish_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle finish audio"""
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
                MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['CHECK_AUDIO']}$"), handle_audio_confirmation),
                MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['CANCEL']}$"), cancel)
            ],
            CONFIRMATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_audio_confirmation),
                MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['CANCEL']}$"), cancel)
            ],
            NEXT_OR_FINISH: [
                MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['NEXT']}$"), handle_next_audio),
                MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['FINISH']}$"), handle_finish_audio)
            ],
        },
        fallbacks=[MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['CANCEL']}$"), cancel)],
        allow_reentry=True
    )
    
    
    app.add_handler(audio_conv_handler)


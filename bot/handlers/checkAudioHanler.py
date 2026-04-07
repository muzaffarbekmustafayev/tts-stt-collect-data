from telegram import Update
from telegram.ext import Application, ContextTypes, ConversationHandler, MessageHandler, filters
from app.core.logging import get_logger
from app.services.user_service import get_user_statistic
from beanie import PydanticObjectId

from bot.utils.keyboards import get_main_menu_keyboard, get_verification_keyboard, get_next_or_finish_keyboard
from bot.utils.config import KEYBOARD_NAMES
from bot.services.user_services import get_user_by_telegramId
from app.services.bot_services import (
    bot_get_audio_for_checking,
    bot_create_checked_audio,
    BotServiceError
)

logger = get_logger("handlers")

# Conversation states
AWAITING_VERIFICATION = 1
NEXT_OR_FINISH = 2

async def get_audio_for_checking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get audio for checking"""
    user_telegram_id = str(update.effective_user.id)
    
    try:
        # Get user info using bot service
        user = await get_user_by_telegramId(user_telegram_id)
        if not user:
             await update.message.reply_text("❌ Foydalanuvchi topilmadi. Iltimos, /start buyrug'ini yuboring.")
             return ConversationHandler.END
            
        # Get audio for checking using bot service
        received_audio = await bot_get_audio_for_checking(user.id)

        # sentence already fetched via fetch_links=True in service
        sentence_text = received_audio.sentence.text if received_audio.sentence else "Matn topilmadi"
        sentence_id = received_audio.sentence.id if received_audio.sentence else None
            
        context.user_data['current_audio'] = received_audio
        context.user_data['user_id'] = user.id
        
        await update.message.reply_text(
            f"🎧 Quyidagi ovozni tinglab, sifatini baholang:\n\n"
            f"📝 Matn: <b><i>{sentence_text}</i></b>\n\n"
            f"🎤 Ovoz fayli yuklanmoqda...",
            reply_markup=get_verification_keyboard(),
            parse_mode="HTML"
        )

        # Send audio file
        if received_audio.audio_path:
            try:
                audio_path = f"media/{received_audio.audio_path}"
                caption_text = f"📝 Matn: <b><i>{sentence_text}</i></b>"
                with open(audio_path, 'rb') as audio_file:
                    await update.message.reply_voice(
                        voice=audio_file,
                        caption=caption_text,
                        parse_mode="HTML"
                    )
            except Exception as e:
                logger.error(f"Audio file send error: {e}")
                try:
                    with open(audio_path, 'rb') as audio_file:
                        await update.message.reply_document(
                            document=audio_file,
                            caption=caption_text + "\n\n⚠️ Hujjat sifatida yuborildi.",
                            parse_mode="HTML"
                        )
                except Exception as doc_e:
                    logger.error(f"Document send error: {doc_e}")
                    await update.message.reply_text(
                        "❌ Ovoz faylini yuklashda xatolik.",
                        reply_markup=get_main_menu_keyboard()
                    )
                    return ConversationHandler.END
        
        return AWAITING_VERIFICATION
            
    except BotServiceError as e:
        msg = e.message
        if "no available" in msg.lower() or "topilmadi" in msg.lower():
            msg = "📭 Hozircha tekshirish uchun ovoz mavjud emas. Keyinroq qaytib keling!"
        elif "limit" in msg.lower():
            msg = "✅ Siz belgilangan limitdagi barcha ovozlarni tekshirdingiz!"
        await update.message.reply_text(msg, reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Get audio for checking error: {e}")
        await update.message.reply_text("❌ Server bilan bog'lanishda xatolik.", reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END


async def handle_verification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle audio verification"""
    verification_text = update.message.text.strip()
    
    if verification_text not in [KEYBOARD_NAMES["CORRECT"], KEYBOARD_NAMES["INCORRECT"]]:
        await update.message.reply_text(
            f"❌ Iltimos, quyidagi tugmalardan birini tanlang:",
            reply_markup=get_verification_keyboard()
        )
        return AWAITING_VERIFICATION
    
    try:
        # Determine if audio is correct
        is_correct = verification_text == KEYBOARD_NAMES["CORRECT"]
        
        # Get data from context
        user_id = context.user_data['user_id']
        received_audio = context.user_data['current_audio']
        
        # Create checked audio record via bot service wrapper
        await bot_create_checked_audio(received_audio.id, user_id, is_correct)
        
        await update.message.reply_text(
            f"Baholaganingiz uchun rahmat! 👌",
            reply_markup=get_next_or_finish_keyboard()
        )
        
        return NEXT_OR_FINISH
        
    except BotServiceError as e:
        await update.message.reply_text(f"❌ {e.message}", reply_markup=get_main_menu_keyboard())
        context.user_data.clear()
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Verification error: {e}")
        await update.message.reply_text("❌ Baholashda xatolik yuz berdi.", reply_markup=get_main_menu_keyboard())
        context.user_data.clear()
        return ConversationHandler.END


async def cancel_checking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation"""
    context.user_data.clear()
    
    await update.message.reply_text(
        "❌ Audio tekshirish bekor qilindi.",
        reply_markup=get_main_menu_keyboard()
    )
    return ConversationHandler.END

async def handle_finish_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle finish audio"""
    context.user_data.clear()
    try:
        user_telegram_id = str(update.effective_user.id)
        stats = await get_user_statistic(user_telegram_id)
        _, _, _, checkedAudioCount, _ = stats
        await update.message.reply_text(
            f"✅ Yakunlandi! Siz tekshirgan ovozlar soni: {checkedAudioCount} ta.\n"
            f"Yana ovoz tekshirish uchun '{KEYBOARD_NAMES['CHECK_AUDIO']}' ni bosing.",
            reply_markup=get_main_menu_keyboard()
        )
    except Exception:
        await update.message.reply_text(
            "✅ Baholash yakunlandi!",
            reply_markup=get_main_menu_keyboard()
        )
    return ConversationHandler.END


def check_audio_handler(app: Application):
    """Register audio checking handler"""
    
    # Audio checking conversation handler
    check_audio_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['CHECK_AUDIO']}$"), get_audio_for_checking)],
        states={
            AWAITING_VERIFICATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_verification)
            ],
            NEXT_OR_FINISH: [
                MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['NEXT']}$"), get_audio_for_checking),
                MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['FINISH']}$"), handle_finish_audio)
            ],
        },
        fallbacks=[MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['CANCEL']}$"), cancel_checking)],
        allow_reentry=True
    )
    
    app.add_handler(check_audio_conv_handler)
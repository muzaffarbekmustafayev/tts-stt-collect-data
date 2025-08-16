from telegram import Update
from telegram.ext import Application, ContextTypes, ConversationHandler, MessageHandler, filters
from app.core.logging import get_logger

from app.db.session import AsyncSessionLocal
from bot.utils.keyboards import get_main_menu_keyboard, get_verification_keyboard
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

async def get_audio_for_checking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get audio for checking"""
    user_telegram_id = str(update.effective_user.id)
    
    try:
        # Get user info using bot service
        async with AsyncSessionLocal() as db:
            user = await get_user_by_telegramId(user_telegram_id, db)
            
        # Get audio for checking using bot service
        async with AsyncSessionLocal() as db:
            received_audio = await bot_get_audio_for_checking(user.id, db)
            
        # Get sentence for the audio
        from app.services.sentence_service import get_sentence_by_id
        async with AsyncSessionLocal() as db:
            sentence = await get_sentence_by_id(received_audio.sentence_id, db)
            
        context.user_data['current_audio'] = received_audio
        context.user_data['user_id'] = user.id
        
        # Debug: log received_audio attributes
        logger.info(f"Received audio object: {received_audio}")
        logger.info(f"Received audio attributes: {dir(received_audio)}")
        logger.info(f"Audio path: {getattr(received_audio, 'audio_path', 'NOT_FOUND')}")
        
        reply_markup = get_verification_keyboard()
        
        await update.message.reply_text(
            f"🎧 Quyidagi ovozni tinglab, sifatini baholang:\n\n"
            f"📝 Matn: '{sentence.text}'\n\n"
            f"🎤 Ovoz fayli yuklanmoqda...\n\n"
            f"Ovozni tinglaganingizdan so'ng, quyidagi tugmalardan birini bosing:",
            reply_markup=reply_markup
        )
        
        # Send audio file
        if received_audio.audio_path:  # Fix: use audio_path instead of file_path
            try:
                # Audio faylni yuklash va yuborish
                audio_path = f"media/{received_audio.audio_path}"  # Fix: use audio_path
                with open(audio_path, 'rb') as audio_file:
                    await update.message.reply_audio(
                        audio=audio_file,
                        title=f"Audio {received_audio.id}",
                        performer="User",
                        caption=f"Matn: {sentence.text}"
                    )
            except Exception as e:
                logger.error(f"Audio file send error: {e}")
                await update.message.reply_text(
                    "❌ Ovoz faylini yuklashda xatolik yuz berdi."
                )
                return ConversationHandler.END
        
        return AWAITING_VERIFICATION
            
    except BotServiceError as e:
        await update.message.reply_text(f"❌ {e.message}")
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Get audio for checking error: {e}")
        await update.message.reply_text("❌ Server bilan bog'lanishda xatolik.")
        return ConversationHandler.END


async def handle_verification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle audio verification"""
    verification_text = update.message.text.strip()
    
    if verification_text not in [KEYBOARD_NAMES["CORRECT"], KEYBOARD_NAMES["INCORRECT"]]:
        reply_markup = get_verification_keyboard()
        await update.message.reply_text(
            f"❌ Iltimos, quyidagi tugmalardan birini tanlang:",
            reply_markup=reply_markup
        )
        return AWAITING_VERIFICATION
    
    try:
        # Determine if audio is correct
        is_correct = verification_text == KEYBOARD_NAMES["CORRECT"]
        
        # Get data from context
        user_id = context.user_data['user_id']
        received_audio = context.user_data['current_audio']
        
        # Create checked audio record
        async with AsyncSessionLocal() as db:
            await bot_create_checked_audio(
                audio_id=received_audio.id,
                checked_by=user_id,
                is_correct=is_correct,
                db=db
            )
        
        # Success message
        status_text = "✅ To'g'ri" if is_correct else "❌ Noto'g'ri"
        reply_markup = get_main_menu_keyboard()
        
        await update.message.reply_text(
            f"🎉 Ovoz sifatini baholadingiz: {status_text}\n\n"
            f"Rahmat! Boshqa ovozlarni ham tekshirib ko'ring.",
            reply_markup=reply_markup
        )
        
        # Clear user data
        context.user_data.clear()
        return ConversationHandler.END
        
    except BotServiceError as e:
        await update.message.reply_text(f"❌ {e.message}")
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Verification error: {e}")
        await update.message.reply_text("❌ Baholashda xatolik yuz berdi.")
        return ConversationHandler.END


async def cancel_checking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation"""
    context.user_data.clear()
    
    reply_markup = get_main_menu_keyboard()
    
    await update.message.reply_text(
        "❌ Audio tekshirish bekor qilindi.",
        reply_markup=reply_markup
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
        },
        fallbacks=[MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['CANCEL']}$"), cancel_checking)],
        allow_reentry=True
    )
    
    app.add_handler(check_audio_conv_handler)
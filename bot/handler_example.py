from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from app.core.logging import get_logger
import requests
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.services.user_service import get_user_by_telegramId
from app.schemas.user import UserCreate
from app.schemas.checked_audio import CheckedAudioCreate
import os
import tempfile
from app.config import settings
from app.services.bot_services import (
    bot_get_user_by_telegramId, 
    bot_get_available_sentence,
    bot_get_audio_for_checking,
    bot_create_checked_audio,
    BotServiceError
)

logger = get_logger("handlers")

# Conversation states
(REGISTRATION_NAME, REGISTRATION_AGE, REGISTRATION_GENDER, REGISTRATION_INFO,
 AWAITING_AUDIO, CHECKING_AUDIO) = range(6)

# API base URL
API_BASE = "http://localhost:8000"

async def get_db_session():
    """Get database session"""
    async with AsyncSessionLocal() as session:
        return session

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - check if user is registered"""
    user_telegram_id = str(update.effective_user.id)
    
    try:
        # Check if user exists using bot service
        async with AsyncSessionLocal() as db:
            user = await bot_get_user_by_telegramId(user_telegram_id, db)
            
        # User exists, show main menu
        keyboard = [
            [KeyboardButton("📝 Gap olish va ovoz yuborish")],
            [KeyboardButton("🎧 Audio tekshirish")],
            [KeyboardButton("📊 Statistika"), KeyboardButton("ℹ️ Ma'lumot")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            f"Salom {user.name}! 👋\n\n"
            "Siz allaqachon ro'yxatdan o'tgansiz. Quyidagi tugmalardan birini tanlang:",
            reply_markup=reply_markup
        )
        return ConversationHandler.END
        
    except BotServiceError as e:
        if e.error_type == "http_error" and "not found" in e.message.lower():
            # User doesn't exist, start registration
            await update.message.reply_text(
                "Assalomu alaykum! 👋 TTS-STT ma'lumotlar yig'ish botiga xush kelibsiz!\n\n"
                "Davom etish uchun ro'yxatdan o'tishingiz kerak.\n"
                "Ismingizni kiriting:"
            )
            return REGISTRATION_NAME
        else:
            await update.message.reply_text(f"❌ {e.message}")
            return ConversationHandler.END
    except Exception as e:
        logger.error(f"Start error: {e}")
        await update.message.reply_text("❌ Server bilan bog'lanishda xatolik.")
        return ConversationHandler.END

async def registration_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle name input during registration"""
    name = update.message.text.strip()
    
    if len(name) < 3 or len(name) > 100:
        await update.message.reply_text(
            "❌ Ism 3 dan 100 ta belgigacha bo'lishi kerak. Qaytadan kiriting:"
        )
        return REGISTRATION_NAME
    
    context.user_data['name'] = name
    await update.message.reply_text(
        f"Yaxshi, {name}! 👍\n\n"
        "Endi yoshingizni kiriting (faqat raqam):"
    )
    return REGISTRATION_AGE

async def registration_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle age input during registration"""
    try:
        age = int(update.message.text.strip())
        if age < 1 or age > 120:
            await update.message.reply_text(
                "❌ Yosh 1 dan 120 gacha bo'lishi kerak. Qaytadan kiriting:"
            )
            return REGISTRATION_AGE
    except ValueError:
        await update.message.reply_text(
            "❌ Faqat raqam kiriting. Qaytadan yoshingizni kiriting:"
        )
        return REGISTRATION_AGE
    
    context.user_data['age'] = age
    
    # Gender selection keyboard
    keyboard = [
        [KeyboardButton("Erkak"), KeyboardButton("Ayol")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(
        "Jinsingizni tanlang:",
        reply_markup=reply_markup
    )
    return REGISTRATION_GENDER

async def registration_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle gender selection during registration"""
    gender_text = update.message.text.strip()
    
    if gender_text == "Erkak":
        gender = "male"
    elif gender_text == "Ayol":
        gender = "female"
    else:
        keyboard = [
            [KeyboardButton("Erkak"), KeyboardButton("Ayol")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(
            "❌ Iltimos, tugmalardan birini tanlang:",
            reply_markup=reply_markup
        )
        return REGISTRATION_GENDER
    
    context.user_data['gender'] = gender
    
    # change keyboard
    keyboard = [
        [KeyboardButton("O'tkazib yuborish")],
    ]
    await update.message.reply_text(
        "O'zingiz haqingizda qisqacha ma'lumot bering (ixtiyoriy):",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return REGISTRATION_INFO

async def registration_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle info input and complete registration"""
    info = update.message.text.strip()
    
    if info == "O'tkazib yuborish":
        info = None
    elif len(info) > 500:
        await update.message.reply_text(
            "❌ Ma'lumot 500 belgidan oshmasligi kerak. Qaytadan kiriting yoki 'O'tkazib yuborish' yozing:"
        )
        return REGISTRATION_INFO
    
    # Register user via API
    user_data = UserCreate(
        name=context.user_data['name'],
        age=context.user_data['age'],
        gender=context.user_data['gender'],
        telegram_id=str(update.effective_user.id),
        info=info
    )
    
    try:
        response = requests.post(
            f"{API_BASE}/users/",
            json=user_data.model_dump()
        )
        
        if response.status_code == 200:
            user = response.json()
            
            # Show success message and main menu
            keyboard = [
                [KeyboardButton("📝 Gap olish va ovoz yuborish")],
                [KeyboardButton("🎧 Audio tekshirish")],
                [KeyboardButton("📊 Statistika"), KeyboardButton("ℹ️ Ma'lumot")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                f"✅ Ro'yxatdan o'tish muvaffaqiyatli yakunlandi!\n\n"
                f"Sizning ma'lumotlaringiz:\n"
                f"👤 Ism: {user['name']}\n"
                f"🎂 Yosh: {user['age']}\n"
                f"👫 Jins: {'Erkak' if user['gender'] == 'male' else 'Ayol'}\n\n"
                f"Quyidagi tugmalardan birini tanlang:",
                reply_markup=reply_markup
            )
            
            # Clear user data
            context.user_data.clear()
            return ConversationHandler.END
            
        else:
            await update.message.reply_text(
                "❌ Ro'yxatdan o'tishda xatolik yuz berdi. Qaytadan urinib ko'ring: /start"
            )
            return ConversationHandler.END
            
    except Exception as e:
        logger.error(f"Registration error: {e}")
        await update.message.reply_text(
            "❌ Server bilan bog'lanishda xatolik. Qaytadan urinib ko'ring: /start"
        )
        return ConversationHandler.END

async def get_sentence_and_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get sentence and handle audio upload"""
    user_telegram_id = str(update.effective_user.id)
    
    try:
        # Get user info using bot service
        async with AsyncSessionLocal() as db:
            user = await bot_get_user_by_telegramId(user_telegram_id, db)
            
        # Get sentence for user using bot service
        async with AsyncSessionLocal() as db:
            sentence = await bot_get_available_sentence(user.id, 0, db)  # sent_audio_count ni hisoblash kerak
            
        context.user_data['current_sentence'] = sentence
        context.user_data['user_id'] = user.id
        
        await update.message.reply_text(
            f"📝 Quyidagi gapni o'qib, ovoz yozib yuboring:\n\n"
            f"'{sentence.text}'\n\n"
            f"🎤 Ovoz xabar yuboring yoki /cancel tugmasini bosib bekor qiling."
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
        await update.message.reply_text(
            "❌ Iltimos, ovoz xabar yuboring yoki /cancel tugmasini bosing."
        )
        return AWAITING_AUDIO
    
    try:
        # Get audio file
        if update.message.voice:
            audio_file = await update.message.voice.get_file()
            file_extension = ".ogg"
        else:
            audio_file = await update.message.audio.get_file()
            file_extension = ".mp3"
        
        # Download to temporary file
        with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
            await audio_file.download_to_drive(temp_file.name)
            temp_file_path = temp_file.name
        
        # Upload to API
        with open(temp_file_path, 'rb') as f:
            files = {'file': f}
            data = {
                'user_id': context.user_data['user_id'],
                'sentence_id': context.user_data['current_sentence']['id']
            }
            
            response = requests.post(
                f"{API_BASE}/received-audio/",
                files=files,
                data=data
            )
        
        # Clean up temp file
        os.unlink(temp_file_path)
        
        if response.status_code == 200:
            await update.message.reply_text(
                "✅ Ovoz muvaffaqiyatli yuklandi va tekshirish uchun yuborildi!\n\n"
                "Yangi gap olish uchun '📝 Gap olish va ovoz yuborish' tugmasini bosing."
            )
        else:
            error_msg = response.json().get('detail', 'Yuklashda xatolik')
            await update.message.reply_text(f"❌ {error_msg}")
        
        # Clear user data
        context.user_data.clear()
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Audio upload error: {e}")
        await update.message.reply_text("❌ Ovoz yuklashda xatolik yuz berdi.")
        return ConversationHandler.END

async def get_audio_for_checking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get audio file for checking"""
    user_telegram_id = str(update.effective_user.id)
    
    try:
        # Get user info using bot service
        async with AsyncSessionLocal() as db:
            user = await bot_get_user_by_telegramId(user_telegram_id, db)
            
        # Get audio for checking using bot service
        async with AsyncSessionLocal() as db:
            audio_data = await bot_get_audio_for_checking(user.id, db)
            
        context.user_data['current_audio'] = audio_data
        context.user_data['user_id'] = user.id
        
        # Send audio file
        audio_url = f"{API_BASE}/{audio_data.audio_path}"
        
        keyboard = [
            [KeyboardButton("✅ To'g'ri"), KeyboardButton("❌ Noto'g'ri")],
            [KeyboardButton("🚫 Bekor qilish")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        
        await update.message.reply_text(
            f"🎧 Quyidagi audio faylni tinglang va to'g'riligini baholang:\n\n"
            f"Audio ID: {audio_data.id}"
        )
        
        # Send audio
        await update.message.reply_audio(
            audio=audio_url,
            caption="Bu audioda gap to'g'ri o'qilganmi?",
            reply_markup=reply_markup
        )
        
        return CHECKING_AUDIO
            
    except BotServiceError as e:
        await update.message.reply_text(f"❌ {e.message}")
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Get audio for checking error: {e}")
        await update.message.reply_text("❌ Server bilan bog'lanishda xatolik.")
        return ConversationHandler.END

async def handle_audio_verification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle audio verification result"""
    verification = update.message.text.strip()
    
    if verification == "🚫 Bekor qilish":
        await update.message.reply_text(
            "❌ Audio tekshirish bekor qilindi.",
            reply_markup=ReplyKeyboardRemove()
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    if verification == "✅ To'g'ri":
        is_correct = True
    elif verification == "❌ Noto'g'ri":
        is_correct = False
    else:
        keyboard = [
            [KeyboardButton("✅ To'g'ri"), KeyboardButton("❌ Noto'g'ri")],
            [KeyboardButton("🚫 Bekor qilish")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(
            "❌ Iltimos, tugmalardan birini tanlang:",
            reply_markup=reply_markup
        )
        return CHECKING_AUDIO
    
    try:
        # Submit verification result using bot service
        async with AsyncSessionLocal() as db:
            await bot_create_checked_audio(
                context.user_data['current_audio'].id,
                context.user_data['user_id'],
                is_correct,
                db
            )
        
        result_text = "to'g'ri" if is_correct else "noto'g'ri"
        await update.message.reply_text(
            f"✅ Audio '{result_text}' deb baholandi!\n\n"
            "Yangi audio tekshirish uchun '🎧 Audio tekshirish' tugmasini bosing.",
            reply_markup=ReplyKeyboardRemove()
        )
        
        # Clear user data
        context.user_data.clear()
        return ConversationHandler.END
        
    except BotServiceError as e:
        await update.message.reply_text(
            f"❌ {e.message}",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Audio verification error: {e}")
        await update.message.reply_text(
            "❌ Baholash natijasini yuborishda xatolik.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

async def get_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get and show statistics"""
    try:
        response = requests.get(f"{API_BASE}/statistic/statistic")
        
        if response.status_code == 200:
            stats = response.json()
            await update.message.reply_text(
                f"📊 **Statistika**\n\n"
                f"👥 Foydalanuvchilar: {stats['users']}\n"
                f"📝 Gaplar: {stats['sentences']}\n"
                f"🎤 Yuklangan audiolar: {stats['audios']}\n"
                f"✅ Tekshirilgan audiolar: {stats['checked_audios']}"
            )
        else:
            await update.message.reply_text("❌ Statistikani olishda xatolik.")
            
    except Exception as e:
        logger.error(f"Statistics error: {e}")
        await update.message.reply_text("❌ Server bilan bog'lanishda xatolik.")

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot information"""
    await update.message.reply_text(
        "ℹ️ **TTS-STT Ma'lumotlar Yig'ish Boti**\n\n"
        "Bu bot orqali siz:\n"
        "📝 Gaplarni o'qib ovoz yozib yuborishingiz\n"
        "🎧 Boshqa foydalanuvchilar yuborgan audiolarni tekshirishingiz mumkin\n\n"
        "Botdan foydalanish uchun avval ro'yxatdan o'ting.\n\n"
        "Yordam uchun: /help"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help information"""
    await update.message.reply_text(
        "🆘 **Yordam**\n\n"
        "**Asosiy buyruqlar:**\n"
        "/start - Botni ishga tushirish\n"
        "/help - Yordam ma'lumotlari\n"
        "/cancel - Joriy amalni bekor qilish\n\n"
        "**Asosiy funksiyalar:**\n"
        "📝 Gap olish va ovoz yuborish\n"
        "🎧 Audio tekshirish\n"
        "📊 Statistika\n"
        "ℹ️ Ma'lumot"
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation"""
    context.user_data.clear()
    
    keyboard = [
        [KeyboardButton("📝 Gap olish va ovoz yuborish")],
        [KeyboardButton("🎧 Audio tekshirish")],
        [KeyboardButton("📊 Statistika"), KeyboardButton("ℹ️ Ma'lumot")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "❌ Amal bekor qilindi.",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def handle_menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu button presses"""
    text = update.message.text
    
    if text == "📝 Gap olish va ovoz yuborish":
        return await get_sentence_and_audio(update, context)
    elif text == "🎧 Audio tekshirish":
        return await get_audio_for_checking(update, context)
    elif text == "📊 Statistika":
        await get_statistics(update, context)
    elif text == "ℹ️ Ma'lumot":
        await info(update, context)
    else:
        await update.message.reply_text("❌ Noma'lum buyruq. Tugmalardan foydalaning.")

def register_handlers(app: Application):
    """Register all bot handlers"""
    
    # Registration conversation handler
    registration_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            REGISTRATION_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, registration_name)],
            REGISTRATION_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, registration_age)],
            REGISTRATION_GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, registration_gender)],
            REGISTRATION_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, registration_info)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Audio upload conversation handler
    audio_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📝 Gap olish va ovoz yuborish$"), get_sentence_and_audio)],
        states={
            AWAITING_AUDIO: [MessageHandler(filters.VOICE | filters.AUDIO, handle_audio_upload)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Audio checking conversation handler
    checking_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🎧 Audio tekshirish$"), get_audio_for_checking)],
        states={
            CHECKING_AUDIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_audio_verification)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Add handlers
    app.add_handler(registration_conv_handler)
    app.add_handler(audio_conv_handler)
    app.add_handler(checking_conv_handler)
    
    # Simple command handlers
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("cancel", cancel))
    
    # Menu button handlers
    app.add_handler(MessageHandler(filters.Regex("^📊 Statistika$"), get_statistics))
    app.add_handler(MessageHandler(filters.Regex("^ℹ️ Ma'lumot$"), info))
    
    # Fallback for other text messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_buttons))
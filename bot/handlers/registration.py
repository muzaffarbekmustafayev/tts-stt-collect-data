from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from app.core.logging import get_logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.schemas.user import UserCreate
from app.schemas.checked_audio import CheckedAudioCreate
from app.config import settings
from app.core.logging import get_logger
from bot.services.user_services import get_user_by_telegramId, create_user
from bot.utils.keyboards import get_main_menu_keyboard, get_gender_keyboard, get_skip_keyboard
from bot.utils.validation import validate_name, validate_age, validate_info
from bot.utils.config import KEYBOARD_NAMES

logger = get_logger("bot")

# Conversation states
(REGISTRATION_NAME, REGISTRATION_AGE, REGISTRATION_GENDER, REGISTRATION_INFO,
 AWAITING_AUDIO, CHECKING_AUDIO) = range(6)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - check if user is registered"""
    user_telegram_id = str(update.effective_user.id)
    
    try:
        # Check if user exists using bot service
        async with AsyncSessionLocal() as db:
            user = await get_user_by_telegramId(user_telegram_id, db)
        
        if user:
            # User exists, show main menu
            reply_markup = get_main_menu_keyboard()
            await update.message.reply_text(
                f"Assalomu alaykum {user.name}! 👋\n\n"
                "Siz allaqachon ro'yxatdan o'tgansiz. Quyidagi tugmalardan birini tanlang:",
                reply_markup=reply_markup
            )
            return ConversationHandler.END
        
        # User doesn't exist, start registration
        await update.message.reply_text(
            "Assalomu alaykum! 👋 TTS-STT botimizga xush kelibsiz!\n\n"
            "Davom etish uchun ro'yxatdan o'tishingiz kerak.\n"
            "Ismingizni kiriting:"
        )
        return REGISTRATION_NAME
    
    except Exception as e:
        logger.error(f"Start error: {e}")
        await update.message.reply_text("❌ Server bilan bog'lanishda xatolik.")
        return ConversationHandler.END

async def registration_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle name input during registration"""
    name = update.message.text.strip()
    
    is_valid, error_message = validate_name(name)
    if not is_valid:
        await update.message.reply_text(
            error_message
        )
        return REGISTRATION_NAME
    
    context.user_data['name'] = name
    await update.message.reply_text(
        f"Yaxshi, {name}! 👍\n\n"
        "Endi yoshingizni kiriting (faqat raqam bilan \nmasalan: 20):"
    )
    return REGISTRATION_AGE

async def registration_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle age input during registration"""
    age_text = update.message.text.strip()
    is_valid, error_message, age = validate_age(age_text)
    if not is_valid:
        await update.message.reply_text(error_message)
        return REGISTRATION_AGE
    
    context.user_data['age'] = age
    
    # Gender selection keyboard
    reply_markup = get_gender_keyboard()
    
    await update.message.reply_text(
        "Jinsingizni tanlang:",
        reply_markup=reply_markup
    )
    return REGISTRATION_GENDER

async def registration_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle gender selection during registration"""
    gender_text = update.message.text.strip()
    
    if gender_text == KEYBOARD_NAMES["MALE"]:
        gender = "Male"
    elif gender_text == KEYBOARD_NAMES["FEMALE"]:
        gender = "Female"
    else:
        keyboard = get_gender_keyboard()
        await update.message.reply_text(
            "❌ Iltimos, tugmalardan birini tanlang:",
            reply_markup=keyboard
        )
        return REGISTRATION_GENDER
    
    context.user_data['gender'] = gender
    
    # change keyboard
    await update.message.reply_text(
        "O'zingiz haqingizda qisqacha ma'lumot bering (ixtiyoriy):",
        reply_markup=get_skip_keyboard()
    )
    return REGISTRATION_INFO

async def registration_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle info input and complete registration"""
    info = update.message.text.strip()
    
    if info == KEYBOARD_NAMES["SKIP"]:
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
    async with AsyncSessionLocal() as db:
        user = await create_user(user_data, db)
    
    try:
        if user:
            # Show success message and main menu
            reply_markup = get_main_menu_keyboard()
            await update.message.reply_text(
                f"✅ Ro'yxatdan o'tish muvaffaqiyatli yakunlandi!\n\n"
                f"Sizning ma'lumotlaringiz:\n"
                f"👤 Ism: {user.name}\n"
                f"🎂 Yosh: {user.age}\n"
                f"👫 Jins: {'Erkak' if user.gender == 'Male' else 'Ayol'}\n\n"
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

async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation"""
    context.user_data.clear()
    
    await update.message.reply_text(
        "❌ Amal bekor qilindi.\n\n"
        "Qaytadan urinib ko'ring: /start",
    )
    return ConversationHandler.END



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
        fallbacks=[
            CommandHandler("cancel", cancel_registration), 
            CommandHandler("start", start)
        ],
        allow_reentry=True
    )
    
    # Add handlers
    app.add_handler(registration_conv_handler)
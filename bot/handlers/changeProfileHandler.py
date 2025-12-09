from telegram import Update
from bot.utils.config import KEYBOARD_NAMES
from telegram.ext import Application, ContextTypes, ConversationHandler, MessageHandler, filters, CommandHandler
from app.services.user_service import get_user_by_telegramId
from app.db.session import AsyncSessionLocal
from bot.utils.keyboards import get_main_menu_keyboard, select_btn_to_change_data, get_gender_keyboard
from app.core.logging import get_logger
from fastapi import HTTPException
from app.services.user_service import update_user

logger = get_logger("handlers")

async def show_profile_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get sentence and handle audio upload"""
    try:
        user_telegram_id = str(update.effective_user.id)
        async with AsyncSessionLocal() as db:
            user = await get_user_by_telegramId(user_telegram_id, db)
        if not user:
            await update.message.reply_text("❌ Foydalanuvchi topilmadi. Iltimos, /start buyrug'ini yuboring.")
            return
        context.user_data['user_data'] = user

        await update.message.reply_text(f"📊 Profil ma'lumotlari:\n\n"
            f"telegram idsi: {user_telegram_id}\n"
            f"ismi: {user.name}\n"
            f"yoshi: {user.age}\n"
            f"jinsi: {'Erkak' if user.gender.lower() == 'male' else 'Ayol'}\n"
            f"qo'shimcha ma'lumot: {"" if not user.info else user.info} \n",
            reply_markup=select_btn_to_change_data()
        )
        return SELECT_DATA_TO_CHANGE
    except HTTPException as e:
        await update.message.reply_text(f"❌ {e.message}", reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Statistics error: {e}")
        await update.message.reply_text("❌ Profil ma'lumotlarini o'zgartirishda xatolik yuz berdi.", reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END


async def change_data_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Change name text"""
    try:
        if update.message.text.strip() == KEYBOARD_NAMES['CHANGE_NAME']:
            context.user_data['current_changing_data'] = 'name'
            await update.message.reply_text("Yangi ism kiriting (3-100 ta belgidan iborat):")
            return CHANGE_DATA
        elif update.message.text.strip() == KEYBOARD_NAMES['CHANGE_AGE']:
            context.user_data['current_changing_data'] = 'age'
            await update.message.reply_text("Yoshingizni kiriting (1-120 ta belgidan iborat):")
            return CHANGE_DATA
        elif update.message.text.strip() == KEYBOARD_NAMES['CHANGE_INFO_TEXT']:
            context.user_data['current_changing_data'] = 'info'
            await update.message.reply_text("Qo'shimcha ma'lumotingizni kiriting (500 ta belgidan oshmasligi kerak):")
            return CHANGE_DATA
        elif update.message.text.strip() == KEYBOARD_NAMES['CHANGE_GENDER']:
            context.user_data['current_changing_data'] = 'gender'
            await update.message.reply_text("Jinsingizni tanlang:", reply_markup=get_gender_keyboard())
            return CHANGE_DATA
        else:
            await update.message.reply_text("❌ Iltimos, quyidagi tugmalardan birini tanlang:", reply_markup=select_btn_to_change_data())
            return SELECT_DATA_TO_CHANGE
    except HTTPException as e:
        await update.message.reply_text(f"❌ {e.message}", reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Statistics error: {e}")
        await update.message.reply_text("❌ Profil ma'lumotlarini o'zgartirishda xatolik yuz berdi.", reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END


async def handle_data_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle data change"""
    try:
        data = update.message.text.strip()
        current_changing_data = context.user_data['current_changing_data']
        user_data = context.user_data['user_data']
        if current_changing_data == 'name':
            if len(data) < 3 or len(data) > 100:
                await update.message.reply_text("❌ Iltimos, ism 3-100 ta belgidan iborat bo'lishi kerak.")
                return CHANGE_DATA
            user_data.name = data
        elif current_changing_data == 'age':
            try:
                user_data.age = int(data)
            except ValueError:
                await update.message.reply_text("❌ Iltimos, raqam kiriting.")
                return CHANGE_DATA
            if user_data.age < 1 or user_data.age > 120:
                await update.message.reply_text("❌ Iltimos, yosh 1 dan 120 gacha bo'lishi kerak.")
                return CHANGE_DATA
        elif current_changing_data == 'info':
            if len(data) > 500:
                await update.message.reply_text("❌ Iltimos, ma'lumot 500 ta belgidan oshmasligi kerak.")
                return CHANGE_DATA
            user_data.info = data
        elif current_changing_data == 'gender':
            if data == KEYBOARD_NAMES['MALE'] or data == KEYBOARD_NAMES['FEMALE']:
                user_data.gender = "Male" if data == KEYBOARD_NAMES['MALE'] else "Female"
            else:
                await update.message.reply_text("❌ Iltimos, quyidagi tugmalardan birini tanlang:", reply_markup=get_gender_keyboard())
                return CHANGE_DATA
        async with AsyncSessionLocal() as db:
            await update_user(user_data.id, user_data, db)
        await update.message.reply_text(f"📊 Profil ma'lumotlarini o'zgartirildi:\n\n"
            f"telegram idsi: {user_data.telegram_id}\n"
            f"ismi: {user_data.name}\n"
            f"yoshi: {user_data.age}\n"
            f"jinsi: {'Erkak' if user_data.gender.lower() == 'male' else 'Ayol'}\n"
            f"qo'shimcha ma'lumot: {"" if not user_data.info else user_data.info} \n",
            reply_markup=select_btn_to_change_data()
        )
        context.user_data['current_changing_data'] = None
        return SELECT_DATA_TO_CHANGE
    except HTTPException as e:
        await update.message.reply_text(f"❌ {e.message}", reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Statistics error: {e}")
        await update.message.reply_text("❌ Profil ma'lumotlarini o'zgartirishda xatolik yuz berdi.", reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END



async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Back to menu"""
    context.user_data.clear()    
    await update.message.reply_text(
        "O'zgartirish bekor qilindi.", reply_markup=select_btn_to_change_data()
    )
    return SELECT_DATA_TO_CHANGE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation"""
    context.user_data.clear()    
    await update.message.reply_text(
        "Bosh menu.",
        reply_markup=get_main_menu_keyboard()
    )
    return ConversationHandler.END


SELECT_DATA_TO_CHANGE = 1
CHANGE_DATA = 2

def change_profile_handler(app: Application):
    """change profile handler"""
    change_profile_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(KEYBOARD_NAMES['CHANGE_INFO']), show_profile_data)],
        states={
            SELECT_DATA_TO_CHANGE: [
                MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['FINISH']}$"), cancel),
                MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['CHANGE_NAME']}$"), change_data_text),
                MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['CHANGE_AGE']}$"), change_data_text),
                MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['CHANGE_INFO_TEXT']}$"), change_data_text),
                MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['CHANGE_GENDER']}$"), change_data_text),
            ],
            CHANGE_DATA: [
                MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['CANCEL']}$"), back_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_data_change),
            ]
        },
        fallbacks=[MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['CANCEL']}$"), cancel)],
        allow_reentry=True
    )
    
    
    app.add_handler(change_profile_handler)
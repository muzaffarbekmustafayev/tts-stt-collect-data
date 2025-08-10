"""
Bot utility functions for common operations
"""
from telegram import ReplyKeyboardMarkup, KeyboardButton
from app.core.logging import get_logger

logger = get_logger("bot.utils")

def get_main_menu_keyboard():
    """Get main menu keyboard markup"""
    keyboard = [
        [KeyboardButton("📝 Gap olish va ovoz yuborish")],
        [KeyboardButton("🎧 Audio tekshirish")],
        [KeyboardButton("📊 Statistika"), KeyboardButton("ℹ️ Ma'lumot")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_gender_keyboard():
    """Get gender selection keyboard"""
    keyboard = [
        [KeyboardButton("Erkak"), KeyboardButton("Ayol")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_verification_keyboard():
    """Get audio verification keyboard"""
    keyboard = [
        [KeyboardButton("✅ To'g'ri"), KeyboardButton("❌ Noto'g'ri")],
        [KeyboardButton("🚫 Bekor qilish")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def format_user_info(user_data):
    """Format user information for display"""
    gender_text = "Erkak" if user_data.get('gender') == 'male' else "Ayol"
    return (
        f"👤 Ism: {user_data.get('name')}\n"
        f"🎂 Yosh: {user_data.get('age')}\n"
        f"👫 Jins: {gender_text}"
    )

def validate_name(name):
    """Validate user name input"""
    if not name or len(name.strip()) < 3 or len(name.strip()) > 100:
        return False, "❌ Ism 3 dan 100 ta belgigacha bo'lishi kerak. Qaytadan kiriting:"
    return True, ""

def validate_age(age_text):
    """Validate user age input"""
    try:
        age = int(age_text.strip())
        if age < 1 or age > 120:
            return False, "❌ Yosh 1 dan 120 gacha bo'lishi kerak. Qaytadan kiriting:", None
        return True, "", age
    except ValueError:
        return False, "❌ Faqat raqam kiriting. Qaytadan yoshingizni kiriting:", None

def validate_info(info_text):
    """Validate user info input"""
    if info_text == "0":
        return True, "", None
    elif len(info_text) > 500:
        return False, "❌ Ma'lumot 500 belgidan oshmasligi kerak. Qaytadan kiriting yoki '0' yozing:", None
    return True, "", info_text

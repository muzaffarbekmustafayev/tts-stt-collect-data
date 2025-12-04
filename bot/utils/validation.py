"""
Bot utility functions for common operations
"""
from app.core.logging import get_logger

logger = get_logger("bot.utils")


def validate_name(name):
    """Validate user name input"""
    if not name or len(name.strip()) < 2 or len(name.strip()) > 120:
        return False, "❌ Ism 2 dan 120 ta belgigacha bo'lishi kerak. Qaytadan kiriting:"
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

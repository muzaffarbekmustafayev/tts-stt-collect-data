from telegram import ReplyKeyboardMarkup, KeyboardButton
from bot.utils.config import KEYBOARD_NAMES

def get_main_menu_keyboard():
    """Get main menu keyboard markup"""
    keyboard = [
        [KeyboardButton(KEYBOARD_NAMES["SEND_AUDIO"])],
        [KeyboardButton(KEYBOARD_NAMES["CHECK_AUDIO"])],
        [KeyboardButton(KEYBOARD_NAMES["STATISTICS"]), KeyboardButton(KEYBOARD_NAMES["INFO"])]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_gender_keyboard():
    """Get gender selection keyboard"""
    keyboard = [
        [KeyboardButton(KEYBOARD_NAMES["MALE"]), KeyboardButton(KEYBOARD_NAMES["FEMALE"])]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_verification_keyboard():
    """Get audio verification keyboard"""
    keyboard = [
        [KeyboardButton(KEYBOARD_NAMES["INCORRECT"]), KeyboardButton(KEYBOARD_NAMES["CORRECT"])]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_cancel_keyboard():
    """Get cancel keyboard"""
    keyboard = [
        [KeyboardButton(KEYBOARD_NAMES["CANCEL"])]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_back_to_menu_keyboard():
    """Get cancel keyboard"""
    keyboard = [
        [KeyboardButton(KEYBOARD_NAMES["BACK_TO_MENU"])]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_skip_keyboard():
    """Get skip keyboard"""
    keyboard = [
        [KeyboardButton(KEYBOARD_NAMES["SKIP"])]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_confirmation_keyboard():
    """Get confirmation keyboard"""
    keyboard = [
        [KeyboardButton(KEYBOARD_NAMES["CANCEL"]), KeyboardButton(KEYBOARD_NAMES["CONFIRMATION"])]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_confirmation_or_retry_keyboard():
    """Get confirmation keyboard"""
    keyboard = [
        [
            KeyboardButton(KEYBOARD_NAMES["RETRY_RECORDING"]), KeyboardButton(KEYBOARD_NAMES["CONFIRMATION"])]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
def get_next_or_finish_keyboard():
    """Get next or finish keyboard"""
    keyboard = [
        [
            KeyboardButton(KEYBOARD_NAMES["FINISH"]),
            KeyboardButton(KEYBOARD_NAMES["NEXT"])
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

from telegram import Update
from telegram.ext import Application, ContextTypes, ConversationHandler, MessageHandler, filters
from app.core.logging import get_logger
from app.services.user_service import get_user_statistic, check_user_sent_audio_over_limit
from app.services.received_audio_services import get_audio_by_user_id_and_sentence_id, update_received_audio_path_status
from app.services.bot_services import bot_get_available_sentence, BotServiceError
from app.api.received_audio import ensure_directories_exist, UPLOAD_DIR
from bot.utils.keyboards import (
    get_main_menu_keyboard, get_confirmation_or_retry_keyboard,
    get_next_or_finish_keyboard, get_back_to_menu_keyboard
)
from bot.utils.config import KEYBOARD_NAMES
from bot.services.user_services import get_user_by_telegramId
import asyncio, os, uuid

logger = get_logger("handlers")

AWAITING_AUDIO = 1
CONFIRMATION = 2
NEXT_OR_FINISH = 3


async def get_sentence_and_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_telegram_id = str(update.effective_user.id)

    try:
        user = await get_user_by_telegramId(user_telegram_id)
        if not user:
            await update.message.reply_text(
                "❌ Foydalanuvchi topilmadi. /start buyrug'ini yuboring.",
                reply_markup=get_main_menu_keyboard()
            )
            return ConversationHandler.END

        sent_count = await check_user_sent_audio_over_limit(user.id)
        sentence = await bot_get_available_sentence(user.id, sent_count)

        context.user_data['current_sentence'] = sentence
        context.user_data['user_id'] = user.id

        await update.message.reply_text(
            f"📝 Quyidagi gapni o'qing va ovozli xabar yuborin:\n\n"
            f"<b><i>{sentence.text}</i></b>",
            reply_markup=get_back_to_menu_keyboard(),
            parse_mode="HTML"
        )
        return AWAITING_AUDIO

    except BotServiceError as e:
        msg = e.message
        if "limit" in msg.lower():
            msg = "✅ Siz barcha mavjud gaplarni o'qib bo'ldingiz! Keyinroq yangi gaplar qo'shiladi."
        elif "no available" in msg.lower() or "topilmadi" in msg.lower():
            msg = "📭 Hozircha yangi gap mavjud emas. Keyinroq qaytib keling!"
        await update.message.reply_text(msg, reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"get_sentence_and_audio error: {e}", exc_info=True)
        await update.message.reply_text("❌ Server bilan bog'lanishda xatolik.", reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END


async def handle_audio_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.voice and not update.message.audio:
        await update.message.reply_text(
            f"❌ Iltimos, ovozli xabar yuboring.",
            reply_markup=get_back_to_menu_keyboard()
        )
        return AWAITING_AUDIO

    try:
        ensure_directories_exist()
        processing_msg = await update.message.reply_text("⏳ Audio yuklanmoqda...")

        if update.message.voice:
            audio_file = await update.message.voice.get_file()
            ext = "ogg"
            context.user_data['duration'] = update.message.voice.duration
        else:
            audio_file = await update.message.audio.get_file()
            ext = os.path.splitext(update.message.audio.file_name or "audio.ogg")[1].lstrip(".") or "ogg"
            context.user_data['duration'] = update.message.audio.duration

        user_id = context.user_data['user_id']
        sentence_id = context.user_data['current_sentence'].id

        received_audio = await get_audio_by_user_id_and_sentence_id(user_id, sentence_id)

        file_name = f"{uuid.uuid4()}.{ext}"
        audio_path = os.path.join(UPLOAD_DIR, file_name)

        try:
            await asyncio.wait_for(audio_file.download_to_drive(audio_path), timeout=60.0)
        except asyncio.TimeoutError:
            await processing_msg.delete()
            await update.message.reply_text(
                "❌ Yuklash vaqti tugadi. Kichikroq fayl yuboring.",
                reply_markup=get_back_to_menu_keyboard()
            )
            return AWAITING_AUDIO

        context.user_data['relative_path'] = f"audio/{file_name}"
        context.user_data['audio_path'] = audio_path
        context.user_data['received_audio_id'] = received_audio.id

        await processing_msg.delete()
        await update.message.reply_text(
            "✅ Audio yuklandi! Tasdiqlaysizmi?",
            reply_markup=get_confirmation_or_retry_keyboard()
        )
        return CONFIRMATION

    except Exception as e:
        logger.error(f"Audio upload error: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Audio yuklashda xatolik. Qaytadan urinib ko'ring.",
            reply_markup=get_back_to_menu_keyboard()
        )
        return AWAITING_AUDIO


async def handle_audio_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text not in [KEYBOARD_NAMES["RETRY_RECORDING"], KEYBOARD_NAMES["CONFIRMATION"]]:
        await update.message.reply_text(
            "❌ Tugmalardan birini tanlang:",
            reply_markup=get_confirmation_or_retry_keyboard()
        )
        return CONFIRMATION

    if text == KEYBOARD_NAMES["RETRY_RECORDING"]:
        path = context.user_data.get('audio_path')
        if path and os.path.exists(path):
            os.remove(path)
        await update.message.reply_text(
            f"🔄 Qaytadan yozing:\n\n<b><i>{context.user_data['current_sentence'].text}</i></b>",
            reply_markup=get_back_to_menu_keyboard(),
            parse_mode="HTML"
        )
        return AWAITING_AUDIO

    # Confirm
    await update_received_audio_path_status(
        context.user_data['received_audio_id'],
        context.user_data['relative_path'],
        context.user_data.get('duration', 0)
    )
    await update.message.reply_text("✅ Ovoz muvaffaqiyatli saqlandi!", reply_markup=get_next_or_finish_keyboard())
    return NEXT_OR_FINISH


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Bosh menu.", reply_markup=get_main_menu_keyboard())
    return ConversationHandler.END


async def handle_finish_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    try:
        stats = await get_user_statistic(str(update.effective_user.id))
        _, sent_count, _, _, _ = stats
        await update.message.reply_text(
            f"✅ Yakunlandi! Yuborgan ovozlaringiz: {sent_count} ta.\n"
            f"Yana yuborish uchun '{KEYBOARD_NAMES['SEND_AUDIO']}' ni bosing.",
            reply_markup=get_main_menu_keyboard()
        )
    except Exception:
        await update.message.reply_text("✅ Ovoz muvaffaqiyatli saqlandi!", reply_markup=get_main_menu_keyboard())
    return ConversationHandler.END


def get_audio_handler(app: Application):
    handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(KEYBOARD_NAMES['SEND_AUDIO']), get_sentence_and_audio)],
        states={
            AWAITING_AUDIO: [
                MessageHandler(filters.VOICE | filters.AUDIO, handle_audio_upload),
                MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['BACK_TO_MENU']}$"), cancel),
            ],
            CONFIRMATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_audio_confirmation),
            ],
            NEXT_OR_FINISH: [
                MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['NEXT']}$"), get_sentence_and_audio),
                MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['FINISH']}$"), handle_finish_audio),
            ],
        },
        fallbacks=[MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['CANCEL']}$"), cancel)],
        allow_reentry=True
    )
    app.add_handler(handler)

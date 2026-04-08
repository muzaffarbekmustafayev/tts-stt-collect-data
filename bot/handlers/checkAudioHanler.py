from telegram import Update
from telegram.ext import Application, ContextTypes, ConversationHandler, MessageHandler, filters
from app.core.logging import get_logger
from app.services.user_service import get_user_statistic

from bot.utils.keyboards import get_main_menu_keyboard, get_verification_keyboard, get_next_or_finish_keyboard
from bot.utils.config import KEYBOARD_NAMES
from bot.services.user_services import get_user_by_telegramId
from app.services.bot_services import bot_get_audio_for_checking, bot_create_checked_audio, BotServiceError

logger = get_logger("handlers")

AWAITING_VERIFICATION = 1
NEXT_OR_FINISH = 2


async def get_audio_for_checking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_telegram_id = str(update.effective_user.id)

    try:
        user = await get_user_by_telegramId(user_telegram_id)
        if not user:
            await update.message.reply_text(
                "❌ Foydalanuvchi topilmadi. /start buyrug'ini yuboring.",
                reply_markup=get_main_menu_keyboard()
            )
            return ConversationHandler.END

        received_audio = await bot_get_audio_for_checking(user.id)

        # fetch_links=True bilan qaytgan, sentence va user mavjud
        sentence_text = received_audio.sentence.text if received_audio.sentence else "Matn topilmadi"

        context.user_data['current_audio'] = received_audio
        context.user_data['user_id'] = user.id

        await update.message.reply_text(
            f"🎧 Quyidagi ovozni tinglab, sifatini baholang:\n\n"
            f"📝 Matn: <b><i>{sentence_text}</i></b>\n\n"
            f"🎤 Ovoz yuklanmoqda...",
            reply_markup=get_verification_keyboard(),
            parse_mode="HTML"
        )

        if received_audio.audio_path:
            audio_path = f"media/{received_audio.audio_path}"
            caption = f"📝 <b><i>{sentence_text}</i></b>"
            try:
                with open(audio_path, 'rb') as f:
                    await update.message.reply_voice(voice=f, caption=caption, parse_mode="HTML")
            except FileNotFoundError:
                await update.message.reply_text("⚠️ Audio fayl topilmadi, lekin baholashingiz mumkin.")
            except Exception as e:
                logger.error(f"Audio send error: {e}")
                await update.message.reply_text("⚠️ Audio yuborishda xatolik.")

        return AWAITING_VERIFICATION

    except BotServiceError as e:
        msg = e.message
        if "no available" in msg.lower() or "topilmadi" in msg.lower() or "404" in msg.lower():
            msg = "📭 Hozircha tekshirish uchun ovoz mavjud emas. Keyinroq qaytib keling!"
        elif "limit" in msg.lower():
            msg = "✅ Siz belgilangan limitdagi barcha ovozlarni tekshirdingiz!"
        await update.message.reply_text(msg, reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"get_audio_for_checking error: {e}", exc_info=True)
        await update.message.reply_text("❌ Server bilan bog'lanishda xatolik.", reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END


async def handle_verification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text not in [KEYBOARD_NAMES["CORRECT"], KEYBOARD_NAMES["INCORRECT"]]:
        await update.message.reply_text(
            "❌ Iltimos, quyidagi tugmalardan birini tanlang:",
            reply_markup=get_verification_keyboard()
        )
        return AWAITING_VERIFICATION

    try:
        is_correct = text == KEYBOARD_NAMES["CORRECT"]
        user_id = context.user_data['user_id']
        received_audio = context.user_data['current_audio']

        await bot_create_checked_audio(received_audio.id, user_id, is_correct)

        await update.message.reply_text(
            "✅ Baholaganingiz uchun rahmat!",
            reply_markup=get_next_or_finish_keyboard()
        )
        return NEXT_OR_FINISH

    except BotServiceError as e:
        logger.error(f"Verification BotServiceError: {e.message}")
        await update.message.reply_text(f"❌ {e.message}", reply_markup=get_main_menu_keyboard())
        context.user_data.clear()
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Verification error: {e}", exc_info=True)
        await update.message.reply_text("❌ Baholashda xatolik yuz berdi.", reply_markup=get_main_menu_keyboard())
        context.user_data.clear()
        return ConversationHandler.END


async def cancel_checking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Bosh menu.", reply_markup=get_main_menu_keyboard())
    return ConversationHandler.END


async def handle_finish_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    try:
        stats = await get_user_statistic(str(update.effective_user.id))
        _, _, _, checked_count, _ = stats
        await update.message.reply_text(
            f"✅ Yakunlandi! Tekshirgan ovozlaringiz: {checked_count} ta.\n"
            f"Yana tekshirish uchun '{KEYBOARD_NAMES['CHECK_AUDIO']}' ni bosing.",
            reply_markup=get_main_menu_keyboard()
        )
    except Exception:
        await update.message.reply_text("✅ Baholash yakunlandi!", reply_markup=get_main_menu_keyboard())
    return ConversationHandler.END


def check_audio_handler(app: Application):
    handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['CHECK_AUDIO']}$"), get_audio_for_checking)],
        states={
            AWAITING_VERIFICATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_verification)
            ],
            NEXT_OR_FINISH: [
                MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['NEXT']}$"), get_audio_for_checking),
                MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['FINISH']}$"), handle_finish_audio),
            ],
        },
        fallbacks=[MessageHandler(filters.Regex(f"^{KEYBOARD_NAMES['CANCEL']}$"), cancel_checking)],
        allow_reentry=True
    )
    app.add_handler(handler)

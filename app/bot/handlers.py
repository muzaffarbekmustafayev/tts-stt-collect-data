from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from app.core.logging import get_logger

logger = get_logger("handlers")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salom! Gap yuboraman, ovoz yozib qaytaring 🎤")

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot haqida ma'lumot")

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot haqida ma'lumot")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    await update.message.reply_text("Sizning xabaringiz: " + update.message.text)

def register_handlers(app: Application):
    logger.info("Registering bot handlers")
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(MessageHandler(filters.TEXT, handle_text))

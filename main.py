from fastapi import FastAPI
from app.api import user, sentence, received_audio, checked_audio, statistic, admin
from app.core.logging import setup_logging, get_logger
from fastapi.staticfiles import StaticFiles
from app.config import AUDIO_DIR
from contextlib import asynccontextmanager
import asyncio
from bot.main_bot import create_bot_application

# Setup logging
setup_logging()
logger = get_logger("main")

# FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code here
    logger.info("Starting the application")
    asyncio.create_task(run_bot())
    yield
    # Shutdown code here
    global bot_application
    if bot_application:
        logger.info("Stopping the bot")
        await bot_application.updater.stop()
        await bot_application.stop()
        await bot_application.shutdown()
        logger.info("Bot stopped")

app = FastAPI(title="TTS-STT data collection api", lifespan=lifespan)

# Mount static files
app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")

app.include_router(user.router)
app.include_router(sentence.router)
app.include_router(received_audio.router)
app.include_router(checked_audio.router)
app.include_router(statistic.router)
# app.include_router(admin.router)

@app.get("/")
async def root():
    return {"message": "Hello, TTS World!"}



# Bot application instance
bot_application = None

async def run_bot():
    """Run the telegram bot in the background"""
    global bot_application
    try:
        bot_application = create_bot_application()
        await bot_application.initialize()
        await bot_application.start()
        await bot_application.updater.start_polling()
        logger.info("Bot started successfully")
        
        # Keep the bot running
        while True:
            await asyncio.sleep(1)
            
    except asyncio.CancelledError:
        logger.info("Bot task cancelled")
    except Exception as e:
        logger.error(f"Error in bot: {str(e)}")
        raise e
    finally:
        if bot_application:
            await bot_application.updater.stop()
            await bot_application.stop()
            await bot_application.shutdown()
            logger.info("Bot stopped")

# Main entry point
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting uvicorn server")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="debug")
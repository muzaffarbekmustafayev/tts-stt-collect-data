from fastapi import FastAPI
from app.api import user, sentence, received_audio, checked_audio, statistic    
from app.bot.bot import run_bot, bot_application
from app.core.logging import setup_logging, get_logger
import asyncio
import os
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from app.config import AUDIO_DIR

# Setup logging
setup_logging()
logger = get_logger("main")

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

app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")

app.include_router(user.router)
app.include_router(sentence.router)
app.include_router(received_audio.router)
app.include_router(checked_audio.router)
app.include_router(statistic.router)

@app.get("/")
async def root():
    return {"message": "Hello, TTS World!"}


# Main entry point
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting uvicorn server")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="debug")
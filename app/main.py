from fastapi import FastAPI
from app.api import user, sentence, received_audio, checked_audio
from app.api import upload
from app.bot.bot import run_bot
from app.core.logging import setup_logging, get_logger
import asyncio

# Setup logging
setup_logging()
logger = get_logger("main")

app = FastAPI(title="TTS-STT data collection api")

app.include_router(user.router)
app.include_router(sentence.router)
app.include_router(received_audio.router)
app.include_router(checked_audio.router)
app.include_router(upload.router)

@app.get("/")
async def root():
    return {"message": "Hello, TTS World!"}

@app.on_event("startup")
async def startup_event():
    logger.info("Starting FastAPI application")
    asyncio.create_task(run_bot())  
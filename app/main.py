from fastapi import FastAPI
from app.api import user, sentence, received_audio, checked_audio, statistic    
from app.bot.bot import run_bot
from app.core.logging import setup_logging, get_logger
import asyncio
import os
from fastapi.staticfiles import StaticFiles
from app.config import AUDIO_DIR

# Setup logging
setup_logging()
logger = get_logger("main")

app = FastAPI(title="TTS-STT data collection api")

app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")

app.include_router(user.router)
app.include_router(sentence.router)
app.include_router(received_audio.router)
app.include_router(checked_audio.router)
app.include_router(statistic.router)

@app.get("/")
async def root():
    return {"message": "Hello, TTS World!"}

@app.on_event("startup")
async def startup_event():
    logger.info("Starting FastAPI application")
    asyncio.create_task(run_bot())  
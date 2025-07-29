from fastapi import FastAPI
from app.api import user, sentence, received_audio, checked_audio
from os import getenv

app = FastAPI(title=getenv("PROJECT_NAME"))

app.include_router(user.router)
app.include_router(sentence.router)
app.include_router(received_audio.router)
app.include_router(checked_audio.router)

@app.get("/")
async def root():
    return {"message": "Hello, TTS World!"}

from fastapi import FastAPI, HTTPException
from app.api import user, sentence, received_audio, second_check, checked_audio, statistic, admin, auth
from app.core.logging import setup_logging, get_logger
from fastapi.responses import FileResponse
from app.config import AUDIO_DIR
from app.db.session import init_db, close_db
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime, timezone
UTC = timezone.utc
from telegram import Update
from bot.main_bot import create_bot_application
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time
import os

# Setup logging
setup_logging()
logger = get_logger("main")

# Request logging middleware
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")
        logger.debug(f"Headers: {dict(request.headers)}")
        
        # Log request body for debugging
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            if body:
                try:
                    logger.debug(f"Body: {body.decode('utf-8')}")
                except:
                    logger.debug(f"Body (binary): {len(body)} bytes")
            # Important: recreate request with body
            async def receive():
                return {"type": "http.request", "body": body}
            request._receive = receive
        
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(f"Response: {response.status_code} - {process_time:.3f}s")
        
        return response

# Bot application instance
bot_application = None
bot_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global bot_task
    
    # Startup
    logger.info("Starting the application")
    try:
        await init_db()
        logger.info("Database initialized successfully")
        
        # Start bot in background
        bot_task = asyncio.create_task(run_bot())
        logger.info("Bot task created")
        
        yield
        
    finally:
        # Shutdown
        logger.info("Shutting down the application")
        
        # Stop bot
        if bot_task and not bot_task.done():
            bot_task.cancel()
            try:
                await bot_task
            except asyncio.CancelledError:
                logger.info("Bot task cancelled successfully")
        
        global bot_application
        if bot_application:
            try:
                await bot_application.updater.stop()
                await bot_application.stop()
                await bot_application.shutdown()
                logger.info("Bot stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping bot: {str(e)}")
        
        # Close database connection
        await close_db()
        logger.info("Application shutdown complete")

app = FastAPI(
    title="TTS-STT Data Collection API", 
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    redirect_slashes=True  # Trailing slash'ni avtomatik redirect qiladi
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

origins = [
    "https://tts-stt-collect-data-admin-panel-cyy0et0co.vercel.app",
    "https://tts-stt-collect-data-admin-panel.vercel.app",
    "https://tts-stt.uz",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "*",  # Development uchun - production'da olib tashlang
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Development uchun - barcha origin'larga ruxsat
    allow_credentials=True,
    allow_methods=["*"],  # Barcha metodlarga ruxsat
    allow_headers=["*"],  # Barcha header'larga ruxsat
    expose_headers=["*"],
)

# Audio file endpoint with better error handling
from fastapi import Response
from fastapi.responses import FileResponse
import os

@app.get("/audio/{filename}")
async def serve_audio(filename: str):
    """Serve audio files with proper error handling"""
    file_path = os.path.join(AUDIO_DIR, filename)
    
    if not os.path.exists(file_path):
        logger.warning(f"Audio file not found: {filename} (path: {file_path})")
        raise HTTPException(
            status_code=404, 
            detail={
                "error": "Audio file not found",
                "filename": filename,
                "message": "The audio file may have been deleted or never uploaded"
            }
        )
    
    return FileResponse(
        file_path,
        media_type="audio/ogg",
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=3600"
        }
    )

# Include routers
app.include_router(user.router)
app.include_router(sentence.router)
app.include_router(received_audio.router)
app.include_router(checked_audio.router)
app.include_router(second_check.router)
app.include_router(statistic.router)
app.include_router(admin.router)
app.include_router(auth.router)

@app.get("/")
async def root():
    return {"message": "Hello, TTS World!"}

@app.get("/ping")
async def ping():
    """Simple ping endpoint for connectivity test"""
    return {"status": "ok", "message": "pong"}

@app.options("/{path:path}")
async def options_handler(path: str):
    """Handle OPTIONS requests for CORS preflight"""
    return {"status": "ok"}

@app.get("/health")
async def health_check():
    """Detailed health check endpoint"""
    from app.db.session import get_client
    
    health_status = {
        "status": "healthy",
        "service": "TTS-STT Data Collection API",
        "timestamp": datetime.now(UTC).isoformat()
    }
    
    # Check MongoDB connection
    try:
        client = get_client()
        if client:
            await client.admin.command('ping')
            health_status["database"] = "connected"
        else:
            health_status["database"] = "not_initialized"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check bot status
    global bot_application
    if bot_application:
        health_status["bot"] = "running"
    else:
        health_status["bot"] = "not_running"
        health_status["status"] = "degraded"
    
    return health_status

async def run_bot():
    """Run the telegram bot in the background."""
    global bot_application
    try:
        logger.info("Initializing bot...")
        bot_application = create_bot_application()
        await bot_application.initialize()
        await bot_application.start()
        await bot_application.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
        )
        logger.info("Bot started successfully")

        while True:
            await asyncio.sleep(3600)  # just keep alive

    except asyncio.CancelledError:
        logger.info("Bot task cancelled")
        raise
    except Exception as e:
        logger.error(f"Bot startup error: {e}")
        # Don't crash the API server if bot fails

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting uvicorn server")
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000,  # 8797 dan 8000 ga o'zgardi
        log_level="debug",  # debug mode
        reload=False
    )

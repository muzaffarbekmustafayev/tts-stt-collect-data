import asyncio
import logging
import sys
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional
from config import WEBAPP_URL

from telegram import User

from config import LOG_FORMAT, LOG_LEVEL
from db.db import init_db
from bot import create_bot_application, lifespan
from api import get_stores, get_store, get_store_products, get_user, create_order, get_user_orders, get_user_order_items, get_product, update_user
from db.models import Order, UserUpdate

# Configure logging
logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG)  # Set to DEBUG for more detailed logs
logger = logging.getLogger(__name__)

# Log startup information
logger.info(f"Python version: {sys.version}")
logger.info(f"Starting Water Delivery System API")

# Initialize the database
init_db()
logger.info("Database initialized successfully")

# Create static directory if it doesn't exist
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
PRODUCT_IMAGES_DIR = os.path.join(STATIC_DIR, "product_images")
os.makedirs(PRODUCT_IMAGES_DIR, exist_ok=True)

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

app = FastAPI(title="Water Delivery System", lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["http://localhost:5173", "https://water-delivery-system-frontend.vercel.app", "https://asror-qobulov.jprq.site"],  # or ["*"] for all origins (not recommended for production)
    allow_origins=["*"],  # or ["*"] for all origins (not recommended for production)
    # allow_origins=[WEBAPP_URL, "https://asror-qobulov.jprq.site"],  # or ["*"] for all origins (not recommended for production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API endpoints
@app.get("/")
def root():
    logger.info("Root endpoint called")
    return {"message": "Water Delivery System API"}

@app.get("/api/stores")
def api_get_stores():
    logger.info("API endpoint /api/stores called")
    result = get_stores()
    logger.info(f"API endpoint /api/stores returning: {result}")
    return result

@app.get("/api/stores/{store_id}")
def api_get_store(store_id: int):
    logger.info(f"API endpoint /api/stores/{store_id} called")
    return get_store(store_id)

@app.get("/api/stores/{store_id}/products")
def api_get_store_products(store_id: int):
    return get_store_products(store_id)

@app.get("/api/users/{telegram_id}")
def api_get_user(telegram_id: int):
    return get_user(telegram_id)


@app.put("/api/users/{telegram_id}")
async def api_update_user(telegram_id: int, user: UserUpdate):
    if telegram_id != user.telegram_id:
        raise HTTPException(status_code=400, detail="Telegram ID mismatch")
    return update_user(telegram_id, user)

@app.post("/api/orders")
def api_create_order(order: Order):
    return create_order(order)

@app.get("/api/products/{product_id}")
def api_get_product(product_id: int):
    return get_product(product_id)

@app.get("/api/users/{telegram_id}/orders")
def api_get_user_orders(telegram_id: int):
    return get_user_orders(telegram_id)

@app.get("/api/users/{telegram_id}/order_items")
def api_get_user_order_items(telegram_id: int):
    return get_user_order_items(telegram_id)


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
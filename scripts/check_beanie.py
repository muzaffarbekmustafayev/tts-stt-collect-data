import asyncio
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

async def check():
    print(f"MONGODB_URL: {settings.MONGODB_URL}")
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client.get_database()
    print(f"DB: {db}")
    print(f"DB.client: {db.client}")
    print(f"Type of DB.client: {type(db.client)}")
    
    try:
        from beanie import __version__ as beanie_version
        print(f"Beanie version: {beanie_version}")
    except ImportError:
        print("Beanie not found")
        
    try:
        import motor
        print(f"Motor version: {motor.version}")
    except ImportError:
        print("Motor not found")

if __name__ == "__main__":
    asyncio.run(check())

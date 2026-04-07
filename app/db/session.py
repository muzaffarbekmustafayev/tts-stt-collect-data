from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from beanie import init_beanie
from app.config import settings
from app.models.user import User
from app.models.sentence import Sentence
from app.models.received_audio import ReceivedAudio
from app.models.checked_audio import CheckedAudio
from app.models.admin_users import AdminUser
from app.core.logging import get_logger

logger = get_logger("db.session")

# Global client instance
_client: AsyncIOMotorClient = None

# Global monkeypatch for Beanie/Motor compatibility
original_aggregate = AsyncIOMotorCollection.aggregate
def patched_aggregate(self, *args, **kwargs):
    result = original_aggregate(self, *args, **kwargs)
    async def wrapper():
        return result
    return wrapper()
AsyncIOMotorCollection.aggregate = patched_aggregate

async def init_db():
    """Initialize MongoDB connection with optimized settings"""
    global _client
    
    # Monkeypatch for Beanie/Motor compatibility
    if not hasattr(AsyncIOMotorClient, 'append_metadata'):
        AsyncIOMotorClient.append_metadata = lambda self, metadata: None
    
    try:
        # Create Motor client with connection pooling
        _client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            maxPoolSize=50,  # Maximum connections in pool
            minPoolSize=10,  # Minimum connections in pool
            maxIdleTimeMS=45000,  # Close idle connections after 45s
            serverSelectionTimeoutMS=5000,  # Timeout for server selection
            connectTimeoutMS=10000,  # Connection timeout
            socketTimeoutMS=45000,  # Socket timeout
        )
        
        # Test connection
        await _client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        
        # Initialize beanie with the document models
        await init_beanie(
            database=_client.get_database(),
            document_models=[
                User,
                Sentence,
                ReceivedAudio,
                CheckedAudio,
                AdminUser
            ]
        )
        logger.info("Beanie initialized with all document models")
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise

async def close_db():
    """Close MongoDB connection"""
    global _client
    if _client:
        _client.close()
        logger.info("MongoDB connection closed")

def get_client() -> AsyncIOMotorClient:
    """Get the global MongoDB client"""
    return _client

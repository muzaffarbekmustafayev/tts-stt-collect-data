from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA_DIR = os.path.join(BASE_DIR, "media")
AUDIO_DIR = os.path.join(MEDIA_DIR, "audio")

# Ensure directories exist
os.makedirs(AUDIO_DIR, exist_ok=True)

class Settings(BaseSettings):
    # Bot settings
    BOT_API_TOKEN: str = Field(..., description="Telegram bot token")
    
    # Database settings
    DATABASE_URL: str = Field(..., description="MongoDB connection URL (deprecated, use MONGODB_URL)")
    MONGODB_URL: str = Field(..., description="MongoDB connection URL")
    
    # Audio limits
    sentence_to_audio_limit: int = Field(default=5, ge=1, le=100, description="Max audios per sentence")
    user_sent_audio_limit: int = Field(default=5, ge=1, description="Max audios user can send")
    user_check_audio_limit: int = Field(default=1000, ge=1, description="Max audios user can check")
    audio_check_limit: int = Field(default=5, ge=1, le=20, description="Max checks per audio")
    
    # Timeout settings
    pending_audio_timeout_minutes: int = Field(default=10, ge=1, le=1440, description="Pending audio timeout in minutes")
    
    # Security settings
    SECRET_KEY: str = Field(..., min_length=32, description="Secret key for JWT")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440, ge=1, description="Access token expiration in minutes")
    
    @field_validator('MONGODB_URL')
    @classmethod
    def validate_mongodb_url(cls, v: str) -> str:
        if not v.startswith('mongodb://') and not v.startswith('mongodb+srv://'):
            raise ValueError('MONGODB_URL must start with mongodb:// or mongodb+srv://')
        return v
    
    @field_validator('SECRET_KEY')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError('SECRET_KEY must be at least 32 characters long')
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

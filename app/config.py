from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BOT_API_TOKEN: str
    DATABASE_URL: str
    sentence_to_audio_limit: int = 5
    user_sent_audio_limit: int = 5
    user_check_audio_limit: int = 0
    audio_check_limit: int = 5
    pending_audio_timeout_minutes: int = 10
    # other settings
    class Config:
        env_file = ".env"

settings = Settings()

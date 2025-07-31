from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BOT_API_TOKEN: str # telegram bot token
    DATABASE_URL: str # database url
    sentence_to_audio_limit: int = 5 # bir gap nechta audio bo'lishi 
    user_sent_audio_limit: int = 5 # bir user nechta audio yuborishi
    user_check_audio_limit: int = 0 # bir user nechta audio tekshirishi
    audio_check_limit: int = 5 # bir audio nechta marta takshirilishi
    pending_audio_timeout_minutes: int = 10 # audio tekshirish vaqti
    # other settings
    class Config:
        env_file = ".env"

settings = Settings()

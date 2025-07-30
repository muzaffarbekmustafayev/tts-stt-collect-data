from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BOT_API_TOKEN: str
    DATABASE_URL: str
    # other settings
    class Config:
        env_file = ".env"

settings = Settings()

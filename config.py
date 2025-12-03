from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Глобальные настройки приложения.
    Загружает переменные окружения из файла .env и валидирует их наличие.
    """
    CLIENT_ID: str
    CLIENT_SECRET: str
    HOST_URL: str
    TOKENS_FILE: str = "tokens.json"
    BITRIX_OAUTH_URL: str = "https://oauth.bitrix.info"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
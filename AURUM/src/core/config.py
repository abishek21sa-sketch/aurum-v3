from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    APP_NAME: str = "AURUM"
    APP_ENV: str = "dev"
    API_KEY: str = ""

    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000

    DASHBOARD_HOST: str = "localhost"
    DASHBOARD_PORT: int = 8501

    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/aurum"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    LOG_LEVEL: str = "INFO"


settings = Settings()

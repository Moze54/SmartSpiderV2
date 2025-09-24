import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "SmartSpider"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        env_file = ".env"

settings = Settings()
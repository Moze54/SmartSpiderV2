from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "SmartSpider"
    debug: bool = False
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

settings = Settings()
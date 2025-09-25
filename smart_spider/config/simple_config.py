from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class DatabaseConfig(BaseModel):
    """数据库配置"""
    host: str = "localhost"
    port: int = 3306
    user: str = "smartspider"
    password: str = "smartspider"
    name: str = "smartspider"

    @property
    def url(self) -> str:
        # 使用SQLite作为默认数据库，无需外部依赖
        return "sqlite+aiosqlite:///./smartspider.db"


class RedisConfig(BaseModel):
    """Redis配置"""
    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    db: int = 0

    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class AppConfig(BaseModel):
    """应用配置"""
    name: str = "SmartSpider"
    version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000


# 全局配置
config = AppConfig()
database_config = DatabaseConfig()
redis_config = RedisConfig()
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings
import os


class DatabaseSettings(BaseSettings):
    """数据库配置"""

    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    user: str = Field(default="smartspider", env="DB_USER")
    password: str = Field(default="smartspider", env="DB_PASSWORD")
    name: str = Field(default="smartspider", env="DB_NAME")

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class RedisSettings(BaseSettings):
    """Redis配置"""

    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    db: int = Field(default=0, env="REDIS_DB")

    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class CelerySettings(BaseSettings):
    """Celery配置"""

    broker_url: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    result_backend: str = Field(default="redis://localhost:6379/2", env="CELERY_RESULT_BACKEND")
    task_serializer: str = "json"
    accept_content: List[str] = ["json"]
    result_serializer: str = "json"
    timezone: str = "Asia/Shanghai"
    enable_utc: bool = False
    task_track_started: bool = True
    task_time_limit: int = 30 * 60  # 30 minutes
    task_soft_time_limit: int = 25 * 60  # 25 minutes


class MinIOSettings(BaseSettings):
    """MinIO配置"""

    endpoint: str = Field(default="localhost:9000", env="MINIO_ENDPOINT")
    access_key: str = Field(default="minioadmin", env="MINIO_ACCESS_KEY")
    secret_key: str = Field(default="minioadmin", env="MINIO_SECRET_KEY")
    secure: bool = Field(default=False, env="MINIO_SECURE")
    bucket_name: str = Field(default="smartspider", env="MINIO_BUCKET")


class SecuritySettings(BaseSettings):
    """安全配置"""

    secret_key: str = Field(default="your-secret-key-change-this", env="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    allowed_methods: List[str] = ["*"]
    allowed_headers: List[str] = ["*"]


class LoggingSettings(BaseSettings):
    """日志配置"""

    level: str = Field(default="INFO", env="LOG_LEVEL")
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: str = Field(default="logs/smartspider.log", env="LOG_FILE_PATH")
    max_bytes: int = Field(default=10 * 1024 * 1024, env="LOG_MAX_BYTES")  # 10MB
    backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")

    # 结构化日志
    enable_structured: bool = Field(default=True, env="ENABLE_STRUCTURED_LOG")

    # 外部日志服务
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")


class CrawlerSettings(BaseSettings):
    """爬虫配置"""

    max_concurrent_requests: int = Field(default=100, env="MAX_CONCURRENT_REQUESTS")
    download_delay: float = Field(default=1.0, env="DOWNLOAD_DELAY")
    randomize_download_delay: bool = Field(default=True, env="RANDOMIZE_DOWNLOAD_DELAY")

    # 重试配置
    retry_times: int = Field(default=3, env="RETRY_TIMES")
    retry_http_codes: List[int] = [500, 502, 503, 504, 408, 429]

    # 超时配置
    download_timeout: int = Field(default=30, env="DOWNLOAD_TIMEOUT")

    # User-Agent
    user_agent: str = Field(
        default="SmartSpider/1.0 (+https://github.com/your-repo)",
        env="USER_AGENT"
    )

    # 代理配置
    proxy_enabled: bool = Field(default=False, env="PROXY_ENABLED")
    proxy_list: List[str] = Field(default_factory=list, env="PROXY_LIST")


class MonitoringSettings(BaseSettings):
    """监控配置"""

    prometheus_enabled: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    prometheus_port: int = Field(default=8000, env="PROMETHEUS_PORT")

    # 健康检查
    health_check_enabled: bool = Field(default=True, env="HEALTH_CHECK_ENABLED")
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")

    # 指标收集
    metrics_enabled: bool = Field(default=True, env="METRICS_ENABLED")
    metrics_interval: int = Field(default=60, env="METRICS_INTERVAL")


class AppSettings(BaseSettings):
    """应用配置"""

    # 基础配置
    name: str = "SmartSpider"
    version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")

    # 服务器配置
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=1, env="WORKERS")

    # API配置
    api_v1_prefix: str = "/api/v1"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"

    # 文件上传
    max_upload_size: int = Field(default=10 * 1024 * 1024, env="MAX_UPLOAD_SIZE")  # 10MB
    upload_dir: str = Field(default="uploads", env="UPLOAD_DIR")


class Settings(BaseSettings):
    """主配置类"""

    app: AppSettings = AppSettings()
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    celery: CelerySettings = CelerySettings()
    minio: MinIOSettings = MinIOSettings()
    security: SecuritySettings = SecuritySettings()
    logging: LoggingSettings = LoggingSettings()
    crawler: CrawlerSettings = CrawlerSettings()
    monitoring: MonitoringSettings = MonitoringSettings()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 全局配置实例
settings = Settings()
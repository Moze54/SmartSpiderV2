from typing import List, Optional, Dict, Any
from pydantic import Field, validator
from pydantic_settings import BaseSettings
import os


class DatabaseSettings(BaseSettings):
    """数据库配置 - 增强版"""

    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    user: str = Field(default="smartspider", env="DB_USER")
    password: str = Field(default="smartspider", env="DB_PASSWORD")
    name: str = Field(default="smartspider", env="DB_NAME")
    pool_size: int = Field(default=20, env="DATABASE_POOL_SIZE")
    max_overflow: int = Field(default=30, env="DATABASE_MAX_OVERFLOW")

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
    """爬虫配置 - 增强版"""

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

    # 高级功能配置
    request_fingerprint_enabled: bool = Field(default=True, env="REQUEST_FINGERPRINT_ENABLED")
    request_deduplication_enabled: bool = Field(default=True, env="REQUEST_DEDUPLICATION_ENABLED")
    cookie_rotation_enabled: bool = Field(default=True, env="COOKIE_ROTATION_ENABLED")
    proxy_rotation_enabled: bool = Field(default=True, env="PROXY_ROTATION_ENABLED")
    browser_cookie_enabled: bool = Field(default=True, env="BROWSER_COOKIE_ENABLED")
    data_validation_enabled: bool = Field(default=True, env="DATA_VALIDATION_ENABLED")

    # 安全限制
    max_url_length: int = Field(default=2048, env="MAX_URL_LENGTH")
    max_content_length: int = Field(default=10485760, env="MAX_CONTENT_LENGTH")  # 10MB
    max_redirects: int = Field(default=10, env="MAX_REDIRECTS")
    max_retry_times: int = Field(default=5, env="MAX_RETRY_TIMES")


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
    """应用配置 - 增强版"""

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

    # 存储配置
    output_dir: str = Field(default="./output", env="OUTPUT_DIR")
    storage_dir: str = Field(default="./storage", env="STORAGE_DIR")

    # 安全限制
    max_url_length: int = Field(default=2048, env="MAX_URL_LENGTH")
    max_content_length: int = Field(default=10 * 1024 * 1024, env="MAX_CONTENT_LENGTH")  # 10MB

    # 高级功能开关
    request_fingerprint_enabled: bool = Field(default=True, env="REQUEST_FINGERPRINT_ENABLED")
    request_deduplication_enabled: bool = Field(default=True, env="REQUEST_DEDUPLICATION_ENABLED")
    cookie_rotation_enabled: bool = Field(default=True, env="COOKIE_ROTATION_ENABLED")
    proxy_rotation_enabled: bool = Field(default=True, env="PROXY_ROTATION_ENABLED")
    browser_cookie_enabled: bool = Field(default=True, env="BROWSER_COOKIE_ENABLED")
    data_validation_enabled: bool = Field(default=True, env="DATA_VALIDATION_ENABLED")
    scheduler_enabled: bool = Field(default=True, env="SCHEDULER_ENABLED")


class ProxyPoolSettings(BaseSettings):
    """代理池配置"""

    test_url: str = Field(default="https://httpbin.org/ip", env="PROXY_TEST_URL")
    check_interval: int = Field(default=300, env="PROXY_CHECK_INTERVAL")  # 5分钟
    max_response_time: float = Field(default=10.0, env="PROXY_MAX_RESPONSE_TIME")
    min_success_rate: float = Field(default=0.8, env="PROXY_MIN_SUCCESS_RATE")
    max_failures: int = Field(default=5, env="PROXY_MAX_FAILURES")


class SchedulerSettings(BaseSettings):
    """调度器配置"""

    enabled: bool = Field(default=True, env="SCHEDULER_ENABLED")
    max_instances: int = Field(default=3, env="SCHEDULER_MAX_INSTANCES")
    coalesce: bool = Field(default=False, env="SCHEDULER_COALESCE")
    misfire_grace_time: int = Field(default=300, env="SCHEDULER_MISFIRE_GRACE_TIME")


class ExportSettings(BaseSettings):
    """数据导出配置"""

    formats: List[str] = Field(default=["json", "csv", "excel"], env="EXPORT_FORMATS")
    max_records: int = Field(default=100000, env="EXPORT_MAX_RECORDS")
    file_size_limit: int = Field(default=104857600, env="EXPORT_FILE_SIZE_LIMIT")  # 100MB


class CleanupSettings(BaseSettings):
    """清理配置"""

    old_files_days: int = Field(default=30, env="CLEANUP_OLD_FILES_DAYS")
    old_cookies_days: int = Field(default=7, env="CLEANUP_OLD_COOKIES_DAYS")
    old_proxies_days: int = Field(default=30, env="CLEANUP_OLD_PROXIES_DAYS")
    interval_hours: int = Field(default=24, env="CLEANUP_INTERVAL_HOURS")


class AdvancedSettings(BaseSettings):
    """高级配置"""

    # 请求指纹和去重
    request_fingerprint_enabled: bool = Field(default=True, env="REQUEST_FINGERPRINT_ENABLED")
    request_deduplication_enabled: bool = Field(default=True, env="REQUEST_DEDUPLICATION_ENABLED")
    deduplication_backend: str = Field(default="memory", env="DEDUPLICATION_BACKEND")
    deduplication_max_size: int = Field(default=100000, env="DEDUPLICATION_MAX_SIZE")
    deduplication_ttl: Optional[int] = Field(default=3600, env="DEDUPLICATION_TTL")

    # Cookie管理
    cookie_rotation_enabled: bool = Field(default=True, env="COOKIE_ROTATION_ENABLED")
    browser_cookie_enabled: bool = Field(default=True, env="BROWSER_COOKIE_ENABLED")
    cookie_storage_dir: str = Field(default="./cookies", env="COOKIE_STORAGE_DIR")

    # 数据验证
    data_validation_enabled: bool = Field(default=True, env="DATA_VALIDATION_ENABLED")
    default_validation_schema: str = Field(default="basic", env="DEFAULT_VALIDATION_SCHEMA")


class Settings(BaseSettings):
    """主配置类 - 增强版"""

    app: AppSettings = AppSettings()
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    celery: CelerySettings = CelerySettings()
    minio: MinIOSettings = MinIOSettings()
    security: SecuritySettings = SecuritySettings()
    logging: LoggingSettings = LoggingSettings()
    crawler: CrawlerSettings = CrawlerSettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    proxy_pool: ProxyPoolSettings = ProxyPoolSettings()
    scheduler: SchedulerSettings = SchedulerSettings()
    export: ExportSettings = ExportSettings()
    cleanup: CleanupSettings = CleanupSettings()
    advanced: AdvancedSettings = AdvancedSettings()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 全局配置实例
settings = Settings()
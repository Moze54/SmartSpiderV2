import logging
import logging.config
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import structlog
from pythonjsonlogger import jsonlogger

from smart_spider.config.settings import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """自定义JSON日志格式化器"""

    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """添加自定义字段到日志记录"""
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)

        # 添加时间戳
        log_record['timestamp'] = datetime.utcnow().isoformat()

        # 添加上下文信息
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno

        # 添加线程信息
        log_record['thread'] = record.thread
        log_record['thread_name'] = record.threadName

        # 添加进程信息
        log_record['process'] = record.process
        log_record['process_name'] = record.processName

        # 添加异常信息
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)

        # 添加额外字段
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        if hasattr(record, 'task_id'):
            log_record['task_id'] = record.task_id


class RequestIdFilter(logging.Filter):
    """请求ID过滤器"""

    def __init__(self, request_id: str = None):
        super().__init__()
        self.request_id = request_id

    def filter(self, record: logging.LogRecord) -> bool:
        """添加请求ID到日志记录"""
        if self.request_id:
            record.request_id = self.request_id
        return True


class ContextFilter(logging.Filter):
    """上下文信息过滤器"""

    def __init__(self):
        super().__init__()
        self._context = {}

    def add_context(self, key: str, value: Any):
        """添加上下文信息"""
        self._context[key] = value

    def remove_context(self, key: str):
        """移除上下文信息"""
        self._context.pop(key, None)

    def clear_context(self):
        """清空上下文信息"""
        self._context.clear()

    def filter(self, record: logging.LogRecord) -> bool:
        """添加上下文信息到日志记录"""
        for key, value in self._context.items():
            setattr(record, key, value)
        return True


class Logger:
    """日志管理器"""

    def __init__(self):
        self.context_filter = ContextFilter()
        self._setup_logging()

    def _setup_logging(self):
        """设置日志配置"""
        # 创建日志目录
        log_dir = Path(settings.logging.file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        # 基础日志配置
        logging_config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': settings.logging.format
                },
                'json': {
                    '()': CustomJsonFormatter,
                    'json_ensure_ascii': False,
                },
                'detailed': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s'
                }
            },
            'filters': {
                'context': {
                    '()': lambda: self.context_filter
                }
            },
            'handlers': {
                'console': {
                    'level': settings.logging.level,
                    'class': 'logging.StreamHandler',
                    'formatter': 'json' if settings.logging.enable_structured else 'standard',
                    'filters': ['context'],
                    'stream': sys.stdout
                },
                'file': {
                    'level': settings.logging.level,
                    'class': 'logging.handlers.RotatingFileHandler',
                    'formatter': 'json' if settings.logging.enable_structured else 'detailed',
                    'filters': ['context'],
                    'filename': settings.logging.file_path,
                    'maxBytes': settings.logging.max_bytes,
                    'backupCount': settings.logging.backup_count,
                    'encoding': 'utf-8'
                },
                'error_file': {
                    'level': 'ERROR',
                    'class': 'logging.handlers.RotatingFileHandler',
                    'formatter': 'json' if settings.logging.enable_structured else 'detailed',
                    'filters': ['context'],
                    'filename': str(Path(settings.logging.file_path).parent / 'error.log'),
                    'maxBytes': settings.logging.max_bytes,
                    'backupCount': settings.logging.backup_count,
                    'encoding': 'utf-8'
                }
            },
            'loggers': {
                '': {  # root logger
                    'handlers': ['console', 'file', 'error_file'],
                    'level': settings.logging.level,
                    'propagate': False
                },
                'uvicorn': {
                    'handlers': ['console', 'file'],
                    'level': settings.logging.level,
                    'propagate': False
                },
                'uvicorn.error': {
                    'handlers': ['console', 'file'],
                    'level': settings.logging.level,
                    'propagate': False
                },
                'uvicorn.access': {
                    'handlers': ['console', 'file'],
                    'level': settings.logging.level,
                    'propagate': False
                },
                'sqlalchemy': {
                    'handlers': ['console', 'file'],
                    'level': 'WARNING',
                    'propagate': False
                },
                'celery': {
                    'handlers': ['console', 'file'],
                    'level': settings.logging.level,
                    'propagate': False
                }
            }
        }

        # 应用日志配置
        logging.config.dictConfig(logging_config)

        # 配置structlog
        if settings.logging.enable_structured:
            structlog.configure(
                processors=[
                    structlog.stdlib.filter_by_level,
                    structlog.stdlib.add_logger_name,
                    structlog.stdlib.add_log_level,
                    structlog.stdlib.PositionalArgumentsFormatter(),
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.processors.StackInfoRenderer(),
                    structlog.processors.format_exc_info,
                    structlog.processors.UnicodeDecoder(),
                    structlog.processors.JSONRenderer()
                ],
                context_class=dict,
                logger_factory=structlog.stdlib.LoggerFactory(),
                wrapper_class=structlog.stdlib.BoundLogger,
                cache_logger_on_first_use=True,
            )

        # 配置Sentry
        if settings.logging.sentry_dsn:
            import sentry_sdk
            sentry_sdk.init(
                dsn=settings.logging.sentry_dsn,
                environment=settings.app.environment,
                release=f"{settings.app.name}@{settings.app.version}",
                traces_sample_rate=1.0,
                profiles_sample_rate=1.0,
            )

    def get_logger(self, name: str) -> logging.Logger:
        """获取日志器"""
        return logging.getLogger(name)

    def get_struct_logger(self, name: str):
        """获取结构化日志器"""
        return structlog.get_logger(name)

    def add_context(self, key: str, value: Any):
        """添加上下文"""
        self.context_filter.add_context(key, value)

    def remove_context(self, key: str):
        """移除上下文"""
        self.context_filter.remove_context(key)

    def clear_context(self):
        """清空上下文"""
        self.context_filter.clear_context()

    def bind_context(self, **kwargs):
        """绑定上下文（上下文管理器）"""
        return ContextManager(self.context_filter, **kwargs)


class ContextManager:
    """上下文管理器"""

    def __init__(self, context_filter: ContextFilter, **kwargs):
        self.context_filter = context_filter
        self.context_data = kwargs
        self.previous_context = {}

    def __enter__(self):
        """进入上下文"""
        for key, value in self.context_data.items():
            self.previous_context[key] = getattr(self.context_filter, key, None)
            self.context_filter.add_context(key, value)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        for key, value in self.previous_context.items():
            if value is None:
                self.context_filter.remove_context(key)
            else:
                self.context_filter.add_context(key, value)


# 全局日志管理器实例
logger_manager = Logger()

# 快捷访问
get_logger = logger_manager.get_logger
get_struct_logger = logger_manager.get_struct_logger
add_context = logger_manager.add_context
remove_context = logger_manager.remove_context
clear_context = logger_manager.clear_context
bind_context = logger_manager.bind_context

# 常用日志器
logger = get_logger("smartspider")
api_logger = get_logger("smartspider.api")
celery_logger = get_logger("smartspider.celery")
crawler_logger = get_logger("smartspider.crawler")
database_logger = get_logger("smartspider.database")
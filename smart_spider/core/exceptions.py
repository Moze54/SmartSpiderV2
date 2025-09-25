"""
自定义异常类 - 增强版错误处理
"""
from typing import Optional, Dict, Any, List
from datetime import datetime


class SmartSpiderException(Exception):
    """基础异常类 - 增强版"""

    def __init__(
        self,
        message: str,
        code: int = 500,
        details: dict = None,
        timestamp: Optional[datetime] = None,
        traceback: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        self.timestamp = timestamp or datetime.now()
        self.traceback = traceback
        self.context = context or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'error': self.__class__.__name__,
            'message': self.message,
            'code': self.code,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
            'traceback': self.traceback,
            'context': self.context
        }

    def __str__(self):
        return f"[{self.code}] {self.message}"

    def __repr__(self):
        return f"{self.__class__.__name__}(message='{self.message}', code={self.code})"


class TaskNotFoundException(SmartSpiderException):
    """任务不存在异常 - 增强版"""

    def __init__(self, task_id: str, context: Optional[Dict] = None):
        super().__init__(
            message=f"任务不存在: {task_id}",
            code=404,
            details={"task_id": task_id},
            context=context
        )


class TaskConflictException(SmartSpiderException):
    """任务状态冲突异常"""

    def __init__(self, message: str, task_id: str = None):
        super().__init__(
            message=message,
            code=409,
            details={"task_id": task_id} if task_id else {}
        )


class CrawlerException(SmartSpiderException):
    """爬虫异常 - 增强版"""

    def __init__(
        self,
        message: str,
        url: str = None,
        details: dict = None,
        error_type: str = "general",
        severity: str = "error"
    ):
        super().__init__(
            message=message,
            code=500,
            details={
                "url": url,
                "error_type": error_type,
                "severity": severity,
                "retryable": self._is_retryable_error(error_type),
                **(details or {})
            }
        )

    @staticmethod
    def _is_retryable_error(error_type: str) -> bool:
        """判断错误是否可重试"""
        retryable_errors = {
            "network_error", "timeout_error", "server_error",
            "rate_limit", "proxy_error", "dns_error"
        }
        return error_type in retryable_errors


class ConfigurationException(SmartSpiderException):
    """配置异常"""

    def __init__(self, message: str, config_key: str = None):
        super().__init__(
            message=message,
            code=400,
            details={"config_key": config_key} if config_key else {}
        )


class DatabaseException(SmartSpiderException):
    """数据库异常"""

    def __init__(self, message: str, operation: str = None):
        super().__init__(
            message=message,
            code=500,
            details={"operation": operation} if operation else {}
        )


class NetworkException(SmartSpiderException):
    """网络异常 - 增强版"""

    def __init__(
        self,
        message: str,
        url: str = None,
        status_code: int = None,
        error_type: str = "network_error",
        recoverable: bool = True
    ):
        super().__init__(
            message=message,
            code=status_code or 500,
            details={
                "url": url,
                "status_code": status_code,
                "error_type": error_type,
                "recoverable": recoverable
            }
        )


class TimeoutException(SmartSpiderException):
    """超时异常"""

    def __init__(self, message: str, timeout: int = None):
        super().__init__(
            message=message,
            code=408,
            details={"timeout": timeout} if timeout else {}
        )


class RateLimitException(SmartSpiderException):
    """限流异常 - 增强版"""

    def __init__(
        self,
        message: str,
        retry_after: int = None,
        url: str = None,
        rate_limit_type: str = "generic",
        reset_time: Optional[datetime] = None
    ):
        super().__init__(
            message=message,
            code=429,
            details={
                "retry_after": retry_after,
                "url": url,
                "rate_limit_type": rate_limit_type,
                "reset_time": reset_time.isoformat() if reset_time else None
            }
        )


class ValidationException(SmartSpiderException):
    """验证异常"""

    def __init__(self, message: str, field: str = None, value: str = None):
        super().__init__(
            message=message,
            code=400,
            details={"field": field, "value": value} if field else {}
        )


class StorageException(SmartSpiderException):
    """存储异常"""

    def __init__(self, message: str, storage_type: str = None, path: str = None):
        super().__init__(
            message=message,
            code=500,
            details={"storage_type": storage_type, "path": path} if storage_type else {}
        )


class ParserException(SmartSpiderException):
    """解析异常"""

    def __init__(self, message: str, selector: str = None, content_type: str = None):
        super().__init__(
            message=message,
            code=500,
            details={"selector": selector, "content_type": content_type} if selector else {}
        )


class ProxyException(SmartSpiderException):
    """代理异常"""

    def __init__(self, message: str, proxy: str = None):
        super().__init__(
            message=message,
            code=500,
            details={"proxy": proxy} if proxy else {}
        )


class CookieException(SmartSpiderException):
    """Cookie异常 - 增强版"""

    def __init__(
        self,
        message: str,
        domain: str = None,
        cookie_name: str = None,
        error_type: str = "invalid"
    ):
        super().__init__(
            message=message,
            code=500,
            details={
                "domain": domain,
                "cookie_name": cookie_name,
                "error_type": error_type,
                "is_authentication_error": error_type in ["expired", "invalid", "missing"]
            }
        )


class ProxyException(SmartSpiderException):
    """代理异常 - 增强版"""

    def __init__(
        self,
        message: str,
        proxy: str = None,
        proxy_type: str = "http",
        error_type: str = "connection_failed"
    ):
        super().__init__(
            message=message,
            code=500,
            details={
                "proxy": proxy,
                "proxy_type": proxy_type,
                "error_type": error_type,
                "retryable": error_type in ["connection_failed", "timeout", "banned"]
            }
        )


class ParserException(SmartSpiderException):
    """解析异常 - 增强版"""

    def __init__(
        self,
        message: str,
        selector: str = None,
        content_type: str = None,
        content_length: int = None,
        error_type: str = "selector_not_found"
    ):
        super().__init__(
            message=message,
            code=500,
            details={
                "selector": selector,
                "content_type": content_type,
                "content_length": content_length,
                "error_type": error_type,
                "recoverable": error_type in ["selector_not_found", "empty_content", "encoding_error"]
            }
        )


class StorageException(SmartSpiderException):
    """存储异常 - 增强版"""

    def __init__(
        self,
        message: str,
        storage_type: str = None,
        path: str = None,
        operation: str = None,
        error_type: str = "io_error"
    ):
        super().__init__(
            message=message,
            code=500,
            details={
                "storage_type": storage_type,
                "path": path,
                "operation": operation,
                "error_type": error_type,
                "retryable": error_type in ["io_error", "temporary_failure", "quota_exceeded"]
            }
        )


class ValidationException(SmartSpiderException):
    """验证异常 - 增强版"""

    def __init__(
        self,
        message: str,
        field: str = None,
        value: str = None,
        validation_type: str = "format",
        expected_format: str = None
    ):
        super().__init__(
            message=message,
            code=400,
            details={
                "field": field,
                "value": value,
                "validation_type": validation_type,
                "expected_format": expected_format
            }
        )


class DatabaseException(SmartSpiderException):
    """数据库异常 - 增强版"""

    def __init__(
        self,
        message: str,
        operation: str = None,
        table: str = None,
        error_type: str = "connection_error"
    ):
        super().__init__(
            message=message,
            code=500,
            details={
                "operation": operation,
                "table": table,
                "error_type": error_type,
                "retryable": error_type in ["connection_error", "timeout_error", "lock_timeout"]
            }
        )


class ConfigurationException(SmartSpiderException):
    """配置异常 - 增强版"""

    def __init__(
        self,
        message: str,
        config_key: str = None,
        config_value: str = None,
        config_type: str = "invalid"
    ):
        super().__init__(
            message=message,
            code=400,
            details={
                "config_key": config_key,
                "config_value": config_value,
                "config_type": config_type,
                "retryable": False  # 配置错误通常不可重试
            }
        )


class TaskConflictException(SmartSpiderException):
    """任务状态冲突异常 - 增强版"""

    def __init__(
        self,
        message: str,
        task_id: str = None,
        current_status: str = None,
        expected_status: str = None
    ):
        super().__init__(
            message=message,
            code=409,
            details={
                "task_id": task_id,
                "current_status": current_status,
                "expected_status": expected_status,
                "retryable": False  # 状态冲突通常不可重试
            }
        )


class ServerException(SmartSpiderException):
    """服务器异常 - 增强版"""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        server_type: str = "unknown",
        recoverable: bool = True
    ):
        super().__init__(
            message=message,
            code=status_code,
            details={
                "status_code": status_code,
                "server_type": server_type,
                "recoverable": recoverable,
                "is_server_error": 500 <= status_code < 600
            }
        )


# 错误处理工具函数
def create_retryable_error(
    exception_class: type,
    message: str,
    **kwargs
) -> SmartSpiderException:
    """创建可重试的错误"""
    kwargs.setdefault('error_type', 'retryable')
    return exception_class(message, **kwargs)


def create_non_retryable_error(
    exception_class: type,
    message: str,
    **kwargs
) -> SmartSpiderException:
    """创建不可重试的错误"""
    kwargs.setdefault('error_type', 'permanent')
    if 'recoverable' in kwargs:
        kwargs['recoverable'] = False
    return exception_class(message, **kwargs)


def is_retryable_error(exception: SmartSpiderException) -> bool:
    """判断错误是否可重试"""
    details = exception.details or {}
    return (
        details.get('retryable', True) and
        details.get('recoverable', True) and
        exception.code not in [400, 401, 403, 404, 422]  # 客户端错误通常不重试
    )


def extract_error_context(exception: Exception) -> Dict[str, Any]:
    """提取异常的上下文信息"""
    context = {
        'exception_type': type(exception).__name__,
        'message': str(exception),
        'timestamp': datetime.now().isoformat()
    }

    if isinstance(exception, SmartSpiderException):
        context.update({
            'code': exception.code,
            'details': exception.details,
            'retryable': is_retryable_error(exception)
        })

    return context


# 常用错误类型映射
ERROR_TYPE_MAPPING = {
    'network': NetworkException,
    'timeout': TimeoutException,
    'rate_limit': RateLimitException,
    'proxy': ProxyException,
    'cookie': CookieException,
    'parser': ParserException,
    'storage': StorageException,
    'validation': ValidationException,
    'database': DatabaseException,
    'configuration': ConfigurationException,
    'task_conflict': TaskConflictException,
    'task_not_found': TaskNotFoundException,
    'server': ServerException,
    'crawler': CrawlerException
}


def create_exception_from_error_type(
    error_type: str,
    message: str,
    **kwargs
) -> SmartSpiderException:
    """根据错误类型创建对应的异常"""
    exception_class = ERROR_TYPE_MAPPING.get(error_type, SmartSpiderException)
    return exception_class(message, **kwargs)
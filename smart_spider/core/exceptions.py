"""
自定义异常类
"""


class SmartSpiderException(Exception):
    """基础异常类"""

    def __init__(self, message: str, code: int = 500, details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class TaskNotFoundException(SmartSpiderException):
    """任务不存在异常"""

    def __init__(self, task_id: str):
        super().__init__(
            message=f"任务不存在: {task_id}",
            code=404,
            details={"task_id": task_id}
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
    """爬虫异常"""

    def __init__(self, message: str, url: str = None, details: dict = None):
        super().__init__(
            message=message,
            code=500,
            details={"url": url, **(details or {})}
        )


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
    """网络异常"""

    def __init__(self, message: str, url: str = None, status_code: int = None):
        super().__init__(
            message=message,
            code=status_code or 500,
            details={"url": url, "status_code": status_code} if url else {}
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
    """限流异常"""

    def __init__(self, message: str, retry_after: int = None):
        super().__init__(
            message=message,
            code=429,
            details={"retry_after": retry_after} if retry_after else {}
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
    """Cookie异常"""

    def __init__(self, message: str, domain: str = None):
        super().__init__(
            message=message,
            code=500,
            details={"domain": domain} if domain else {}
        )
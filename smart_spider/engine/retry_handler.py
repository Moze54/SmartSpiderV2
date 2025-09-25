import asyncio
import random
from typing import Callable, Any, Optional, Type, Union
from datetime import datetime
import aiohttp
from aiohttp import ClientError, ClientResponseError, ServerDisconnectedError, ClientOSError

from smart_spider.core.logger import crawler_logger
from smart_spider.core.exceptions import (
    NetworkException, TimeoutException, RateLimitException,
    ProxyException, ServerException
)


class RetryHandler:
    """智能重试处理器"""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retry_on_timeout: bool = True,
        retry_on_rate_limit: bool = True,
        custom_retry_rules: Optional[dict] = None
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retry_on_timeout = retry_on_timeout
        self.retry_on_rate_limit = retry_on_rate_limit
        self.custom_retry_rules = custom_retry_rules or {}

        # 默认重试状态码
        self.retry_status_codes = {
            408,  # Request Timeout
            429,  # Too Many Requests
            500,  # Internal Server Error
            502,  # Bad Gateway
            503,  # Service Unavailable
            504,  # Gateway Timeout
            520,  # Unknown Error
            521,  # Web Server Is Down
            522,  # Connection Timed Out
            523,  # Origin Is Unreachable
            524,  # A Timeout Occurred
        }

        # 更新自定义重试规则
        if 'status_codes' in self.custom_retry_rules:
            self.retry_status_codes.update(self.custom_retry_rules['status_codes'])

    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """执行函数并处理重试逻辑"""
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                crawler_logger.debug(
                    f"执行尝试 {attempt + 1}/{self.max_retries + 1}",
                    extra={'attempt': attempt + 1, 'max_attempts': self.max_retries + 1}
                )

                result = await func(*args, **kwargs)

                # 检查是否需要基于结果重试
                if self._should_retry_based_on_result(result, attempt):
                    delay = self._calculate_delay(attempt)
                    crawler_logger.info(
                        f"基于结果需要重试，等待 {delay:.2f} 秒后重试",
                        extra={'delay': delay, 'attempt': attempt + 1}
                    )
                    await asyncio.sleep(delay)
                    continue

                return result

            except Exception as e:
                last_exception = e

                if not self._should_retry_on_exception(e, attempt):
                    crawler_logger.error(
                        f"不可重试的异常，停止重试: {str(e)}",
                        extra={'exception': str(e), 'attempt': attempt + 1}
                    )
                    raise

                if attempt < self.max_retries:
                    delay = self._calculate_delay(attempt)
                    crawler_logger.warning(
                        f"异常重试: {str(e)}，等待 {delay:.2f} 秒后重试",
                        extra={
                            'exception': str(e),
                            'delay': delay,
                            'attempt': attempt + 1,
                            'max_attempts': self.max_retries + 1
                        }
                    )
                    await asyncio.sleep(delay)
                else:
                    crawler_logger.error(
                        f"达到最大重试次数 ({self.max_retries + 1})，停止重试",
                        extra={'final_exception': str(e)}
                    )

        # 所有重试都失败，抛出最后的异常
        raise last_exception

    def _should_retry_on_exception(self, exception: Exception, attempt: int) -> bool:
        """判断是否应该基于异常重试"""
        # 已经达到最大重试次数
        if attempt >= self.max_retries:
            return False

        # 网络相关异常
        if isinstance(exception, (NetworkException, TimeoutException)):
            return self.retry_on_timeout

        # 速率限制异常
        if isinstance(exception, RateLimitException):
            return self.retry_on_rate_limit

        # 代理相关异常
        if isinstance(exception, ProxyException):
            return True

        # 服务器异常
        if isinstance(exception, ServerException):
            return True

        # aiohttp 异常
        if isinstance(exception, ClientError):
            if isinstance(exception, ClientResponseError):
                status = exception.status
                if status in self.retry_status_codes:
                    return True
                # 4xx 错误通常不重试，除了特定的几个
                if 400 <= status < 500 and status not in [408, 429]:
                    return False
                return True
            elif isinstance(exception, (ServerDisconnectedError, ClientOSError)):
                return True

        # 自定义异常规则
        exception_type = type(exception).__name__
        if exception_type in self.custom_retry_rules.get('exceptions', {}):
            return self.custom_retry_rules['exceptions'][exception_type]

        return False

    def _should_retry_based_on_result(self, result: Any, attempt: int) -> bool:
        """判断是否应该基于结果重试"""
        # 可以在这里添加基于结果的重试逻辑
        # 例如：检查结果是否为空，是否包含特定错误信息等
        return False

    def _calculate_delay(self, attempt: int) -> float:
        """计算重试延迟时间"""
        # 指数退避
        delay = self.base_delay * (self.exponential_base ** attempt)

        # 添加随机抖动
        if self.jitter:
            delay = random.uniform(delay * 0.5, delay * 1.5)

        # 限制最大延迟
        delay = min(delay, self.max_delay)

        return delay

    def update_retry_rules(self, **kwargs):
        """更新重试规则"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            elif key in ['max_retries', 'base_delay', 'max_delay']:
                setattr(self, key, value)


class CircuitBreaker:
    """熔断器 - 防止连续失败"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    def call(self, func: Callable, *args, **kwargs):
        """包装函数调用"""
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """判断是否应该尝试重置熔断器"""
        return (
            self.last_failure_time and
            (datetime.now() - self.last_failure_time).seconds >= self.recovery_timeout
        )

    def _on_success(self):
        """处理成功情况"""
        self.failure_count = 0
        self.state = "closed"

    def _on_failure(self):
        """处理失败情况"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"


class AdaptiveRetryHandler(RetryHandler):
    """自适应重试处理器 - 根据成功率动态调整重试策略"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.success_count = 0
        self.failure_count = 0
        self.request_count = 0

        # 自适应参数
        self.adaptive_base_delay = self.base_delay
        self.adaptive_max_retries = self.max_retries
        self.success_rate_threshold = 0.8  # 成功率阈值

    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """执行函数并自适应调整重试策略"""
        self.request_count += 1

        try:
            result = await super().execute_with_retry(func, *args, **kwargs)
            self.success_count += 1
            self._adapt_strategy()
            return result

        except Exception as e:
            self.failure_count += 1
            self._adapt_strategy()
            raise

    def _adapt_strategy(self):
        """自适应调整重试策略"""
        if self.request_count < 10:  # 样本太少时不调整
            return

        success_rate = self.success_count / self.request_count

        # 根据成功率调整重试次数
        if success_rate < self.success_rate_threshold:
            # 成功率低，增加重试次数和延迟
            self.adaptive_max_retries = min(self.max_retries + 2, 10)
            self.adaptive_base_delay = min(self.base_delay * 1.5, 10.0)
        else:
            # 成功率高，减少重试次数和延迟
            self.adaptive_max_retries = max(self.max_retries - 1, 1)
            self.adaptive_base_delay = max(self.base_delay * 0.8, 0.5)

        crawler_logger.info(
            f"自适应调整重试策略: 成功率={success_rate:.2f}, "
            f"重试次数={self.adaptive_max_retries}, 基础延迟={self.adaptive_base_delay:.2f}s"
        )

    def get_stats(self) -> dict:
        """获取统计信息"""
        if self.request_count == 0:
            return {"message": "No requests processed yet"}

        return {
            "total_requests": self.request_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_count / self.request_count,
            "current_retry_config": {
                "max_retries": self.adaptive_max_retries,
                "base_delay": self.adaptive_base_delay
            }
        }
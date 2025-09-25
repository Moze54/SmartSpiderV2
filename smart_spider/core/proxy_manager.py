"""
代理管理模块 - 基础版本
"""
import asyncio
import aiohttp
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging

from smart_spider.core.exceptions import ProxyException, NetworkException
from smart_spider.core.logger import logger


class ProxyStatus(Enum):
    """代理状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BANNED = "banned"
    TIMEOUT = "timeout"
    TESTING = "testing"


@dataclass
class ProxyInfo:
    """代理信息数据类"""
    url: str
    proxy_type: str = "http"
    status: ProxyStatus = ProxyStatus.ACTIVE
    response_time: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    last_used: Optional[datetime] = None
    last_tested: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        """计算成功率"""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0

    def is_valid(self) -> bool:
        """检查代理是否有效"""
        return self.success_rate >= 0.8 and self.status != ProxyStatus.BANNED


class ProxyManager:
    """代理管理器"""

    def __init__(self):
        self.proxies: List[ProxyInfo] = []
        self.current_index = 0
        self.test_url = "https://httpbin.org/ip"
        self.timeout = 10

    async def add_proxy(self, proxy_url: str, proxy_type: str = "http") -> bool:
        """添加代理"""
        try:
            proxy_info = ProxyInfo(
                url=proxy_url,
                proxy_type=proxy_type,
                status=ProxyStatus.TESTING
            )

            # 测试代理
            is_valid = await self._test_proxy(proxy_info)

            if is_valid:
                self.proxies.append(proxy_info)
                logger.info(f"代理添加成功: {proxy_url}")
                return True
            else:
                logger.warning(f"代理测试失败: {proxy_url}")
                return False

        except Exception as e:
            logger.error(f"添加代理失败: {proxy_url}, 错误: {str(e)}")
            return False

    async def _test_proxy(self, proxy_info: ProxyInfo) -> bool:
        """测试代理"""
        try:
            proxy_info.status = ProxyStatus.TESTING
            proxy_info.last_tested = datetime.now()

            start_time = datetime.now()

            async with aiohttp.ClientSession() as session:
                proxy_url = proxy_info.url
                if not proxy_url.startswith(('http://', 'https://')):
                    proxy_url = f"http://{proxy_url}"

                async with session.get(
                    self.test_url,
                    proxy=proxy_url,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        end_time = datetime.now()
                        proxy_info.response_time = (end_time - start_time).total_seconds()
                        proxy_info.status = ProxyStatus.ACTIVE
                        proxy_info.success_count += 1
                        return True
                    else:
                        proxy_info.status = ProxyStatus.INACTIVE
                        proxy_info.failure_count += 1
                        return False

        except asyncio.TimeoutError:
            proxy_info.status = ProxyStatus.TIMEOUT
            proxy_info.failure_count += 1
            return False
        except Exception as e:
            proxy_info.status = ProxyStatus.INACTIVE
            proxy_info.failure_count += 1
            logger.error(f"代理测试异常: {proxy_info.url}, 错误: {str(e)}")
            return False

    def get_proxy(self) -> Optional[ProxyInfo]:
        """获取下一个可用代理"""
        if not self.proxies:
            return None

        # 找到第一个有效的代理
        for proxy in self.proxies:
            if proxy.is_valid():
                proxy.last_used = datetime.now()
                return proxy

        return None

    def remove_proxy(self, proxy_url: str) -> bool:
        """移除代理"""
        for i, proxy in enumerate(self.proxies):
            if proxy.url == proxy_url:
                del self.proxies[i]
                logger.info(f"代理已移除: {proxy_url}")
                return True
        return False

    async def check_all_proxies(self) -> Dict[str, Any]:
        """检查所有代理"""
        results = {
            "total": len(self.proxies),
            "active": 0,
            "inactive": 0,
            "banned": 0,
            "timeout": 0
        }

        for proxy in self.proxies:
            await self._test_proxy(proxy)

            if proxy.status == ProxyStatus.ACTIVE:
                results["active"] += 1
            elif proxy.status == ProxyStatus.INACTIVE:
                results["inactive"] += 1
            elif proxy.status == ProxyStatus.BANNED:
                results["banned"] += 1
            elif proxy.status == ProxyStatus.TIMEOUT:
                results["timeout"] += 1

        logger.info(f"代理检查完成: {results}")
        return results

    def get_proxy_stats(self) -> Dict[str, Any]:
        """获取代理统计信息"""
        return {
            "total": len(self.proxies),
            "active": sum(1 for p in self.proxies if p.status == ProxyStatus.ACTIVE),
            "inactive": sum(1 for p in self.proxies if p.status == ProxyStatus.INACTIVE),
            "banned": sum(1 for p in self.proxies if p.status == ProxyStatus.BANNED),
            "timeout": sum(1 for p in self.proxies if p.status == ProxyStatus.TIMEOUT),
            "average_response_time": sum(p.response_time for p in self.proxies) / len(self.proxies) if self.proxies else 0
        }


# 全局代理管理器实例
proxy_manager = ProxyManager()


# 快捷函数
def get_proxy_statistics() -> Dict[str, Any]:
    """获取代理统计信息"""
    return proxy_manager.get_proxy_stats()


async def check_proxy_health() -> Dict[str, Any]:
    """检查代理健康状态"""
    return await proxy_manager.check_all_proxies()


async def cleanup_proxies():
    """清理无效代理"""
    original_count = len(proxy_manager.proxies)
    proxy_manager.proxies = [p for p in proxy_manager.proxies if p.is_valid()]
    removed_count = original_count - len(proxy_manager.proxies)

    if removed_count > 0:
        logger.info(f"清理了 {removed_count} 个无效代理")

    return removed_count


__all__ = [
    'ProxyManager',
    'ProxyInfo',
    'ProxyStatus',
    'proxy_manager',
    'get_proxy_statistics',
    'check_proxy_health',
    'cleanup_proxies'
]
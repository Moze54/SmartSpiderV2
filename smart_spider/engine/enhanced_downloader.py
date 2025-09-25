import asyncio
import random
from typing import Dict, List, Optional, Tuple, Any
import aiohttp
from aiohttp import ClientTimeout, ClientSession, ClientResponseError
from fake_useragent import UserAgent

from smart_spider.core.logger import crawler_logger
from smart_spider.config.crawler_config import CrawlerConfig
from smart_spider.engine.retry_handler import AdaptiveRetryHandler, CircuitBreaker
from smart_spider.core.cookie_manager import cookie_manager
from smart_spider.core.exceptions import (
    NetworkException, TimeoutException, RateLimitException,
    ProxyException, ServerException, CookieException
)


class EnhancedDownloader:
    """增强版HTTP下载器 - 支持重试、熔断、Cookie轮换"""

    def __init__(self, config: CrawlerConfig):
        self.config = config
        self.ua = UserAgent()
        self.session: Optional[ClientSession] = None
        self.retry_handler = AdaptiveRetryHandler(
            max_retries=config.retry_times,
            base_delay=config.retry_delay,
            max_delay=60.0,
            exponential_base=2.0,
            jitter=True
        )
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=Exception
        )

        # 统计信息
        self.request_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'retried_requests': 0,
            'total_response_time': 0.0
        }

    async def __aenter__(self):
        """异步上下文管理器入口"""
        timeout = ClientTimeout(total=self.config.timeout)
        connector = aiohttp.TCPConnector(
            limit=self.config.max_concurrent_requests,
            limit_per_host=5,
            ssl=self.config.verify_ssl,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )

        self.session = ClientSession(
            timeout=timeout,
            connector=connector,
            headers=self._get_default_headers(),
            trust_env=True
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()

    def _get_default_headers(self) -> Dict[str, str]:
        """获取默认请求头"""
        user_agent = (
            self.ua.random if self.config.rotate_user_agent
            else self.config.user_agent
        )
        return {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }

    def _get_proxy(self) -> Optional[str]:
        """获取代理"""
        if not self.config.use_proxy or not self.config.proxy_list:
            return None

        if self.config.proxy_rotation:
            return random.choice(self.config.proxy_list)
        else:
            return self.config.proxy_list[0]

    def _get_cookies(self, url: str) -> Optional[Dict[str, str]]:
        """获取Cookie"""
        if not self.config.use_cookies:
            return None

        # 从URL提取域名
        from urllib.parse import urlparse
        domain = urlparse(url).netloc

        if self.config.cookie_domain and domain != self.config.cookie_domain:
            return None

        try:
            # 尝试轮换Cookie
            cookies = cookie_manager.rotate_cookies(domain)
            if cookies:
                crawler_logger.info(f"使用轮换Cookie: {domain} ({len(cookies)}个)")
                return cookies

            # 如果没有可用的Cookie，尝试从浏览器获取
            cookies = cookie_manager.get_browser_cookies(domain)
            if cookies:
                cookie_manager.save_cookies(cookies, domain, "browser")
                crawler_logger.info(f"从浏览器获取Cookie: {domain} ({len(cookies)}个)")
                return cookies

        except Exception as e:
            crawler_logger.warning(f"获取Cookie失败: {domain} - {str(e)}")

        return None

    def _should_retry_on_exception(self, exception: Exception, url: str) -> bool:
        """判断是否应该基于异常重试"""
        # 速率限制异常
        if isinstance(exception, RateLimitException):
            crawler_logger.warning(f"速率限制，需要等待后重试: {url}")
            return True

        # 代理异常
        if isinstance(exception, ProxyException):
            crawler_logger.warning(f"代理错误，需要更换代理后重试: {url}")
            return True

        # Cookie异常
        if isinstance(exception, CookieException):
            crawler_logger.warning(f"Cookie错误，需要更换Cookie后重试: {url}")
            return True

        # 服务器异常
        if isinstance(exception, ServerException):
            crawler_logger.warning(f"服务器错误，需要等待后重试: {url}")
            return True

        # 网络超时
        if isinstance(exception, (asyncio.TimeoutError, TimeoutException)):
            crawler_logger.warning(f"网络超时，需要重试: {url}")
            return True

        # 连接错误
        if isinstance(exception, (aiohttp.ClientOSError, aiohttp.ServerDisconnectedError)):
            crawler_logger.warning(f"连接错误，需要重试: {url}")
            return True

        return False

    async def _make_request_with_retry(
        self,
        url: str,
        method: str = 'GET',
        headers: Optional[Dict] = None,
        cookies: Optional[Dict] = None,
        data: Optional[Dict] = None,
        proxy: Optional[str] = None,
        **kwargs
    ) -> Tuple[int, str, float]:
        """执行HTTP请求（带重试逻辑）"""

        async def _single_request() -> Tuple[int, str, float]:
            """单次请求"""
            if not self.session:
                raise RuntimeError("Downloader未初始化，请使用async with")

            request_headers = {**self._get_default_headers(), **(headers or {})}

            start_time = asyncio.get_event_loop().time()

            try:
                async with self.session.request(
                    method=method,
                    url=url,
                    headers=request_headers,
                    cookies=cookies,
                    data=data,
                    proxy=proxy,
                    allow_redirects=self.config.follow_redirects,
                    max_redirects=self.config.max_redirects,
                    **kwargs
                ) as response:
                    content = await response.text()
                    response_time = asyncio.get_event_loop().time() - start_time

                    # 检查速率限制
                    if response.status == 429:
                        retry_after = response.headers.get('Retry-After')
                        if retry_after:
                            wait_time = int(retry_after)
                            crawler_logger.warning(f"速率限制，等待 {wait_time} 秒: {url}")
                            await asyncio.sleep(wait_time)
                        raise RateLimitException(f"速率限制: {url}")

                    # 检查服务器错误
                    if response.status in [500, 502, 503, 504]:
                        raise ServerException(f"服务器错误 {response.status}: {url}")

                    # 检查代理错误
                    if response.status in [407, 502, 503] and proxy:
                        raise ProxyException(f"代理错误 {response.status}: {proxy}")

                    # 检查Cookie错误
                    if response.status in [401, 403] and cookies:
                        raise CookieException(f"Cookie错误 {response.status}: {url}")

                    crawler_logger.info(
                        f"HTTP请求完成: {response.status} - {url}",
                        extra={
                            'url': url,
                            'status': response.status,
                            'response_time': response_time,
                            'proxy': proxy is not None,
                            'cookies': cookies is not None
                        }
                    )

                    return response.status, content, response_time

            except asyncio.TimeoutError:
                response_time = asyncio.get_event_loop().time() - start_time
                crawler_logger.error(f"请求超时: {url} (耗时: {response_time:.2f}s)")
                raise TimeoutException(f"请求超时: {url}")

            except ClientResponseError as e:
                response_time = asyncio.get_event_loop().time() - start_time
                crawler_logger.error(
                    f"HTTP错误: {e.status} - {url}",
                    extra={'status': e.status, 'url': url, 'response_time': response_time}
                )

                # 检查是否需要重试的HTTP状态码
                if e.status in self.retry_handler.retry_status_codes:
                    if e.status == 429:
                        raise RateLimitException(f"速率限制: {url}")
                    elif e.status in [500, 502, 503, 504]:
                        raise ServerException(f"服务器错误 {e.status}: {url}")
                    else:
                        raise NetworkException(f"网络错误 {e.status}: {url}")

                return e.status, "", response_time

            except aiohttp.ClientOSError as e:
                response_time = asyncio.get_event_loop().time() - start_time
                crawler_logger.error(f"连接错误: {url} - {str(e)}")
                raise NetworkException(f"连接错误: {url}")

            except Exception as e:
                response_time = asyncio.get_event_loop().time() - start_time
                crawler_logger.error(f"请求失败: {url} - {str(e)}")
                raise NetworkException(f"请求失败: {url}")

        # 使用重试处理器执行请求
        try:
            return await self.retry_handler.execute_with_retry(_single_request)
        except Exception as e:
            if self._should_retry_on_exception(e, url):
                # 如果是可以重试的异常，重新抛出让上层处理
                raise
            else:
                # 如果是不可重试的异常，返回错误状态
                return 0, "", 0.0

    async def download(
        self,
        url: str,
        method: str = 'GET',
        headers: Optional[Dict] = None,
        cookies: Optional[Dict] = None,
        data: Optional[Dict] = None,
        **kwargs
    ) -> Tuple[int, str, float]:
        """下载单个URL（增强版）"""

        # 更新统计信息
        self.request_stats['total_requests'] += 1

        try:
            # 添加随机延迟
            if self.config.randomize_delay:
                delay = random.uniform(*self.config.delay_range)
                await asyncio.sleep(delay)

            # 获取代理
            proxy = self._get_proxy()

            # 获取Cookie（如果没有提供）
            if not cookies and self.config.use_cookies:
                cookies = self._get_cookies(url)

            # 执行请求
            status_code, content, response_time = await self._make_request_with_retry(
                url=url,
                method=method,
                headers=headers,
                cookies=cookies,
                data=data,
                proxy=proxy,
                **kwargs
            )

            # 更新统计信息
            if status_code == 200:
                self.request_stats['successful_requests'] += 1
            else:
                self.request_stats['failed_requests'] += 1

            self.request_stats['total_response_time'] += response_time

            return status_code, content, response_time

        except Exception as e:
            self.request_stats['failed_requests'] += 1
            crawler_logger.error(f"下载失败: {url} - {str(e)}")
            raise

    async def download_batch(
        self,
        urls: List[str],
        method: str = 'GET',
        headers: Optional[Dict] = None,
        cookies: Optional[Dict] = None,
        data: Optional[Dict] = None,
        max_concurrent: int = None
    ) -> List[Tuple[int, str, float]]:
        """批量下载（增强版）"""
        if not max_concurrent:
            max_concurrent = self.config.concurrent_limit

        semaphore = asyncio.Semaphore(max_concurrent)

        async def _download_single(url: str) -> Tuple[int, str, float]:
            async with semaphore:
                try:
                    return await self.download(url, method, headers, cookies, data)
                except Exception as e:
                    crawler_logger.error(f"批量下载失败: {url} - {str(e)}")
                    return 0, "", 0.0

        tasks = [_download_single(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def get_stats(self) -> Dict[str, Any]:
        """获取下载统计信息"""
        total = self.request_stats['total_requests']
        successful = self.request_stats['successful_requests']
        failed = self.request_stats['failed_requests']

        avg_response_time = (
            self.request_stats['total_response_time'] / total
            if total > 0 else 0.0
        )

        return {
            'total_requests': total,
            'successful_requests': successful,
            'failed_requests': failed,
            'success_rate': successful / total if total > 0 else 0.0,
            'average_response_time': avg_response_time,
            'retry_stats': self.retry_handler.get_stats()
        }

    async def health_check(self, test_url: str = "https://httpbin.org/status/200") -> bool:
        """健康检查"""
        try:
            status, content, response_time = await self.download(test_url)
            return status == 200
        except Exception as e:
            crawler_logger.error(f"健康检查失败: {str(e)}")
            return False\n\n# 增强的爬虫引擎将在 crawler.py 中调用这个下载器\n# 这里只是一个下载器组件，具体的爬虫逻辑在引擎中实现
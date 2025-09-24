import asyncio
import random
from typing import Dict, List, Optional, Tuple
import aiohttp
from aiohttp import ClientTimeout, ClientSession
from fake_useragent import UserAgent

from smart_spider.core.logger import crawler_logger
from smart_spider.config.crawler_config import CrawlerConfig


class Downloader:
    """HTTP下载器"""

    def __init__(self, config: CrawlerConfig):
        self.config = config
        self.ua = UserAgent()
        self.session: Optional[ClientSession] = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        timeout = ClientTimeout(total=self.config.timeout)
        connector = aiohttp.TCPConnector(
            limit=self.config.max_concurrent_requests,
            limit_per_host=5,
            ssl=self.config.verify_ssl
        )

        self.session = ClientSession(
            timeout=timeout,
            connector=connector,
            headers=self._get_default_headers()
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
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

    def _get_proxy(self) -> Optional[str]:
        """获取代理"""
        if not self.config.use_proxy or not self.config.proxy_list:
            return None

        if self.config.proxy_rotation:
            return random.choice(self.config.proxy_list)
        else:
            return self.config.proxy_list[0]

    async def _make_request(
        self,
        url: str,
        method: str = 'GET',
        headers: Optional[Dict] = None,
        cookies: Optional[Dict] = None,
        data: Optional[Dict] = None,
        proxy: Optional[str] = None
    ) -> Tuple[int, str, float]:
        """执行HTTP请求"""
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
                max_redirects=self.config.max_redirects
            ) as response:
                content = await response.text()
                response_time = asyncio.get_event_loop().time() - start_time

                crawler_logger.info(
                    f"HTTP请求完成",
                    extra={
                        'url': url,
                        'status': response.status,
                        'response_time': response_time
                    }
                )

                return response.status, content, response_time

        except asyncio.TimeoutError:
            crawler_logger.error(f"请求超时: {url}")
            raise
        except aiohttp.ClientError as e:
            crawler_logger.error(f"请求失败: {url} - {str(e)}")
            raise

    async def download(
        self,
        url: str,
        method: str = 'GET',
        headers: Optional[Dict] = None,
        cookies: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Tuple[int, str, float]:
        """下载单个URL"""
        proxy = self._get_proxy()

        # 添加随机延迟
        if self.config.randomize_delay:
            delay = random.uniform(*self.config.delay_range)
            await asyncio.sleep(delay)

        return await self._make_request(url, method, headers, cookies, data, proxy)

    async def download_batch(
        self,
        urls: List[str],
        method: str = 'GET',
        headers: Optional[Dict] = None,
        cookies: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> List[Tuple[int, str, float]]:
        """批量下载"""
        semaphore = asyncio.Semaphore(self.config.concurrent_limit)

        async def _download_single(url: str) -> Tuple[int, str, float]:
            async with semaphore:
                return await self.download(url, method, headers, cookies, data)

        tasks = [_download_single(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)
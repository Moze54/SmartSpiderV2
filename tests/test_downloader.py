import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from smart_spider.engine.downloader import Downloader
from smart_spider.config.crawler_config import CrawlerConfig


class TestDownloader:
    """测试下载器"""

    def setup_method(self):
        """设置测试环境"""
        self.config = CrawlerConfig(
            max_concurrent_requests=5,
            request_delay=0.1,
            timeout=10,
            retry_times=2,
            retry_delay=0.1,
            user_agent="TestBot/1.0"
        )

    @pytest.mark.asyncio
    async def test_downloader_initialization(self):
        """测试下载器初始化"""
        async with Downloader(self.config) as downloader:
            assert downloader.config == self.config
            assert downloader.session is not None

    @pytest.mark.asyncio
    async def test_download_success(self):
        """测试成功下载"""
        async with Downloader(self.config) as downloader:
            with patch('aiohttp.ClientSession.get') as mock_get:
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.text = AsyncMock(return_value="<html><body>Test</body></html>")
                mock_response.__aenter__.return_value = mock_response
                mock_get.return_value = mock_response

                status, content, response_time = await downloader.download(
                    "https://example.com"
                )
                assert status == 200
                assert content == "<html><body>Test</body></html>"
                assert response_time > 0

    @pytest.mark.asyncio
    async def test_download_timeout(self):
        """测试下载超时"""
        async with Downloader(self.config) as downloader:
            with patch('aiohttp.ClientSession.get') as mock_get:
                mock_get.side_effect = asyncio.TimeoutError()

                status, content, response_time = await downloader.download(
                    "https://example.com"
                )
                assert status == 408
                assert "超时" in str(content)

    @pytest.mark.asyncio
    async def test_download_connection_error(self):
        """测试连接错误"""
        async with Downloader(self.config) as downloader:
            with patch('aiohttp.ClientSession.get') as mock_get:
                mock_get.side_effect = Exception("Connection failed")

                status, content, response_time = await downloader.download(
                    "https://example.com"
                )
                assert status == 500
                assert "连接失败" in str(content)

    @pytest.mark.asyncio
    async def test_proxy_rotation(self):
        """测试代理轮换"""
        config = CrawlerConfig(
            max_concurrent_requests=5,
            timeout=10,
            proxies=["http://proxy1:8080", "http://proxy2:8080"],
            proxy_rotation=True
        )

        async with Downloader(config) as downloader:
            proxy1 = downloader._get_proxy()
            proxy2 = downloader._get_proxy()
            assert proxy1 != proxy2  # 应该轮换代理

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """测试速率限制"""
        config = CrawlerConfig(
            max_concurrent_requests=2,
            request_delay=0.1,
            timeout=10
        )

        async with Downloader(config) as downloader:
            start_time = asyncio.get_event_loop().time()

            # 快速发起多个请求
            tasks = [
                downloader.download("https://example.com"),
                downloader.download("https://example.com"),
                downloader.download("https://example.com")
            ]

            # 模拟请求完成
            with patch('aiohttp.ClientSession.get') as mock_get:
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.text = AsyncMock(return_value="test")
                mock_response.__aenter__.return_value = mock_response
                mock_get.return_value = mock_response

                await asyncio.gather(*tasks)

            # 验证速率限制
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            assert duration >= 0.1  # 应该有延迟
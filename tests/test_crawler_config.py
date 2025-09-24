import pytest
from pydantic import ValidationError
from smart_spider.config.crawler_config import TaskConfig, CrawlerConfig, ParseConfig, ProxyConfig


class TestTaskConfig:
    """测试任务配置"""

    def test_valid_task_config(self):
        """测试有效的任务配置"""
        config = TaskConfig(
            name="测试任务",
            description="测试描述",
            urls=["https://example.com"],
            max_concurrent_requests=5,
            timeout=30
        )
        assert config.name == "测试任务"
        assert len(config.urls) == 1
        assert config.max_concurrent_requests == 5

    def test_invalid_url(self):
        """测试无效的URL"""
        with pytest.raises(ValidationError):
            TaskConfig(
                name="测试任务",
                urls=["invalid-url"],
                max_concurrent_requests=5
            )

    def test_empty_urls(self):
        """测试空URL列表"""
        with pytest.raises(ValidationError):
            TaskConfig(
                name="测试任务",
                urls=[],
                max_concurrent_requests=5
            )


class TestCrawlerConfig:
    """测试爬虫配置"""

    def test_valid_crawler_config(self):
        """测试有效的爬虫配置"""
        config = CrawlerConfig(
            max_concurrent_requests=10,
            request_delay=1.0,
            timeout=30,
            retry_times=3,
            retry_delay=2.0,
            user_agent="TestBot/1.0"
        )
        assert config.max_concurrent_requests == 10
        assert config.request_delay == 1.0

    def test_invalid_concurrent_requests(self):
        """测试无效的并发请求数"""
        with pytest.raises(ValidationError):
            CrawlerConfig(
                max_concurrent_requests=0,
                timeout=30
            )


class TestParseConfig:
    """测试解析配置"""

    def test_valid_parse_config(self):
        """测试有效的解析配置"""
        config = ParseConfig(
            selector_type="css",
            parse_rules={"title": "h1", "content": ".content"},
            extract_links=True,
            extract_images=True
        )
        assert config.selector_type == "css"
        assert len(config.parse_rules) == 2

    def test_invalid_selector_type(self):
        """测试无效的选择器类型"""
        with pytest.raises(ValidationError):
            ParseConfig(
                selector_type="invalid",
                parse_rules={}
            )


class TestProxyConfig:
    """测试代理配置"""

    def test_valid_proxy_config(self):
        """测试有效的代理配置"""
        config = ProxyConfig(
            enabled=True,
            proxies=["http://proxy1:8080", "http://proxy2:8080"],
            rotate=True
        )
        assert config.enabled is True
        assert len(config.proxies) == 2

    def test_empty_proxies_with_rotation(self):
        """测试空代理列表但启用轮换"""
        config = ProxyConfig(
            enabled=True,
            proxies=[],
            rotate=True
        )
        assert config.enabled is True
        assert len(config.proxies) == 0
import pytest
from smart_spider.core.exceptions import (
    SmartSpiderException,
    TaskNotFoundException,
    TaskConflictException,
    CrawlerException,
    ValidationException,
    NetworkException,
    TimeoutException
)


class TestExceptions:
    """测试异常类"""

    def test_smart_spider_exception(self):
        """测试基础异常类"""
        exc = SmartSpiderException("测试错误", code=400, details={"key": "value"})
        assert str(exc) == "测试错误"
        assert exc.code == 400
        assert exc.details == {"key": "value"}

    def test_task_not_found_exception(self):
        """测试任务不存在异常"""
        exc = TaskNotFoundException("test-task-id")
        assert "test-task-id" in str(exc)
        assert exc.code == 404
        assert exc.details == {"task_id": "test-task-id"}

    def test_task_conflict_exception(self):
        """测试任务冲突异常"""
        exc = TaskConflictException("任务冲突", "test-task-id")
        assert str(exc) == "任务冲突"
        assert exc.code == 409
        assert exc.details == {"task_id": "test-task-id"}

    def test_crawler_exception(self):
        """测试爬虫异常"""
        exc = CrawlerException("爬取失败", "https://example.com", {"error": "timeout"})
        assert str(exc) == "爬取失败"
        assert exc.code == 500
        assert exc.details["url"] == "https://example.com"

    def test_validation_exception(self):
        """测试验证异常"""
        exc = ValidationException("参数错误", "url", "invalid-url")
        assert str(exc) == "参数错误"
        assert exc.code == 400
        assert exc.details["field"] == "url"
        assert exc.details["value"] == "invalid-url"

    def test_network_exception(self):
        """测试网络异常"""
        exc = NetworkException("网络错误", "https://example.com", 500)
        assert str(exc) == "网络错误"
        assert exc.code == 500
        assert exc.details["url"] == "https://example.com"
        assert exc.details["status_code"] == 500

    def test_timeout_exception(self):
        """测试超时异常"""
        exc = TimeoutException("请求超时", timeout=30)
        assert str(exc) == "请求超时"
        assert exc.code == 408
        assert exc.details["timeout"] == 30
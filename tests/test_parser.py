import pytest
from bs4 import BeautifulSoup
from smart_spider.engine.parser import Parser
from smart_spider.config.crawler_config import ParseConfig


class TestParser:
    """测试解析器"""

    def setup_method(self):
        """设置测试环境"""
        self.html_content = """
        <html>
            <head><title>测试页面</title></head>
            <body>
                <h1 class="title">主标题</h1>
                <div class="content">
                    <p>这是第一段内容</p>
                    <p>这是第二段内容</p>
                </div>
                <ul class="list">
                    <li>项目1</li>
                    <li>项目2</li>
                    <li>项目3</li>
                </ul>
                <div class="links">
                    <a href="https://example.com/page1">链接1</a>
                    <a href="https://example.com/page2">链接2</a>
                </div>
                <img src="https://example.com/image1.jpg" alt="图片1">
                <img src="https://example.com/image2.jpg" alt="图片2">
            </body>
        </html>
        """

    def test_css_selector_parsing(self):
        """测试CSS选择器解析"""
        config = ParseConfig(
            selector_type="css",
            parse_rules={
                "title": "h1.title",
                "content": "div.content p",
                "list_items": "ul.list li"
            },
            extract_links=True,
            extract_images=True
        )

        parser = Parser(config)
        results = parser.parse_html(self.html_content, "https://example.com")

        assert len(results) > 0
        first_result = results[0]
        assert "title" in first_result
        assert first_result["title"] == "主标题"
        assert first_result["content"] == "这是第一段内容"
        assert first_result["list_items"] == "项目1"

    def test_xpath_selector_parsing(self):
        """测试XPath选择器解析"""
        config = ParseConfig(
            selector_type="xpath",
            parse_rules={
                "title": "//h1[@class='title']/text()",
                "content": "//div[@class='content']/p[1]/text()",
                "list_count": "count(//ul[@class='list']/li)"
            }
        )

        parser = Parser(config)
        results = parser.parse_html(self.html_content, "https://example.com")

        assert len(results) > 0
        first_result = results[0]
        assert "title" in first_result
        assert first_result["title"] == "主标题"
        assert first_result["content"] == "这是第一段内容"

    def test_link_extraction(self):
        """测试链接提取"""
        config = ParseConfig(
            selector_type="css",
            parse_rules={},
            extract_links=True
        )

        parser = Parser(config)
        results = parser.parse_html(self.html_content, "https://example.com")

        assert len(results) > 0
        first_result = results[0]
        assert "links" in first_result
        links = first_result["links"]
        assert len(links) == 2
        assert links[0]["href"] == "https://example.com/page1"
        assert links[0]["text"] == "链接1"

    def test_image_extraction(self):
        """测试图片提取"""
        config = ParseConfig(
            selector_type="css",
            parse_rules={},
            extract_images=True
        )

        parser = Parser(config)
        results = parser.parse_html(self.html_content, "https://example.com")

        assert len(results) > 0
        first_result = results[0]
        assert "images" in first_result
        images = first_result["images"]
        assert len(images) == 2
        assert images[0]["src"] == "https://example.com/image1.jpg"
        assert images[0]["alt"] == "图片1"

    def test_empty_html(self):
        """测试空HTML内容"""
        config = ParseConfig(
            selector_type="css",
            parse_rules={"title": "h1"}
        )

        parser = Parser(config)
        results = parser.parse_html("", "https://example.com")

        assert len(results) == 0

    def test_invalid_html(self):
        """测试无效的HTML内容"""
        config = ParseConfig(
            selector_type="css",
            parse_rules={"title": "h1"}
        )

        parser = Parser(config)
        invalid_html = "<p>这不是完整的HTML文档"
        results = parser.parse_html(invalid_html, "https://example.com")

        # 应该能够处理并返回空结果
        assert isinstance(results, list)

    def test_multiple_items_extraction(self):
        """测试多项目提取"""
        config = ParseConfig(
            selector_type="css",
            parse_rules={"item": "ul.list li"},
            multiple_items=True
        )

        parser = Parser(config)
        results = parser.parse_html(self.html_content, "https://example.com")

        # 应该返回3个结果，每个li元素一个
        assert len(results) == 3
        for i, result in enumerate(results):
            assert "item" in result
            assert result["item"] == f"项目{i + 1}"

    def test_no_matching_elements(self):
        """测试没有匹配元素的情况"""
        config = ParseConfig(
            selector_type="css",
            parse_rules={"nonexistent": ".nonexistent-class"}
        )

        parser = Parser(config)
        results = parser.parse_html(self.html_content, "https://example.com")

        # 应该返回空结果
        assert len(results) == 0
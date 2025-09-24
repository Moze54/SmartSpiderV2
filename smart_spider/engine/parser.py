import re
from typing import Any, Dict, List, Optional, Union
from bs4 import BeautifulSoup
from lxml import etree, html

from smart_spider.core.logger import crawler_logger
from smart_spider.config.crawler_config import ParseConfig


class Parser:
    """数据解析器"""

    def __init__(self, config: ParseConfig):
        self.config = config

    def parse_html(self, html_content: str, url: str) -> List[Dict[str, Any]]:
        """解析HTML内容"""
        if self.config.selector_type.lower() == "css":
            return self._parse_by_css(html_content, url)
        elif self.config.selector_type.lower() == "xpath":
            return self._parse_by_xpath(html_content, url)
        else:
            raise ValueError(f"不支持的选择器类型: {self.config.selector_type}")

    def _parse_by_css(self, html_content: str, url: str) -> List[Dict[str, Any]]:
        """使用CSS选择器解析"""
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            results = []

            # 解析规则
            rules = self.config.rules
            if not rules:
                return []

            # 提取数据
            data = {'url': url}
            for field, selector in rules.items():
                try:
                    if selector.endswith('::text'):
                        css_selector = selector[:-6]
                        elements = soup.select(css_selector)
                        values = [elem.get_text(strip=True) for elem in elements]
                        data[field] = values if len(values) > 1 else values[0] if values else None
                    elif selector.endswith('::attr()'):
                        css_selector = selector[:-8]
                        attr_name = selector.split('::attr(')[1].rstrip(')')
                        elements = soup.select(css_selector)
                        values = [elem.get(attr_name) for elem in elements if elem.get(attr_name)]
                        data[field] = values if len(values) > 1 else values[0] if values else None
                    else:
                        elements = soup.select(selector)
                        values = [elem.get_text(strip=True) for elem in elements]
                        data[field] = values if len(values) > 1 else values[0] if values else None

                    # 数据清洗
                    if self.config.clean_whitespace and data[field]:
                        if isinstance(data[field], list):
                            data[field] = [re.sub(r'\s+', ' ', str(v)).strip() for v in data[field]]
                        else:
                            data[field] = re.sub(r'\s+', ' ', str(data[field])).strip()

                    if self.config.clean_html and data[field]:
                        if isinstance(data[field], list):
                            data[field] = [self._clean_html_tags(str(v)) for v in data[field]]
                        else:
                            data[field] = self._clean_html_tags(str(data[field]))

                except Exception as e:
                    crawler_logger.error(f"解析字段 {field} 失败: {str(e)}")
                    data[field] = None

            results.append(data)
            return results

        except Exception as e:
            crawler_logger.error(f"CSS解析失败: {str(e)}")
            return []

    def _parse_by_xpath(self, html_content: str, url: str) -> List[Dict[str, Any]]:
        """使用XPath解析"""
        try:
            tree = html.fromstring(html_content)
            results = []

            # 解析规则
            rules = self.config.rules
            if not rules:
                return []

            # 提取数据
            data = {'url': url}
            for field, xpath in rules.items():
                try:
                    elements = tree.xpath(xpath)
                    if elements:
                        if len(elements) > 1:
                            values = [str(elem).strip() for elem in elements]
                            data[field] = values
                        else:
                            data[field] = str(elements[0]).strip()
                    else:
                        data[field] = None

                    # 数据清洗
                    if self.config.clean_whitespace and data[field]:
                        if isinstance(data[field], list):
                            data[field] = [re.sub(r'\s+', ' ', str(v)).strip() for v in data[field]]
                        else:
                            data[field] = re.sub(r'\s+', ' ', str(data[field])).strip()

                    if self.config.clean_html and data[field]:
                        if isinstance(data[field], list):
                            data[field] = [self._clean_html_tags(str(v)) for v in data[field]]
                        else:
                            data[field] = self._clean_html_tags(str(data[field]))

                except Exception as e:
                    crawler_logger.error(f"解析字段 {field} 失败: {str(e)}")
                    data[field] = None

            results.append(data)
            return results

        except Exception as e:
            crawler_logger.error(f"XPath解析失败: {str(e)}")
            return []

    def _clean_html_tags(self, text: str) -> str:
        """清除HTML标签"""
        clean = re.compile('<.*?\u003e')
        return re.sub(clean, '', text)

    def extract_links(self, html_content: str, base_url: str) -> List[str]:
        """提取页面中的链接"""
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            links = []

            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('http'):
                    links.append(href)
                elif href.startswith('/'):
                    from urllib.parse import urljoin
                    links.append(urljoin(base_url, href))

            return list(set(links))  # 去重
        except Exception as e:
            crawler_logger.error(f"提取链接失败: {str(e)}")
            return []

    def extract_images(self, html_content: str, base_url: str) -> List[str]:
        """提取页面中的图片"""
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            images = []

            for img in soup.find_all('img', src=True):
                src = img['src']
                if src.startswith('http'):
                    images.append(src)
                elif src.startswith('/'):
                    from urllib.parse import urljoin
                    images.append(urljoin(base_url, src))

            return list(set(images))  # 去重
        except Exception as e:
            crawler_logger.error(f"提取图片失败: {str(e)}")
            return []

    def extract_emails(self, text: str) -> List[str]:
        """提取邮箱地址"""
        try:
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, text)
            return list(set(emails))
        except Exception as e:
            crawler_logger.error(f"提取邮箱失败: {str(e)}")
            return []

    def extract_phone_numbers(self, text: str) -> List[str]:
        """提取电话号码"""
        try:
            phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
            phones = re.findall(phone_pattern, text)
            return list(set(phones))
        except Exception as e:
            crawler_logger.error(f"提取电话号码失败: {str(e)}")
            return []

    def extract_by_regex(self, text: str, pattern: str) -> List[str]:
        """使用正则表达式提取数据"""
        try:
            matches = re.findall(pattern, text)
            return list(set(matches))
        except Exception as e:
            crawler_logger.error(f"正则表达式提取失败: {str(e)}")
            return []
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator


class CrawlerConfig(BaseModel):
    """爬虫核心配置"""

    # 基础配置
    max_concurrent_requests: int = Field(default=10, description="最大并发请求数")
    request_delay: float = Field(default=1.0, description="请求间隔(秒)")
    randomize_delay: bool = Field(default=True, description="随机化请求间隔")

    # 超时配置
    timeout: int = Field(default=30, description="请求超时时间(秒)")
    retry_times: int = Field(default=3, description="重试次数")
    retry_delay: float = Field(default=1.0, description="重试间隔(秒)")

    # 用户代理
    user_agent: str = Field(
        default="SmartSpider/1.0",
        description="User-Agent"
    )
    rotate_user_agent: bool = Field(default=True, description="轮换User-Agent")

    # 代理配置
    use_proxy: bool = Field(default=False, description="是否使用代理")
    proxy_list: List[str] = Field(default_factory=list, description="代理列表")
    proxy_rotation: bool = Field(default=True, description="代理轮换")

    # Cookie配置
    use_cookies: bool = Field(default=False, description="是否使用Cookie")
    cookie_domain: Optional[str] = Field(default=None, description="Cookie域名")

    # 反反爬配置
    follow_redirects: bool = Field(default=True, description="跟随重定向")
    max_redirects: int = Field(default=10, description="最大重定向次数")
    verify_ssl: bool = Field(default=True, description="SSL验证")

    # 限速配置
    concurrent_limit: int = Field(default=5, description="并发限制")
    delay_range: tuple = Field(default=(1, 3), description="延迟范围")

    @validator('max_concurrent_requests')
    def validate_concurrent_requests(cls, v):
        if v < 1 or v > 100:
            raise ValueError('max_concurrent_requests必须在1-100之间')
        return v

    @validator('timeout')
    def validate_timeout(cls, v):
        if v < 1 or v > 300:
            raise ValueError('timeout必须在1-300秒之间')
        return v


class ParseConfig(BaseModel):
    """解析配置"""

    # 解析规则
    rules: Dict[str, str] = Field(default_factory=dict, description="解析规则")

    # 选择器类型
    selector_type: str = Field(default="css", description="选择器类型(css/xpath)")

    # 数据清洗
    clean_whitespace: bool = Field(default=True, description="清除空白字符")
    clean_html: bool = Field(default=True, description="清除HTML标签")

    # 分页配置
    pagination: bool = Field(default=False, description="是否分页")
    next_page_selector: Optional[str] = Field(default=None, description="下一页选择器")
    max_pages: int = Field(default=1, description="最大页数")


class StorageConfig(BaseModel):
    """存储配置"""

    # 存储类型
    storage_type: str = Field(default="json", description="存储类型(json/csv/database)")

    # 文件配置
    output_dir: str = Field(default="./output", description="输出目录")
    filename_template: str = Field(default="{task_id}_{timestamp}", description="文件名模板")

    # 数据库配置
    mysql_config: Optional[Dict] = Field(default=None, description="MySQL配置")
    redis_config: Optional[Dict] = Field(default=None, description="Redis配置")


class TaskConfig(BaseModel):
    """任务配置"""

    name: str = Field(..., description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")

    # 目标配置
    urls: List[str] = Field(..., description="目标URL列表")

    # 子配置
    crawler: CrawlerConfig = Field(default_factory=CrawlerConfig)
    parse: ParseConfig = Field(default_factory=ParseConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)

    # 任务选项
    priority: int = Field(default=0, description="优先级")
    max_items: Optional[int] = Field(None, description="最大抓取数量")

    class Config:
        schema_extra = {
            "example": {
                "name": "示例爬虫任务",
                "description": "这是一个示例爬虫任务",
                "urls": ["https://example.com"],
                "crawler": {
                    "max_concurrent_requests": 5,
                    "request_delay": 1.0,
                    "timeout": 30
                },
                "parse": {
                    "rules": {
                        "title": "title::text",
                        "content": ".content::text"
                    },
                    "selector_type": "css"
                },
                "storage": {
                    "storage_type": "json",
                    "output_dir": "./output"
                }
            }
        }
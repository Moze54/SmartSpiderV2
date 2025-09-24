from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime

from smart_spider.models.database import TaskStatus


class TaskCreateRequest(BaseModel):
    """创建任务请求"""
    name: str = Field(..., description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    urls: List[str] = Field(..., description="目标URL列表")

    # 爬虫配置
    max_concurrent_requests: int = Field(default=5, description="最大并发请求数")
    request_delay: float = Field(default=1.0, description="请求间隔(秒)")
    timeout: int = Field(default=30, description="超时时间(秒)")
    retry_times: int = Field(default=3, description="重试次数")

    # 解析配置
    parse_rules: Dict[str, str] = Field(default_factory=dict, description="解析规则")
    selector_type: str = Field(default="css", description="选择器类型")

    # 存储配置
    storage_type: str = Field(default="json", description="存储类型")
    output_dir: str = Field(default="./output", description="输出目录")

    # 其他配置
    max_items: Optional[int] = Field(None, description="最大抓取数量")
    priority: int = Field(default=0, description="优先级")

    class Config:
        schema_extra = {
            "example": {
                "name": "示例爬虫任务",
                "description": "爬取示例网站的数据",
                "urls": ["https://example.com"],
                "max_concurrent_requests": 3,
                "request_delay": 1.0,
                "timeout": 30,
                "parse_rules": {
                    "title": "title::text",
                    "content": ".content::text"
                },
                "storage_type": "json",
                "output_dir": "./output"
            }
        }


class TaskResponse(BaseModel):
    """任务响应"""
    task_id: str
    name: str
    description: Optional[str]
    urls: List[str]
    status: TaskStatus
    progress: float
    total_count: int
    success_count: int
    failed_count: int
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        orm_mode = True


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    name: str
    status: TaskStatus
    progress: float
    results_count: int


class TaskResultResponse(BaseModel):
    """任务结果响应"""
    id: int
    task_id: str
    data: Dict[str, Any]
    url: str
    status_code: int
    response_time: float
    created_at: datetime

    class Config:
        orm_mode = True


class TaskListResponse(BaseModel):
    """任务列表响应"""
    total: int
    items: List[TaskResponse]


class TaskActionResponse(BaseModel):
    """任务操作响应"""
    success: bool
    message: str


class TaskQueryRequest(BaseModel):
    """任务查询请求"""
    status: Optional[TaskStatus] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
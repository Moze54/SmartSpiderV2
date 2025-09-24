from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    url: HttpUrl
    spider_config: dict = Field(default_factory=dict)

class TaskCreateResponse(BaseModel):
    task_id: str
    status: TaskStatus
    created_at: datetime

class TaskQueryResponse(BaseModel):
    task_id: str
    name: str
    url: str
    status: TaskStatus
    total_url_count: int = 0
    success_url_count: int = 0
    failed_url_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime]
    runtime: Optional[str] = None          # 人性化耗时字符串

class TaskPageResponse(BaseModel):
    total: int
    page: int
    size: int
    items: list[TaskQueryResponse]

class CancelResp(BaseModel):
    task_id: str
    status: str
    message: str
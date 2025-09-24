from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from sqlalchemy import JSON, Column, DateTime, Enum as SQLEnum, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlmodel import Field, SQLModel

Base = declarative_base()


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(SQLModel, table=True):
    """任务模型"""
    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str = Field(unique=True, index=True, description="任务唯一标识")
    name: str = Field(description="任务名称")
    description: Optional[str] = Field(default=None, description="任务描述")

    # 目标配置
    urls: List[str] = Field(default_factory=list, sa_column=Column(JSON))

    # 爬虫配置
    config: Dict = Field(default_factory=dict, sa_column=Column(JSON))

    # 状态信息
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    progress: float = Field(default=0.0, description="任务进度")

    # 统计信息
    total_count: int = Field(default=0, description="总数量")
    success_count: int = Field(default=0, description="成功数量")
    failed_count: int = Field(default=0, description="失败数量")

    # 时间戳
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)


class TaskResult(SQLModel, table=True):
    """任务结果模型"""
    __tablename__ = "task_results"

    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str = Field(index=True)

    # 结果数据
    data: Dict = Field(sa_column=Column(JSON))
    url: str = Field(description="数据来源URL")

    # 元数据
    status_code: int = Field(description="HTTP状态码")
    response_time: float = Field(description="响应时间")

    # 时间戳
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CrawlerStats(SQLModel, table=True):
    """爬虫统计模型"""
    __tablename__ = "crawler_stats"

    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str = Field(index=True)

    # 统计信息
    requests_count: int = Field(default=0)
    success_count: int = Field(default=0)
    failed_count: int = Field(default=0)
    total_response_time: float = Field(default=0.0)

    # 时间戳
    date: datetime = Field(default_factory=datetime.utcnow)
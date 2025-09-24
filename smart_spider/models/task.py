from __future__ import annotations

import time
from datetime import datetime
from typing import Dict, Optional

from smart_spider.models.base import BaseORM  # 见下方
from smart_spider.utils.helpers import snowflake_id

class Task(BaseORM):
    """轻量级 ORM：目前内存 dict 存储，后续可换 SQLModel/SQLAlchemy"""
    _db: Dict[str, "Task"] = {}

    def __init__(
        self,
        *,
        task_id: Optional[str] = None,
        name: str,
        url: str,
        spider_config: dict,
        status: str = "pending",
        total_url_count: int = 0,
        success_url_count: int = 0,
        failed_url_count: int = 0,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.task_id = task_id or snowflake_id()
        self.name = name
        self.url = url
        self.spider_config = spider_config
        self.status = status
        self.total_url_count = total_url_count
        self.success_url_count = success_url_count
        self.failed_url_count = failed_url_count
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at

    # ---------- CRUD ----------
    def save(self) -> None:
        self.updated_at = datetime.utcnow()
        Task._db[self.task_id] = self

    @classmethod
    def get(cls, task_id: str) -> Optional["Task"]:
        return cls._db.get(task_id)

    @classmethod
    def list(cls, page: int = 1, size: int = 20) -> tuple[int, list["Task"]]:
        items = list(cls._db.values())
        total = len(items)
        start, end = (page - 1) * size, page * size
        return total, items[start:end]

    def cancel(self) -> None:
        if self.status in ("pending", "running"):
            self.status = "cancelled"
            self.save()
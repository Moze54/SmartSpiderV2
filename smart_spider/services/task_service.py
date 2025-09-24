from __future__ import annotations

import logging
from datetime import datetime

from smart_spider.api.schemas import TaskCreateRequest, TaskQueryResponse
from smart_spider.core.exceptions import TaskNotFoundException, TaskConflictException
from smart_spider.models.task import Task

logger = logging.getLogger(__name__)

class TaskService:
    @staticmethod
    def create(payload: TaskCreateRequest) -> Task:
        task = Task(
            name=payload.name,
            url=str(payload.url),
            spider_config=payload.spider_config,
        )
        task.save()
        logger.info("[TaskService] created task=%s", task.task_id)
        return task

    @staticmethod
    def get_task(task_id: str) -> TaskQueryResponse:
        task = Task.get(task_id)
        if not task:
            raise TaskNotFoundException(task_id)
        return TaskQueryResponse(
            task_id=task.task_id,
            name=task.name,
            url=task.url,
            status=task.status,
            total_url_count=task.total_url_count,
            success_url_count=task.success_url_count,
            failed_url_count=task.failed_url_count,
            created_at=task.created_at,
            updated_at=task.updated_at,
            runtime=_humanize_runtime(task.created_at, task.updated_at),
        )

    @staticmethod
    def list_tasks(page: int, size: int):
        total, tasks = Task.list(page, size)
        items = [TaskService.get_task(t.task_id) for t in tasks]
        return total, items

    @staticmethod
    def cancel_task(task_id: str) -> None:
        task = Task.get(task_id)
        if not task:
            raise TaskNotFoundException(task_id)
        if task.status not in ("pending", "running"):
            raise TaskConflictException("Task already finished or cancelled")
        task.cancel()
        logger.warning("[TaskService] cancelled task=%s", task_id)

# ---------- helper ----------
def _humanize_runtime(start: datetime, end: datetime | None) -> str | None:
    if not end:
        return None
    delta = end - start
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return f"{seconds}s"
    minutes, seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m{seconds}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h{minutes}m"
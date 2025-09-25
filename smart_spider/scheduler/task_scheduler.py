"""
任务调度器 - 基础版本
"""
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging

from smart_spider.core.exceptions import TaskConflictException, ValidationException
from smart_spider.core.logger import logger


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledTask:
    """定时任务"""
    task_id: str
    name: str
    task_config: Dict[str, Any]
    schedule_type: str  # cron, interval, one_time
    schedule_config: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class TaskScheduler:
    """任务调度器"""

    def __init__(self):
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self.check_interval = 60  # 检查间隔（秒）

    async def start(self):
        """启动调度器"""
        if self.running:
            return

        self.running = True
        logger.info("任务调度器已启动")

        # 启动调度循环
        asyncio.create_task(self._schedule_loop())

    async def stop(self):
        """停止调度器"""
        self.running = False
        logger.info("任务调度器已停止")

    async def add_cron_task(self, task_config: Dict[str, Any], cron_expression: str, name: str) -> str:
        """添加Cron任务"""
        task_id = f"cron_{name}_{datetime.now().timestamp()}"

        scheduled_task = ScheduledTask(
            task_id=task_id,
            name=name,
            task_config=task_config,
            schedule_type="cron",
            schedule_config={"cron_expression": cron_expression}
        )

        self.scheduled_tasks[task_id] = scheduled_task
        logger.info(f"Cron任务已添加: {task_id}")
        return task_id

    async def add_interval_task(self, task_config: Dict[str, Any], interval_seconds: int, name: str) -> str:
        """添加间隔任务"""
        task_id = f"interval_{name}_{datetime.now().timestamp()}"

        scheduled_task = ScheduledTask(
            task_id=task_id,
            name=name,
            task_config=task_config,
            schedule_type="interval",
            schedule_config={"interval_seconds": interval_seconds}
        )

        self.scheduled_tasks[task_id] = scheduled_task
        logger.info(f"间隔任务已添加: {task_id}")
        return task_id

    async def add_one_time_task(self, task_config: Dict[str, Any], run_date: datetime, name: str) -> str:
        """添加一次性任务"""
        task_id = f"onetime_{name}_{datetime.now().timestamp()}"

        scheduled_task = ScheduledTask(
            task_id=task_id,
            name=name,
            task_config=task_config,
            schedule_type="one_time",
            schedule_config={"run_date": run_date.isoformat()},
            next_run=run_date
        )

        self.scheduled_tasks[task_id] = scheduled_task
        logger.info(f"一次性任务已添加: {task_id}")
        return task_id

    async def remove_task(self, task_id: str) -> bool:
        """移除任务"""
        if task_id in self.scheduled_tasks:
            del self.scheduled_tasks[task_id]
            logger.info(f"任务已移除: {task_id}")
            return True
        return False

    def get_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """获取所有定时任务"""
        tasks = []
        for task in self.scheduled_tasks.values():
            tasks.append({
                "task_id": task.task_id,
                "name": task.name,
                "schedule_type": task.schedule_type,
                "schedule_config": task.schedule_config,
                "status": task.status.value,
                "created_at": task.created_at.isoformat(),
                "last_run": task.last_run.isoformat() if task.last_run else None,
                "next_run": task.next_run.isoformat() if task.next_run else None
            })
        return tasks

    async def _schedule_loop(self):
        """调度循环"""
        while self.running:
            try:
                await self._check_and_run_tasks()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"调度循环错误: {str(e)}")
                await asyncio.sleep(self.check_interval)

    async def _check_and_run_tasks(self):
        """检查并运行任务"""
        current_time = datetime.now()

        for task in list(self.scheduled_tasks.values()):
            try:
                if self._should_run_task(task, current_time):
                    await self._run_task(task)
            except Exception as e:
                logger.error(f"运行任务失败: {task.task_id}, 错误: {str(e)}")

    def _should_run_task(self, task: ScheduledTask, current_time: datetime) -> bool:
        """判断是否应该运行任务"""
        if task.status != TaskStatus.PENDING:
            return False

        if task.schedule_type == "one_time":
            return task.next_run and current_time >= task.next_run
        elif task.schedule_type == "interval":
            if task.last_run is None:
                return True
            interval = timedelta(seconds=task.schedule_config["interval_seconds"])
            return current_time >= task.last_run + interval
        elif task.schedule_type == "cron":
            # Cron逻辑简化版本 - 实际应该解析cron表达式
            if task.last_run is None:
                return True
            # 这里应该实现完整的cron表达式解析
            return False

        return False

    async def _run_task(self, task: ScheduledTask):
        """运行任务"""
        logger.info(f"开始运行任务: {task.task_id}")
        task.status = TaskStatus.RUNNING
        task.last_run = datetime.now()

        try:
            # 这里应该调用实际的任务执行逻辑
            # 简化版本，只记录日志
            logger.info(f"执行任务配置: {task.task_config}")

            # 模拟任务执行
            await asyncio.sleep(1)

            task.status = TaskStatus.COMPLETED
            logger.info(f"任务运行成功: {task.task_id}")

        except Exception as e:
            task.status = TaskStatus.FAILED
            logger.error(f"任务运行失败: {task.task_id}, 错误: {str(e)}")

        # 更新下次运行时间（对于间隔任务）
        if task.schedule_type == "interval":
            interval = timedelta(seconds=task.schedule_config["interval_seconds"])
            task.next_run = datetime.now() + interval
        elif task.schedule_type == "one_time":
            # 一次性任务完成后移除
            await self.remove_task(task.task_id)


# 全局任务调度器实例
task_scheduler = TaskScheduler()


# 快捷函数
def get_scheduled_tasks() -> List[Dict[str, Any]]:
    """获取所有定时任务"""
    return task_scheduler.get_scheduled_tasks()


async def start_task_scheduler():
    """启动任务调度器"""
    await task_scheduler.start()


async def stop_task_scheduler():
    """停止任务调度器"""
    await task_scheduler.stop()


__all__ = [
    'TaskScheduler',
    'ScheduledTask',
    'TaskStatus',
    'task_scheduler',
    'get_scheduled_tasks',
    'start_task_scheduler',
    'stop_task_scheduler'
]
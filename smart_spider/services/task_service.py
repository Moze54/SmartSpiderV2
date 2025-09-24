import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from smart_spider.models.database import Task, TaskResult, TaskStatus
from smart_spider.config.crawler_config import TaskConfig
from smart_spider.engine.crawler import crawler_engine
from smart_spider.core.logger import logger
from smart_spider.core.exceptions import TaskNotFoundException, TaskConflictException, ValidationException


class TaskService:
    """任务服务"""

    def __init__(self):
        pass

    async def create_task(self, session: AsyncSession, task_config: TaskConfig) -> Task:
        """创建任务"""
        task_id = str(uuid.uuid4())

        task = Task(
            task_id=task_id,
            name=task_config.name,
            description=task_config.description,
            urls=task_config.urls,
            config=task_config.dict(),
            status=TaskStatus.PENDING
        )

        session.add(task)
        await session.commit()
        await session.refresh(task)

        logger.info(f"任务创建成功: {task_id}")
        return task

    async def start_task(self, session: AsyncSession, task_id: str) -> bool:
        """启动任务"""
        # 查询任务
        result = await session.execute(
            select(Task).where(Task.task_id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            raise TaskNotFoundException(task_id)

        if task.status != TaskStatus.PENDING:
            raise TaskConflictException(f"任务状态错误，无法启动: {task.status}", task_id)

        try:
            # 解析配置
            task_config = TaskConfig(**task.config)

            # 启动爬虫任务
            await crawler_engine.start_task(task_id, task_config)

            # 更新任务状态
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()
            await session.commit()

            logger.info(f"任务启动成功: {task_id}")
            return True

        except Exception as e:
            logger.error(f"任务启动失败: {task_id} - {str(e)}")
            task.status = TaskStatus.FAILED
            await session.commit()
            raise

    async def stop_task(self, session: AsyncSession, task_id: str) -> bool:
        """停止任务"""
        # 查询任务
        result = await session.execute(
            select(Task).where(Task.task_id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            logger.error(f"任务不存在: {task_id}")
            return False

        if task.status != TaskStatus.RUNNING:
            logger.error(f"任务未运行: {task_id} - {task.status}")
            return False

        try:
            # 停止爬虫任务
            success = await crawler_engine.stop_task(task_id)

            if success:
                # 更新任务状态
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.utcnow()
                await session.commit()
                logger.info(f"任务停止成功: {task_id}")
                return True
            else:
                logger.error(f"任务停止失败: {task_id}")
                return False

        except Exception as e:
            logger.error(f"任务停止失败: {task_id} - {str(e)}")
            return False

    async def get_task(self, session: AsyncSession, task_id: str) -> Optional[Task]:
        """获取任务"""
        result = await session.execute(
            select(Task).where(Task.task_id == task_id)
        )
        return result.scalar_one_or_none()

    async def get_tasks(self, session: AsyncSession, status: Optional[TaskStatus] = None) -> List[Task]:
        """获取任务列表"""
        query = select(Task)
        if status:
            query = query.where(Task.status == status)
        query = query.order_by(Task.created_at.desc())

        result = await session.execute(query)
        return result.scalars().all()

    async def get_task_results(self, session: AsyncSession, task_id: str, limit: int = 100) -> List[TaskResult]:
        """获取任务结果"""
        result = await session.execute(
            select(TaskResult)
            .where(TaskResult.task_id == task_id)
            .order_by(TaskResult.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def delete_task(self, session: AsyncSession, task_id: str) -> bool:
        """删除任务"""
        result = await session.execute(
            select(Task).where(Task.task_id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            return False

        # 如果任务正在运行，先停止
        if task.status == TaskStatus.RUNNING:
            await self.stop_task(session, task_id)

        # 删除任务结果
        await session.execute(
            TaskResult.__table__.delete().where(TaskResult.task_id == task_id)
        )

        # 删除任务
        await session.delete(task)
        await session.commit()

        logger.info(f"任务删除成功: {task_id}")
        return True

    async def update_task_progress(self, session: AsyncSession, task_id: str, progress: float) -> bool:
        """更新任务进度"""
        result = await session.execute(
            update(Task)
            .where(Task.task_id == task_id)
            .values(
                progress=progress,
                updated_at=datetime.utcnow()
            )
        )

        if result.rowcount > 0:
            await session.commit()
            return True
        return False

    async def save_task_result(self, session: AsyncSession, task_id: str, result_data: dict) -> bool:
        """保存任务结果"""
        try:
            result = TaskResult(
                task_id=task_id,
                data=result_data.get('data', {}),
                url=result_data.get('url', ''),
                status_code=result_data.get('status_code', 0),
                response_time=result_data.get('response_time', 0.0)
            )

            session.add(result)
            await session.commit()
            return True

        except Exception as e:
            logger.error(f"保存任务结果失败: {task_id} - {str(e)}")
            await session.rollback()
            return False

    async def get_active_tasks(self) -> List[str]:
        """获取活跃任务列表"""
        return await crawler_engine.get_active_tasks()

    async def get_task_status(self, task_id: str) -> Optional[dict]:
        """获取任务状态"""
        return await crawler_engine.get_task_status(task_id)

    async def get_task_results_from_engine(self, task_id: str) -> List[dict]:
        """从引擎获取任务结果"""
        return await crawler_engine.get_task_results(task_id)


# 全局任务服务实例
task_service = TaskService()
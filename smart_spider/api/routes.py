from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict
from pydantic import Field

from smart_spider.api.schemas import (
    TaskCreateRequest,
    TaskResponse,
    TaskListResponse,
    TaskActionResponse,
    TaskResultResponse,
    TaskQueryRequest
)
from smart_spider.services.task_service import task_service
from smart_spider.core.database import get_session
from smart_spider.models.database import TaskStatus
from smart_spider.config.crawler_config import TaskConfig
from smart_spider.core.exceptions import (
    TaskNotFoundException,
    TaskConflictException,
    ValidationException,
    CrawlerException
)

# 创建API路由
router = APIRouter(prefix="/api/v1", tags=["tasks"])


@router.post("/tasks", response_model=TaskResponse, summary="创建爬虫任务")
async def create_task(
    request: TaskCreateRequest,
    session: AsyncSession = Depends(get_session)
):
    """创建新的爬虫任务"""
    try:
        # 构建任务配置
        task_config = TaskConfig(
            name=request.name,
            description=request.description,
            urls=request.urls,
            max_concurrent_requests=request.max_concurrent_requests,
            request_delay=request.request_delay,
            timeout=request.timeout,
            retry_times=request.retry_times,
            parse_rules=request.parse_rules,
            selector_type=request.selector_type,
            storage_type=request.storage_type,
            output_dir=request.output_dir,
            max_items=request.max_items,
            priority=request.priority
        )

        # 创建任务
        task = await task_service.create_task(session, task_config)
        return task

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"创建任务失败: {str(e)}"
        )


@router.get("/tasks", response_model=TaskListResponse, summary="获取任务列表")
async def get_tasks(
    status: Optional[TaskStatus] = Query(None, description="任务状态筛选"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    session: AsyncSession = Depends(get_session)
):
    """获取任务列表，支持按状态筛选"""
    try:
        tasks = await task_service.get_tasks(session, status)
        total = len(tasks)

        # 分页
        paginated_tasks = tasks[offset:offset + limit]

        return TaskListResponse(
            total=total,
            items=paginated_tasks
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取任务列表失败: {str(e)}"
        )


@router.get("/tasks/{task_id}", response_model=TaskResponse, summary="获取任务详情")
async def get_task(
    task_id: str,
    session: AsyncSession = Depends(get_session)
):
    """获取特定任务的详细信息"""
    task = await task_service.get_task(session, task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"任务不存在: {task_id}"
        )
    return task


@router.post("/tasks/{task_id}/start", response_model=TaskActionResponse, summary="启动任务")
async def start_task(
    task_id: str,
    session: AsyncSession = Depends(get_session)
):
    """启动指定的爬虫任务"""
    try:
        await task_service.start_task(session, task_id)
        return TaskActionResponse(
            success=True,
            message=f"任务 {task_id} 已启动"
        )
    except TaskNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TaskConflictException as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动任务失败: {str(e)}")


@router.post("/tasks/{task_id}/stop", response_model=TaskActionResponse, summary="停止任务")
async def stop_task(
    task_id: str,
    session: AsyncSession = Depends(get_session)
):
    """停止指定的爬虫任务"""
    success = await task_service.stop_task(session, task_id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="停止任务失败"
        )

    return TaskActionResponse(
        success=True,
        message=f"任务 {task_id} 已停止"
    )


@router.delete("/tasks/{task_id}", response_model=TaskActionResponse, summary="删除任务")
async def delete_task(
    task_id: str,
    session: AsyncSession = Depends(get_session)
):
    """删除指定的爬虫任务"""
    success = await task_service.delete_task(session, task_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"任务不存在: {task_id}"
        )

    return TaskActionResponse(
        success=True,
        message=f"任务 {task_id} 已删除"
    )


@router.get("/tasks/{task_id}/results", response_model=List[TaskResultResponse], summary="获取任务结果")
async def get_task_results(
    task_id: str,
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    session: AsyncSession = Depends(get_session)
):
    """获取指定任务的爬取结果"""
    task = await task_service.get_task(session, task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"任务不存在: {task_id}"
        )

    results = await task_service.get_task_results(session, task_id, limit)
    return results


@router.get("/tasks/{task_id}/status", response_model=dict, summary="获取任务状态")
async def get_task_status(
    task_id: str
):
    """获取任务的实时状态"""
    status = await task_service.get_task_status(task_id)
    if not status:
        raise HTTPException(
            status_code=404,
            detail=f"任务不存在: {task_id}"
        )
    return status


@router.get("/health", summary="健康检查")
async def health_check():
    """API健康检查"""
    return {"status": "healthy", "service": "SmartSpider"}


# 额外的实用接口
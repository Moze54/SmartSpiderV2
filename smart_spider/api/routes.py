from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from smart_spider.api.schemas import (
    TaskCreateRequest,
    TaskCreateResponse,
    TaskQueryResponse,
    TaskPageResponse,
    CancelResp,
)
from smart_spider.services.task_service import TaskService
from smart_spider.core.exceptions import TaskNotFoundException, TaskConflictException

router = APIRouter()

# 1. 健康检查（也改为 POST）
@router.post("/status", response_model=dict)
def status():
    return {"status": "running", "version": "0.1.0"}

# 2. 创建任务
@router.post("/tasks", response_model=TaskCreateResponse)
def create_task(req: TaskCreateRequest):
    task = TaskService.create(req)
    return TaskCreateResponse(
        task_id=task.task_id,
        status=task.status,
        created_at=task.created_at,
    )

# 3. 查询单个任务
class TaskIDReq(BaseModel):
    task_id: str

@router.post("/tasks/info", response_model=TaskQueryResponse)
def get_task(payload: TaskIDReq):
    try:
        return TaskService.get_task(payload.task_id)
    except TaskNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))

# 4. 分页列表
class ListReq(BaseModel):
    page: int = 1
    size: int = 20

@router.post("/tasks/list", response_model=TaskPageResponse)
def list_tasks(payload: ListReq):
    total, items = TaskService.list_tasks(payload.page, payload.size)
    return TaskPageResponse(total=total, page=payload.page, size=payload.size, items=items)

class CancelReq(BaseModel):
    task_id: str
# 5. 取消任务
@router.post("/tasks/cancel", response_model=CancelResp)
def cancel_task(payload: CancelReq):
    try:
        TaskService.cancel_task(payload.task_id)
        return CancelResp(
            task_id=payload.task_id,
            status="cancelled",
            message="任务已取消"
        )
    except TaskNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TaskConflictException as e:
        raise HTTPException(status_code=409, detail=str(e))
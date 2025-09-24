from pydantic import BaseModel

class TaskCreateRequest(BaseModel):
    name: str
    url: str
    config: dict = {}

class TaskResponse(BaseModel):
    task_id: str
    status: str
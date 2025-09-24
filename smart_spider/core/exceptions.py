class SmartSpiderException(Exception):
    """基础异常类"""
    pass

class TaskNotFoundException(SmartSpiderException):
    """任务未找到"""
    pass
class SmartSpiderException(Exception):
    """根异常，日志统一捕获"""

class TaskNotFoundException(SmartSpiderException):
    def __init__(self, task_id: str):
        super().__init__(f"Task {task_id} not found")

class TaskConflictException(SmartSpiderException):
    """状态冲突，如已完成却再次取消"""
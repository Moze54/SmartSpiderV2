class SmartSpiderException(Exception):
    """基础异常类"""
    pass

class TaskNotFoundException(SmartSpiderException):
    """任务未找到"""
    pass
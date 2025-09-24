import uuid

def generate_task_id() -> str:
    return uuid.uuid4().hex
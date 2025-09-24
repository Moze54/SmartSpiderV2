import time
import uuid

def generate_task_id() -> str:
    return uuid.uuid4().hex

def snowflake_id() -> str:
    """简单雪花 ID（41+10+12=63bit），单机够用"""
    timestamp = int(time.time() * 1000) - 1_600_000_000_000
    worker = 1 & 0x3FF          # 10 bit 工作机 ID
    sequence = uuid.uuid4().int & 0xFFF
    return str((timestamp << 22) | (worker << 12) | sequence)
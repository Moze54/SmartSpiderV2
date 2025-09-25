import asyncio
import heapq
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

from smart_spider.core.logger import logger


class Priority(Enum):
    """任务优先级枚举"""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    MINIMAL = 4


@dataclass
class PriorityItem:
    """优先级队列项"""
    priority: int
    timestamp: float
    item_id: str
    data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __lt__(self, other):
        # 优先级数值越小，优先级越高
        if self.priority != other.priority:
            return self.priority \u003c other.priority
        # 优先级相同时，按时间戳排序（FIFO）
        return self.timestamp \u003c other.timestamp


class PriorityQueue:
    """优先级队列"""

    def __init__(self, maxsize: int = 0):
        self._queue: List[PriorityItem] = []
        self._maxsize = maxsize
        self._item_map: Dict[str, PriorityItem] = {}
        self._lock = asyncio.Lock()
        self._stats = {
            'total_processed': 0,
            'total_failed': 0,
            'total_successful': 0,
            'priority_distribution': {priority.name: 0 for priority in Priority},
            'average_wait_time': 0.0,
            'max_wait_time': 0.0,
            'min_wait_time': float('inf')
        }

    async def put(
        self,
        item: Any,
        priority: Priority = Priority.NORMAL,
        item_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """添加项目到队列"""
        async with self._lock:
            item_id = item_id or str(uuid.uuid4())
            timestamp = datetime.now().timestamp()

            priority_item = PriorityItem(
                priority=priority.value,
                timestamp=timestamp,
                item_id=item_id,
                data=item,
                metadata=metadata or {}
            )

            # 检查队列大小限制
            if self._maxsize \u003e 0 and len(self._queue) \u003e= self._maxsize:
                # 移除优先级最低的项目
                if self._queue:
                    removed_item = heapq.heappop(self._queue)
                    del self._item_map[removed_item.item_id]
                    logger.warning(f"队列已满，移除低优先级项目: {removed_item.item_id}")

            heapq.heappush(self._queue, priority_item)
            self._item_map[item_id] = priority_item

            logger.debug(f"添加项目到优先级队列: {item_id} (优先级: {priority.name})")
            return item_id

    async def get(self, timeout: Optional[float] = None) -> Optional[Tuple[str, Any, Dict[str, Any]]]:
        """从队列获取项目"""
        try:
            # 等待队列中有项目
            start_time = datetime.now().timestamp()

            while not self._queue:
                if timeout and (datetime.now().timestamp() - start_time) \u003e timeout:
                    return None
                await asyncio.sleep(0.1)

            async with self._lock:
                if not self._queue:
                    return None

                item = heapq.heappop(self._queue)
                del self._item_map[item.item_id]

                # 更新统计信息
                self._update_stats(item)

                logger.debug(f"从优先级队列获取项目: {item.item_id} (优先级: {Priority(item.priority).name})")
                return item.item_id, item.data, item.metadata

        except Exception as e:
            logger.error(f"从优先级队列获取项目失败: {str(e)}")
            return None

    async def peek(self) -> Optional[Tuple[str, Any, int]]:
        """查看队列顶部项目（不删除）"""
        async with self._lock:
            if not self._queue:
                return None

            item = self._queue[0]
            return item.item_id, item.data, item.priority

    async def remove(self, item_id: str) -> bool:
        """从队列移除特定项目"""
        async with self._lock:
            if item_id not in self._item_map:
                return False

            # 找到并移除项目
            item = self._item_map[item_id]
            self._queue.remove(item)
            del self._item_map[item_id]

            # 重新堆化
            heapq.heapify(self._queue)

            logger.debug(f"从优先级队列移除项目: {item_id}")
            return True

    async def update_priority(
        self,
        item_id: str,
        new_priority: Priority
    ) -> bool:
        """更新项目优先级"""
        async with self._lock:
            if item_id not in self._item_map:
                return False

            item = self._item_map[item_id]
            old_priority = item.priority
            item.priority = new_priority.value

            # 重新堆化
            heapq.heapify(self._queue)

            logger.debug(f"更新项目优先级: {item_id} (从 {Priority(old_priority).name} 到 {new_priority.name})")
            return True

    def qsize(self) -> int:
        """获取队列大小"""
        return len(self._queue)

    def empty(self) -> bool:
        """检查队列是否为空"""
        return len(self._queue) == 0

    def full(self) -> bool:
        """检查队列是否已满"""
        return self._maxsize \u003e 0 and len(self._queue) \u003e= self._maxsize

    def get_stats(self) -> Dict[str, Any]:
        """获取队列统计信息"""
        current_time = datetime.now().timestamp()

        # 计算当前队列中项目的等待时间
        wait_times = []
        for item in self._queue:
            wait_time = current_time - item.timestamp
            wait_times.append(wait_time)

        stats = {
            'queue_size': len(self._queue),
            'max_size': self._maxsize,
            'is_empty': self.empty(),
            'is_full': self.full(),
            'total_processed': self._stats['total_processed'],
            'total_successful': self._stats['total_successful'],
            'total_failed': self._stats['total_failed'],
            'priority_distribution': self._stats['priority_distribution'].copy(),
            'average_wait_time': sum(wait_times) / len(wait_times) if wait_times else 0,
            'max_wait_time': max(wait_times) if wait_times else 0,
            'min_wait_time': min(wait_times) if wait_times else 0,
            'oldest_item_wait_time': max(wait_times) if wait_times else 0,
        }

        return stats

    def _update_stats(self, item: PriorityItem):
        """更新统计信息"""
        self._stats['total_processed'] += 1
        self._stats['priority_distribution'][Priority(item.priority).name] += 1

        # 计算等待时间
        wait_time = datetime.now().timestamp() - item.timestamp

        # 更新平均等待时间
        total_processed = self._stats['total_processed']
        self._stats['average_wait_time'] = (
            (self._stats['average_wait_time'] * (total_processed - 1) + wait_time) / total_processed
        )

        # 更新最大/最小等待时间
        self._stats['max_wait_time'] = max(self._stats['max_wait_time'], wait_time)
        self._stats['min_wait_time'] = min(self._stats['min_wait_time'], wait_time)

    def clear(self):
        """清空队列"""
        self._queue.clear()
        self._item_map.clear()
        logger.info("优先级队列已清空")


class TaskPriorityQueue:
    """任务优先级队列管理器"""

    def __init__(self):
        self.queues: Dict[str, PriorityQueue] = {}
        self._default_queue_name = "default"

    def create_queue(self, name: str, maxsize: int = 0) -> PriorityQueue:
        """创建新的优先级队列"""
        if name in self.queues:
            logger.warning(f"队列已存在: {name}")
            return self.queues[name]

        queue = PriorityQueue(maxsize=maxsize)
        self.queues[name] = queue
        logger.info(f"创建优先级队列: {name} (最大大小: {maxsize})")
        return queue

    def get_queue(self, name: Optional[str] = None) -> PriorityQueue:
        """获取队列"""
        name = name or self._default_queue_name

        if name not in self.queues:
            return self.create_queue(name)

        return self.queues[name]

    async def submit_task(
        self,
        task_data: Any,
        priority: Priority = Priority.NORMAL,
        queue_name: Optional[str] = None,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """提交任务到队列"""
        queue = self.get_queue(queue_name)
        return await queue.put(task_data, priority, task_id, metadata)

    async def get_next_task(
        self,
        queue_name: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> Optional[Tuple[str, Any, Dict[str, Any]]]:
        """获取下一个任务"""
        queue = self.get_queue(queue_name)
        return await queue.get(timeout)

    async def cancel_task(
        self,
        task_id: str,
        queue_name: Optional[str] = None
    ) -> bool:
        """取消任务"""
        queue = self.get_queue(queue_name)
        return await queue.remove(task_id)

    async def update_task_priority(
        self,
        task_id: str,
        new_priority: Priority,
        queue_name: Optional[str] = None
    ) -> bool:
        """更新任务优先级"""
        queue = self.get_queue(queue_name)
        return await queue.update_priority(task_id, new_priority)

    def get_queue_stats(self, queue_name: Optional[str] = None) -> Dict[str, Any]:
        """获取队列统计信息"""
        if queue_name:
            queue = self.get_queue(queue_name)
            return queue.get_stats()

        # 获取所有队列的统计信息
        all_stats = {}
        total_size = 0
        total_processed = 0

        for name, queue in self.queues.items():
            stats = queue.get_stats()
            all_stats[name] = stats
            total_size += stats['queue_size']
            total_processed += stats['total_processed']

        return {
            'queues': all_stats,
            'total_queues': len(self.queues),
            'total_size': total_size,
            'total_processed': total_processed
        }

    def get_all_queues(self) -> List[str]:
        """获取所有队列名称"""
        return list(self.queues.keys())

    async def clear_queue(self, queue_name: Optional[str] = None):
        """清空队列"""
        if queue_name:
            queue = self.get_queue(queue_name)
            queue.clear()
        else:
            # 清空所有队列
            for queue in self.queues.values():
                queue.clear()

    def remove_queue(self, queue_name: str) -> bool:
        """删除队列"""
        if queue_name not in self.queues:
            return False

        if queue_name == self._default_queue_name:
            logger.warning(f"不能删除默认队列: {queue_name}")
            return False

        del self.queues[queue_name]
        logger.info(f"删除队列: {queue_name}")
        return True\n\n# 全局任务优先级队列管理器\ntask_priority_queue = TaskPriorityQueue()\n\n\n# 快捷函数\nasync def submit_task_with_priority(\n    task_data: Any,\n    priority: str = "NORMAL",\n    queue_name: Optional[str] = None,\n    **kwargs\n) -\u003e str:\n    \"\"\"提交带优先级的任务\"\"\"\n    priority_enum = Priority[priority.upper()]
    return await task_priority_queue.submit_task(task_data, priority_enum, queue_name, **kwargs)\n\n\nasync def get_high_priority_task(\n    queue_name: Optional[str] = None,\n    timeout: Optional[float] = None\n) -\u003e Optional[Tuple[str, Any, Dict[str, Any]]]:\n    \"\"\"获取高优先级任务\"\"\"\n    return await task_priority_queue.get_next_task(queue_name, timeout)\n\n\ndef get_task_queue_stats(queue_name: Optional[str] = None) -\u003e Dict[str, Any]:\n    \"\"\"获取任务队列统计\"\"\"\n    return task_priority_queue.get_queue_stats(queue_name)\n\n\n# 预定义的任务优先级\nCRITICAL = Priority.CRITICAL\nHIGH = Priority.HIGH\nNORMAL = Priority.NORMAL\nLOW = Priority.LOW\nMINIMAL = Priority.MINIMAL\n\n__all__ = [\n    'Priority',\n    'PriorityQueue',\n    'TaskPriorityQueue',\n    'task_priority_queue',\n    'submit_task_with_priority',\n    'get_high_priority_task',\n    'get_task_queue_stats',\n    'CRITICAL', 'HIGH', 'NORMAL', 'LOW', 'MINIMAL'\n]
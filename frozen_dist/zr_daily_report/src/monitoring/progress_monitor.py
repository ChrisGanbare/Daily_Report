"""
实时进度监控系统
提供任务进度监控和实时通知功能
"""

import asyncio
import json
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class TaskStatus(Enum):
    """任务状态枚举"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskProgress:
    """任务进度数据类"""

    task_id: str
    status: TaskStatus
    progress: int = 0  # 0-100
    message: str = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_items: int = 0
    processed_items: int = 0
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class ProgressMonitor:
    """进度监控器"""

    def __init__(self):
        self.tasks: Dict[str, TaskProgress] = {}
        self.observers: List[Callable] = []
        self._lock = threading.Lock()

    def create_task(self, task_id: str, total_items: int = 0) -> TaskProgress:
        """创建新任务"""
        with self._lock:
            task = TaskProgress(
                task_id=task_id,
                status=TaskStatus.PENDING,
                total_items=total_items,
                start_time=datetime.now(),
            )
            self.tasks[task_id] = task
            self._notify_observers(task)
            return task

    def update_progress(
        self,
        task_id: str,
        progress: int,
        message: str = "",
        processed_items: int = None,
    ):
        """更新任务进度"""
        with self._lock:
            if task_id not in self.tasks:
                return

            task = self.tasks[task_id]
            task.progress = max(0, min(100, progress))
            task.message = message

            if processed_items is not None:
                task.processed_items = processed_items

            if task.status == TaskStatus.PENDING:
                task.status = TaskStatus.RUNNING

            self._notify_observers(task)

    def complete_task(self, task_id: str, result: Optional[Dict[str, Any]] = None):
        """完成任务"""
        with self._lock:
            if task_id not in self.tasks:
                return

            task = self.tasks[task_id]
            task.status = TaskStatus.COMPLETED
            task.progress = 100
            task.end_time = datetime.now()
            task.result = result
            task.message = "任务完成"

            self._notify_observers(task)

    def fail_task(self, task_id: str, error_message: str):
        """任务失败"""
        with self._lock:
            if task_id not in self.tasks:
                return

            task = self.tasks[task_id]
            task.status = TaskStatus.FAILED
            task.end_time = datetime.now()
            task.error_message = error_message
            task.message = f"任务失败: {error_message}"

            self._notify_observers(task)

    def cancel_task(self, task_id: str):
        """取消任务"""
        with self._lock:
            if task_id not in self.tasks:
                return

            task = self.tasks[task_id]
            task.status = TaskStatus.CANCELLED
            task.end_time = datetime.now()
            task.message = "任务已取消"

            self._notify_observers(task)

    def get_task(self, task_id: str) -> Optional[TaskProgress]:
        """获取任务信息"""
        with self._lock:
            return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[TaskProgress]:
        """获取所有任务"""
        with self._lock:
            return list(self.tasks.values())

    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """清理旧任务"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        with self._lock:
            tasks_to_remove = []
            for task_id, task in self.tasks.items():
                if task.end_time and task.end_time < cutoff_time:
                    tasks_to_remove.append(task_id)

            for task_id in tasks_to_remove:
                del self.tasks[task_id]

    def add_observer(self, observer: Callable[[TaskProgress], None]):
        """添加观察者"""
        with self._lock:
            self.observers.append(observer)

    def remove_observer(self, observer: Callable[[TaskProgress], None]):
        """移除观察者"""
        with self._lock:
            if observer in self.observers:
                self.observers.remove(observer)

    def _notify_observers(self, task: TaskProgress):
        """通知所有观察者"""
        for observer in self.observers:
            try:
                observer(task)
            except Exception as e:
                print(f"通知观察者时出错: {e}")


class WebSocketProgressMonitor:
    """WebSocket进度监控器"""

    def __init__(self, progress_monitor: ProgressMonitor):
        self.progress_monitor = progress_monitor
        self.connections: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    async def connect(self, websocket, client_id: str):
        """建立WebSocket连接"""
        with self._lock:
            connection = {
                "websocket": websocket,
                "client_id": client_id,
                "connected_at": datetime.now(),
            }
            self.connections.append(connection)

        # 发送当前所有任务状态
        tasks = self.progress_monitor.get_all_tasks()
        await websocket.send(
            json.dumps(
                {"type": "initial_tasks", "tasks": [asdict(task) for task in tasks]}
            )
        )

    async def disconnect(self, websocket):
        """断开WebSocket连接"""
        with self._lock:
            self.connections = [
                conn for conn in self.connections if conn["websocket"] != websocket
            ]

    async def broadcast_progress(self, task: TaskProgress):
        """广播进度更新"""
        message = {"type": "progress_update", "task": asdict(task)}

        disconnected = []
        with self._lock:
            for connection in self.connections:
                try:
                    await connection["websocket"].send(json.dumps(message))
                except Exception as e:
                    print(f"发送WebSocket消息失败: {e}")
                    disconnected.append(connection)

            # 移除断开的连接
            for conn in disconnected:
                self.connections.remove(conn)


class ProgressTracker:
    """进度跟踪器装饰器"""

    def __init__(self, monitor: ProgressMonitor, task_id: str, total_items: int = 0):
        self.monitor = monitor
        self.task_id = task_id
        self.total_items = total_items
        self.processed_items = 0

    def __enter__(self):
        """进入上下文"""
        self.monitor.create_task(self.task_id, self.total_items)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        if exc_type:
            self.monitor.fail_task(self.task_id, str(exc_val))
        else:
            self.monitor.complete_task(self.task_id)

    def update(self, progress: int, message: str = ""):
        """更新进度"""
        self.monitor.update_progress(
            self.task_id, progress, message, self.processed_items
        )

    def increment(self, count: int = 1, message: str = ""):
        """增加处理数量"""
        self.processed_items += count
        if self.total_items > 0:
            progress = int((self.processed_items / self.total_items) * 100)
            self.update(progress, message)


# 使用示例
def progress_tracker_example():
    """进度跟踪器使用示例"""
    monitor = ProgressMonitor()

    # 创建任务
    with ProgressTracker(monitor, "task_001", 100) as tracker:
        for i in range(100):
            # 模拟处理
            time.sleep(0.1)

            # 更新进度
            tracker.increment(1, f"处理第 {i + 1} 项")

    # 获取任务状态
    task = monitor.get_task("task_001")
    print(f"任务状态: {task.status.value}")
    print(f"进度: {task.progress}%")


# 异步进度监控示例
async def async_progress_example():
    """异步进度监控示例"""
    monitor = ProgressMonitor()

    async def process_items(items: List[str], task_id: str):
        """异步处理项目"""
        tracker = ProgressTracker(monitor, task_id, len(items))

        for i, item in enumerate(items):
            # 模拟异步处理
            await asyncio.sleep(0.1)

            # 更新进度
            tracker.increment(1, f"处理 {item}")

        tracker.update(100, "处理完成")

    # 启动多个任务
    items1 = [f"item_{i}" for i in range(10)]
    items2 = [f"data_{i}" for i in range(15)]

    await asyncio.gather(
        process_items(items1, "task_001"), process_items(items2, "task_002")
    )

    # 获取所有任务状态
    tasks = monitor.get_all_tasks()
    for task in tasks:
        print(f"任务 {task.task_id}: {task.status.value} - {task.progress}%")


if __name__ == "__main__":
    # 同步示例
    progress_tracker_example()

    # 异步示例
    asyncio.run(async_progress_example())

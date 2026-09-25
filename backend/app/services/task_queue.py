"""Task Queue Service for CrowdSafe.

Provides an asynchronous priority-based task queue and worker management
system for background video frame ingestion, deep learning inference,
and alert dispatching.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Callable, Coroutine, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class TaskPriority(IntEnum):
    """Priority levels for task scheduling (lower numerical value = higher priority)."""

    CRITICAL = 0  # Emergency alerts, high-risk surge evaluations
    HIGH = 1      # Live stream frame evaluations
    NORMAL = 2    # Regular reporting, periodic health checks
    LOW = 3       # Log archiving, historical analysis cleanup


class TaskStatus(str, Enum):
    """Lifecycle states of a background task."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(order=True)
class PrioritizedItem:
    """Helper wrapper for asyncio.PriorityQueue ordering."""

    priority: int
    created_at: float
    task_id: str = field(compare=False)


@dataclass
class Task:
    """Representation of an asynchronous background job."""

    task_id: str
    name: str
    fn: Callable[..., Any]
    args: Tuple[Any, ...] = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


class TaskQueue:
    """Async priority task queue and worker pool manager."""

    def __init__(self, maxsize: int = 1000) -> None:
        """Initialize task queue and state registry."""
        self._queue: asyncio.PriorityQueue[PrioritizedItem] = asyncio.PriorityQueue(maxsize=maxsize)
        self._tasks: Dict[str, Task] = {}
        self._workers: List[asyncio.Task[None]] = []
        self._is_running = False

    def enqueue(
        self,
        name: str,
        fn: Callable[..., Any],
        *args: Any,
        priority: TaskPriority = TaskPriority.NORMAL,
        **kwargs: Any,
    ) -> str:
        """Add a function to the queue for background execution.

        Args:
            name: Human-readable task name.
            fn: Callable or coroutine function to execute.
            priority: Scheduling priority (CRITICAL, HIGH, NORMAL, LOW).

        Returns:
            Unique task_id.
        """
        task_id = str(uuid.uuid4())
        task = Task(
            task_id=task_id,
            name=name,
            fn=fn,
            args=args,
            kwargs=kwargs,
            priority=priority,
            status=TaskStatus.PENDING,
        )
        self._tasks[task_id] = task

        # Push to priority queue
        item = PrioritizedItem(
            priority=int(priority),
            created_at=task.created_at,
            task_id=task_id,
        )
        self._queue.put_nowait(item)
        logger.debug("Enqueued task %s (%s) with priority %s", task_id, name, priority.name)
        return task_id

    def get_task(self, task_id: str) -> Optional[Task]:
        """Look up task details and status by task_id."""
        return self._tasks.get(task_id)

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        limit: int = 50,
    ) -> List[Task]:
        """List tasks optionally filtered by status."""
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)[:limit]

    async def _worker_loop(self, worker_id: int) -> None:
        """Internal worker coroutine to continuously process queued tasks."""
        logger.info("TaskQueue worker-%d started.", worker_id)
        while self._is_running:
            try:
                item = await self._queue.get()
                task = self._tasks.get(item.task_id)

                if not task or task.status == TaskStatus.CANCELLED:
                    self._queue.task_done()
                    continue

                task.status = TaskStatus.RUNNING
                task.started_at = time.time()

                try:
                    if asyncio.iscoroutinefunction(task.fn):
                        task.result = await task.fn(*task.args, **task.kwargs)
                    else:
                        task.result = task.fn(*task.args, **task.kwargs)
                    task.status = TaskStatus.COMPLETED
                except Exception as e:
                    logger.exception("Task %s failed: %s", task.task_id, e)
                    task.error = str(e)
                    task.status = TaskStatus.FAILED
                finally:
                    task.completed_at = time.time()
                    self._queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Worker-%d encountered error: %s", worker_id, e)

        logger.info("TaskQueue worker-%d stopped.", worker_id)

    def start_workers(self, num_workers: int = 2) -> None:
        """Start background worker tasks."""
        if self._is_running:
            return

        self._is_running = True
        loop = asyncio.get_event_loop()
        for i in range(num_workers):
            w = loop.create_task(self._worker_loop(i + 1))
            self._workers.append(w)

    async def stop_workers(self) -> None:
        """Gracefully stop all background workers."""
        self._is_running = False
        for w in self._workers:
            w.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

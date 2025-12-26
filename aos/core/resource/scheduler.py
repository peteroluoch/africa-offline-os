"""
Resource-Aware Task Scheduling
Priority-based task queue with power-aware execution.
"""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Any, Optional
from queue import PriorityQueue

class TaskPriority(int, Enum):
    """Task priority levels (lower number = higher priority)."""
    CRITICAL = 0    # Never defer (USSD, SMS, emergency)
    HIGH = 1        # Defer only in CRITICAL mode
    NORMAL = 2      # Defer in POWER_SAVER
    LOW = 3         # Defer in BALANCED
    BACKGROUND = 4  # Defer unless FULL_POWER

class TaskState(str, Enum):
    """Task execution states."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DEFERRED = "DEFERRED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

@dataclass
class Task:
    """
    Represents a schedulable task with power awareness.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    priority: TaskPriority = TaskPriority.NORMAL
    func: Optional[Callable] = None
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    
    # Power awareness
    estimated_power_cost: float = 1.0  # Arbitrary units
    max_delay_seconds: Optional[int] = None  # Max time task can be deferred
    
    # State tracking
    state: TaskState = TaskState.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    
    def __lt__(self, other: Task) -> bool:
        """Compare tasks by priority for queue ordering."""
        return self.priority < other.priority
    
    def execute(self) -> Any:
        """Execute the task function."""
        if not self.func:
            raise ValueError(f"Task {self.id} has no function to execute")
        
        self.state = TaskState.RUNNING
        self.started_at = datetime.now(timezone.utc)
        
        try:
            self.result = self.func(*self.args, **self.kwargs)
            self.state = TaskState.COMPLETED
            return self.result
        except Exception as e:
            self.state = TaskState.FAILED
            self.error = str(e)
            raise
        finally:
            self.completed_at = datetime.now(timezone.utc)
    
    def is_expired(self) -> bool:
        """Check if task has exceeded its max delay."""
        if not self.max_delay_seconds:
            return False
        
        elapsed = (datetime.now(timezone.utc) - self.created_at).total_seconds()
        return elapsed > self.max_delay_seconds

class ResourceAwareScheduler:
    """
    Priority-based task scheduler with power awareness.
    Defers low-priority tasks when battery is low.
    """
    
    def __init__(self):
        self._task_queue: PriorityQueue[Task] = PriorityQueue()
        self._deferred_tasks: list[Task] = []
        self._running_tasks: dict[str, Task] = {}
        self._completed_tasks: list[Task] = []
        self._max_completed_history = 100
    
    def schedule(self, task: Task) -> str:
        """
        Schedule a task for execution.
        Returns task ID.
        """
        self._task_queue.put(task)
        return task.id
    
    def schedule_function(
        self,
        func: Callable,
        priority: TaskPriority = TaskPriority.NORMAL,
        name: str = "",
        *args,
        **kwargs
    ) -> str:
        """
        Convenience method to schedule a function.
        Returns task ID.
        """
        task = Task(
            name=name or func.__name__,
            priority=priority,
            func=func,
            args=args,
            kwargs=kwargs
        )
        return self.schedule(task)
    
    def should_execute(self, task: Task, current_profile: str) -> bool:
        """
        Determine if a task should execute given the current power profile.
        """
        from aos.core.resource.profiles import PowerProfile
        
        # CRITICAL tasks always execute
        if task.priority == TaskPriority.CRITICAL:
            return True
        
        # Check against power profile
        if current_profile == PowerProfile.CRITICAL:
            return task.priority == TaskPriority.CRITICAL
        elif current_profile == PowerProfile.POWER_SAVER:
            return task.priority <= TaskPriority.HIGH
        elif current_profile == PowerProfile.BALANCED:
            return task.priority <= TaskPriority.NORMAL
        else:  # FULL_POWER
            return True
    
    def get_next_task(self, current_profile: str) -> Optional[Task]:
        """
        Get the next task to execute based on priority and power profile.
        Returns None if no tasks should execute now.
        """
        # Check deferred tasks first (they've been waiting)
        for task in self._deferred_tasks[:]:
            if self.should_execute(task, current_profile) or task.is_expired():
                self._deferred_tasks.remove(task)
                return task
        
        # Check queue
        if not self._task_queue.empty():
            task = self._task_queue.get()
            
            if self.should_execute(task, current_profile):
                return task
            else:
                # Defer this task
                task.state = TaskState.DEFERRED
                self._deferred_tasks.append(task)
                return None
        
        return None
    
    def execute_next(self, current_profile: str) -> Optional[Task]:
        """
        Execute the next eligible task.
        Returns the executed task or None.
        """
        task = self.get_next_task(current_profile)
        if not task:
            return None
        
        self._running_tasks[task.id] = task
        
        try:
            task.execute()
        finally:
            self._running_tasks.pop(task.id, None)
            self._completed_tasks.append(task)
            
            # Limit history
            if len(self._completed_tasks) > self._max_completed_history:
                self._completed_tasks = self._completed_tasks[-self._max_completed_history:]
        
        return task
    
    def get_stats(self) -> dict:
        """Get scheduler statistics."""
        return {
            "pending": self._task_queue.qsize(),
            "deferred": len(self._deferred_tasks),
            "running": len(self._running_tasks),
            "completed": len(self._completed_tasks)
        }
    
    def get_deferred_tasks(self) -> list[Task]:
        """Get list of currently deferred tasks."""
        return self._deferred_tasks.copy()

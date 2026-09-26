"""Domain models for tasks and GitHub Projects v2 items."""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict

DEFAULT_TIMEOUT_SECONDS = 30
timeout=DEFAULT_TIMEOUT_SECONDS

class TaskStatus(str, Enum):
    TODO = "Todo"
    IN_PROGRESS = "In Progress"
    IN_REVIEW = "In Review"
    DONE = "Done"
    BLOCKED = "Blocked"

@dataclass
class TaskItem:
    task_id: str
    title: str
    status: TaskStatus = TaskStatus.TODO
    assignee: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    project_item_id: Optional[str] = None

@dataclass
class ProjectBoardView:
    project_title: str
    columns: Dict[TaskStatus, List[TaskItem]] = field(default_factory=lambda: {s: [] for s in TaskStatus})

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

@dataclass
class TaskOptions:
    prompt: str
    model: str
    size: Optional[str] = None
    steps: Optional[int] = None

@dataclass
class TaskInfoV1:
    _v: int
    task_options: Optional[TaskOptions] = None
    id: str
    max_price: float
    time_to_money_ratio: float

@dataclass
class TaskResultV1:
  _v: int
  image: str

TaskInfo = TaskInfoV1
TaskResult = TaskResultV1

class TaskType(Enum):
    RESULT = 1
    ERROR = 2
    STATUS = 3

class TaskReadinessStatus(Enum):
    READY = 1
    IN_PROGRESS = 2

@dataclass
class TaskResultClient:
    resultsUrl: List[str]
    taskId: str
    error: Optional[str] = None
    type: TaskType
    status: Optional[TaskReadinessStatus] = None

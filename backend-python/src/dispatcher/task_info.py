from enum import Enum, auto
from dataclasses import dataclass, asdict
from typing import Optional
import json


class TaskStatus(Enum):
    INIT = auto()
    PUSHED_INTO_QUEUE = auto()
    PULLED_BY_DISPATCHER = auto()
    REJECTED = auto()
    ASSIGNED_TO_PROVIDER = auto()
    SENT_FAILED = auto()
    SENT_TO_PROVIDER = auto()
    FAILED_BY_PROVIDER = auto()
    ABORTED = auto()
    COMPLETED = auto()
    TIMED_OUT = auto()


class PublicTaskStatus(Enum):
    SUCCESS = auto()
    PENDING = auto()

def get_public_status(status: int) -> PublicTaskStatus:
    if TaskStatus(status) == COMPLETED:
        return PublicTaskStatus.SUCCESS
    return PublicTaskStatus.PENDING

@dataclass
class ComfyPipelineOptions:
    pipeline_data: str
    pipeline_dependencies: str

    @property
    def __dict__(self):
        return asdict(self)

    @property
    def json(self):
        return json.dumps(self.__dict__)


@dataclass
class StandardPipelineOptions:
    prompt: str
    model: str
    size: Optional[str] = None
    steps: Optional[int] = None

    @property
    def __dict__(self):
        return asdict(self)

    @property
    def json(self):
        return json.dumps(self.__dict__)


@dataclass
class TaskOptions:
    comfy_pipeline: Optional[ComfyPipelineOptions] = None
    standard_pipeline: Optional[StandardPipelineOptions] = None

    @property
    def __dict__(self):
        print('22222')
        return {
            'comfy_pipeline':  self.comfy_pipeline.__dict__ if  self.comfy_pipeline else None,
            'standard_pipeline':  self.standard_pipeline.__dict__ if  self.standard_pipeline else None
        }

    @property
    def json(self):
        return json.dumps(self.__dict__)



@dataclass
class TaskInfo:
    id: str
    max_cost: int
    time_to_money_ratio: int
    task_options: Optional[TaskOptions] = None

    @property
    def __dict__(self):
        print('11111')
        # print(self.task_options.__dict__)
        return {
            'id': self.id,
            'max_cost': self.max_cost,
            'time_to_money_ratio':  self.time_to_money_ratio,
            'task_options':  self.task_options.__dict__ if self.task_options else None
        }

    @property
    def json(self):
        return json.dumps(self.__dict__)


@dataclass
class TaskResult:
    images: list[str]


class TaskResultType(Enum):
    RESULT = auto()
    ERROR = auto()
    STATUS = auto()


class TaskResultStatus(Enum):
    READY = auto()
    IN_PROGRESS = auto()


@dataclass
class TaskResultClient:
    result_url: list[str]
    task_id: str
    result_type: TaskResultType
    status: Optional[TaskResultStatus] = None
    error: Optional[str] = None


"""
export type TaskStatusPayload = {
      [TaskStatus.SetToProvider]: [{ providerId: string, minScore: number, waitingTime: number}];
      [TaskStatus.SentFailed]: [{ attempt: number }];
      [TaskStatus.FailedByProvider]: [{ reason?: string }];
} & {
      [taskStatus: number | string | symbol]: [];
};
"""


@dataclass(kw_only=True)
class TaskStatusPayload:
    task_status: TaskStatus


@dataclass(kw_only=True)
class AssignedToProviderPayload(TaskStatusPayload):
    provider_id: str
    min_score: int | float
    waiting_time: int | float
    task_status: TaskStatus = TaskStatus.ASSIGNED_TO_PROVIDER


@dataclass(kw_only=True)
class SentFailedPayload(TaskStatusPayload):
    attempt_num: int
    task_status = TaskStatus.SENT_FAILED


@dataclass(kw_only=True)
class FailedByProvider(TaskStatusPayload):
    reason: str
    task_status = TaskStatus.FAILED_BY_PROVIDER


def task_status_payload_to_string(payload: TaskStatusPayload) -> str:
    if isinstance(payload, FailedByProvider):
        return "FAILED BY PROVIDER: reason={reason}".format(reason=payload.reason)
    elif isinstance(payload, SentFailedPayload):
        return "SENT FAILED: attempt_num={num}".format(num=payload.attempt_num)
    elif isinstance(payload, AssignedToProviderPayload):
        return "ASSIGNED TO PROVIDER: provider_id={id}, min_score={score}, waiting_time={waiting_time}".format(
            provider_id=payload.provider_id,
            score=payload.min_score,
            waiting_time=payload.waiting_time,
        )
    else:
        return payload.task_status.name

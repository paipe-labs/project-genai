from dispatcher.task_info import (
    ScheduledPayload,
    ComfyPipelineOptions,
    TaskOptions,
    TaskStatus,
    TaskInfo,
    TaskStatusPayload,
    StandardPipelineOptions,
    task_status_payload_to_string,
)

import typing
from datetime import datetime


class TaskLog(typing.NamedTuple):
    date: datetime
    task_status_payload: TaskStatusPayload


class Task:
    def __init__(self, task_info: TaskInfo):
        self._provider_id = None
        self._status = TaskStatus.UNSCHEDULED
        self._log: list[TaskLog] = list()
        self._task_info = task_info

    @property
    def task_info(self):
        return self._task_info

    @property
    def id(self):
        return self._task_info.id

    @property
    def status(self):
        return self._status

    @property
    def task_options(self):
        return self._task_info.task_options

    @property
    def max_cost(self):
        return self._task_info.max_cost

    @property
    def provider_id(self):
        return self._provider_id

    @property
    def time_to_money_ratio(self):
        return self._task_info.time_to_money_ratio

    def set_status(self, task_status_payload: TaskStatusPayload) -> None:
        self._status = task_status_payload.task_status
        self._log.append(
            TaskLog(date=datetime.now(), task_status_payload=task_status_payload)
        )
        if isinstance(task_status_payload, ScheduledPayload):
            self._provider_id = task_status_payload.provider_id

    def get_log_string(self):
        return "\n".join(
            t.strftime("%H:%M:%S %d/%m/%Y")
            + " "
            + task_status_payload_to_string(payload)
            for t, payload in self._log
        )


def build_task_from_query(task_id: str, **kwargs) -> Task:
    max_cost = kwargs.get('max_cost')
    time_to_money_ratio = kwargs.get('time_to_money_ratio')
    standard_pipeline = kwargs.get('standard_pipeline')
    comfy_pipeline = kwargs.get('comfy_pipeline')
    task = Task(
        TaskInfo(**{
            'id': task_id,
            'max_cost': max_cost,
            'time_to_money_ratio': time_to_money_ratio,
            'task_options': TaskOptions(**{
                'standard_pipeline': StandardPipelineOptions(**standard_pipeline) if standard_pipeline else None,
                'comfy_pipeline': ComfyPipelineOptions(**{
                    'pipeline_data': comfy_pipeline.get('pipelineData'),
                    'pipeline_dependencies': comfy_pipeline.get('pipelineDependencies'),
                }) if comfy_pipeline else None
            })
        })
    )

    return task

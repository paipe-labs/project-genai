from dispatcher.util.logger import logger
from dispatcher.task_info import (
    TaskStatus,
    TaskInfo,
    TaskResult,
    TaskStatusPayload,
    AssignedToProviderPayload,
    task_status_payload_to_string,
)

import typing
from datetime import datetime


class TaskLog(typing.NamedTuple):
    date: datetime
    task_status_payload: TaskStatusPayload
    # task_status: TaskStatus


class Task:
    def __init__(self, task_info: TaskInfo):
        self._num_failed_attempts = 0
        self._priority = 0
        self._provider_id = None
        self._status = TaskStatus.INIT
        self._log: list[TaskLog] = list()
        self._task_info = task_info

        self._on_completed = None
        self._on_failed = None

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
    def time_to_money_ratio(self):
        return self._task_info.time_to_money_ratio

    @property
    def num_failed_attempts(self):
        return self._num_failed_attempts

    @property
    def priority(self):
        return self._priority

    @property
    def provider_id(self):
        return self._provider_id

    @property
    def log(self):
        return self._log

    def set_priority(self, priority: int) -> None:
        self._priority = priority

    def set_status(self, task_status_payload: TaskStatusPayload) -> None:
        self._status = task_status_payload.task_status
        self._log.append(
            TaskLog(date=datetime.now(), task_status_payload=task_status_payload)
        )
        if isinstance(task_status_payload, AssignedToProviderPayload):
            self._provider_id = task_status_payload.provider_id

    # def set_provider_id(self, provider_id: str) -> None:
    #    self._provider_id = provider_id

    def add_failed_attempt(self) -> None:
        self._num_failed_attempts += 1

    def get_log_string(self):
        return "\n".join(
            t.strftime("%H:%M:%S %d/%m/%Y")
            + " "
            + task_status_payload_to_string(payload)
            for t, payload in self._log
        )

    def set_on_completed(self, on_completed_callback) -> None:
        self._on_completed = on_completed_callback

    def set_on_failed(self, on_failed_callback) -> None:
        self._on_failed = on_failed_callback

    def complete(self, task_result: TaskResult) -> None:
        if self._on_completed == None:
            logger.error("on_completed callback not set in task {id}".format(self.id))
        else:
            self._on_completed(task_result)

    def fail(self) -> None:
        if self._on_failed == None:
            logger.error("on_failed callback not set in task {id}".format(self.id))
        else:
            self._on_failed()

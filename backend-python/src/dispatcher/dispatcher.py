from dispatcher.provider import Provider
from dispatcher.task import Task
from dispatcher.task_info import (
    ScheduledPayload
)
from dispatcher.util.logger import logger

import typing
from typing import Optional

# TODO: reevaluate & move
MAX_PROVIDER_QUEUE_LEN = 50
MAX_SCHEDULING_ATTEMPTS = 5


class Dispatcher:
    def __init__(self) -> None:
        self._providers: dict[str, Provider] = dict()
        # self._tasks: list[Task] = []

    @property
    def providers(self):
        return self._providers

    def add_task(self, task: Task) -> None:
        # self._tasks.append(task)
        for _ in range(MAX_SCHEDULING_ATTEMPTS):
            if self._schedule_task(task):
                return
        logger.warn("Task {id} failed to be scheduled".format(id=task.id))
        task.fail()

    def add_provider(self, provider: Provider) -> None:
        if provider.id in self._providers.keys():
            logger.warn("Provider {id} already added".format(id=provider.id))
            return
        self._providers[provider.id] = provider
        self._providers[provider.id].set_on_closed(
            lambda: self.remove_provider(provider.id)
        )
        self._providers[provider.id].set_on_connection_lost(
            lambda: self.reschedule_tasks_in_progress(provider.id)
        )

    def remove_provider(self, provider_id: str) -> None:
        self.reschedule_tasks_in_progress(provider_id)
        self._providers.pop(provider_id, None)

    def reschedule_tasks_in_progress(self, provider_id: str) -> None:
        if provider_id not in self._providers.keys():
            logger.warn(
                "Provider {id} not in dispatcher".format(id=provider_id))
            return

        for task in self.providers[provider_id].tasks_in_progress:
            self.add_task(task)

    def _schedule_task(self, task: Task) -> bool:
        least_busy_id: Optional[str] = None
        min_queue_length = MAX_PROVIDER_QUEUE_LEN
        for provider in self.providers.values():
            if provider.queue_length > MAX_PROVIDER_QUEUE_LEN or not provider.is_online:
                continue
            if least_busy_id is None or provider.queue_length < min_queue_length:
                least_busy_id = provider.id
                min_queue_length = provider.queue_length

        if least_busy_id is None:
            # TODO: allocate one?
            logger.info("Not found provider for task {id}".format(id=task.id))
            return False

        task.set_status(ScheduledPayload(
            provider_id=least_busy_id,
            min_score=0,
            waiting_time=self._providers[least_busy_id].waiting_time
        ))
        self._providers[least_busy_id].schedule_task(task)
        return True

from dispatcher.provider import Provider
from dispatcher.task import Task
from dispatcher.task_info import (
    ScheduledPayload
)
from dispatcher.util.logger import logger

import typing

# TODO: reevaluate & move
MAX_PROVIDER_QUEUE_LEN = 50
MAX_SCHEDULING_ATTEMPTS = 5


def is_busy_provider(provider: Provider) -> bool:
    return provider.queue_length > MAX_PROVIDER_QUEUE_LEN


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
        # self._providers[provider.id].set_on_updated()

    def remove_provider(self, provider_id: str) -> None:
        if provider_id not in self._providers.keys():
            logger.warn(
                "Provider {id} not in dispatcher".format(id=provider_id))
            return

        provider = self._providers.pop(provider_id)
        for task in provider.tasks_in_progress:
            self.add_task(task)

    def _schedule_task(self, task: Task) -> bool:
        # TODO
        for provider in self._providers.values():
            if is_busy_provider(provider):
                continue

            task.set_status(ScheduledPayload(
                provider_id=provider.id,
                min_score=0,
                waiting_time=provider.waiting_time
            ))
            provider.schedule_task(task)
            return True

        logger.info("Not found provider for task {id}".format(id=task.id))
        return False

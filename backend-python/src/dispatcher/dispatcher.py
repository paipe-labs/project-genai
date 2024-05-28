from dispatcher.util.logger import logger
from dispatcher.provider import Provider
from dispatcher.task import Task
from dispatcher.task_info import TaskStatus, TaskStatusPayload
from dispatcher.task_info import ScheduledPayload

from typing import Optional

MAX_PROVIDER_QUEUE_LEN = 50
MAX_SCHEDULING_ATTEMPTS = 5


class Dispatcher:
    def __init__(self) -> None:
        self._providers: dict[str, Provider] = dict()

    @property
    def providers(self):
        return self._providers

    async def add_task(self, task: Task) -> None:
        for _ in range(MAX_SCHEDULING_ATTEMPTS):
            if await self._schedule_task(task):
                return
        logger.warn("Task {id} failed to be scheduled".format(id=task.id))
        task.set_status(TaskStatusPayload(task_status=TaskStatus.FAILED))

    def add_provider(self, provider: Provider) -> None:
        if provider.id in self._providers.keys():
            logger.warn("Provider {id} already added".format(id=provider.id))
            return
        self._providers[provider.id] = provider

        async def remove_this_provider():
            await self.remove_provider(provider.id)

        self._providers[provider.id].set_on_closed(
            remove_this_provider)

        async def reschedule_this_providers_tasks():
            await self.reschedule_tasks_in_progress(provider.id)

        self._providers[provider.id].set_on_connection_lost(
            reschedule_this_providers_tasks)

    async def remove_provider(self, provider_id: str) -> None:
        await self.reschedule_tasks_in_progress(provider_id)
        self._providers.pop(provider_id, None)

    async def reschedule_tasks_in_progress(self, provider_id: str) -> None:
        if provider_id not in self._providers.keys():
            logger.warn(
                "Provider {id} not in dispatcher".format(id=provider_id))
            return

        provider = self.providers.pop(provider_id)
        for task in provider.tasks_in_progress:
            await self.add_task(task)
        provider.tasks_in_progress.clear()

    async def _schedule_task(self, task: Task) -> bool:
        least_busy_id: Optional[str] = None
        min_queue_length = MAX_PROVIDER_QUEUE_LEN
        for provider in self.providers.values():
            if provider.queue_length > MAX_PROVIDER_QUEUE_LEN or not provider.is_online:
                continue
            if least_busy_id is None or provider.queue_length < min_queue_length:
                least_busy_id = provider.id
                min_queue_length = provider.queue_length

        if least_busy_id is None:
            logger.info("Not found provider for task {id}".format(id=task.id))
            return False

        task.set_status(ScheduledPayload(
            provider_id=least_busy_id,
            min_score=0,
            waiting_time=self._providers[least_busy_id].waiting_time
        ))
        await self._providers[least_busy_id].schedule_task(task)
        return True

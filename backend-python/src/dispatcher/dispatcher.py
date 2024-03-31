from dispatcher.provider import Provider
from dispatcher.task import Task
from dispatcher.task_info import (
    AssignedToProviderPayload,
    TaskStatus,
    TaskStatusPayload,
)
from dispatcher.entry_queue import EntryQueue
from dispatcher.util.logger import logger

import typing
from math import inf

# TODO: reevaluate & move
DISABLE_DISPATCHER_QUEUE_THRESHOLD = 50
TASK_NUM_MAX_ATTEMPTS = 5


def is_busy_provider(provider: Provider) -> bool:
    return provider.queue_length > DISABLE_DISPATCHER_QUEUE_THRESHOLD


class Dispatcher:
    def __init__(self, entry_queue: EntryQueue) -> None:
        self._entry_queue = entry_queue
        self._entry_queue.set_on_task_added(self.task_added_callback)
        self._providers_map: dict[str, Provider] = dict()
        self._min_cost = inf

    @property
    def providers_map(self):
        return self._providers_map

    @property
    def min_cost(self):  # used to be a get_min_cost() method
        return self._min_cost

    def add_provider(self, provider: Provider) -> None:
        if provider.id in self._providers_map.keys():
            logger.warn("Provider {id} already added".format(id=provider.id))
            return
        self._providers_map[provider.id] = provider
        self.calculate_min_cost()
        pid = provider.id
        self._providers_map[provider.id].set_on_closed(
            lambda: self.remove_provider(pid)
        )
        self._providers_map[provider.id].set_on_updated(
            self.calculate_min_cost)

    def remove_provider(self, provider: Provider) -> None:
        if provider.id not in self._providers_map.keys():
            logger.warn(
                "Provider {id} not in dispatcher".format(id=provider.id))
            return

        self._providers_map.pop(provider.id)
        self.calculate_min_cost()

    # TODO: change recalculation of min cost
    def calculate_min_cost(self) -> None:
        self._min_cost = inf
        for provider in self._providers_map.values():
            if is_busy_provider(provider):
                continue

            self._min_cost = min(self._min_cost, provider.min_cost)

    def _schedule_task(self, task: Task) -> bool:
        best_provider: Provider | None = None
        min_score: int | float = inf
        min_waiting_time: int | float = inf
        for provider in self._providers_map.values():
            if is_busy_provider(provider):
                continue
            if provider.min_cost > task.max_cost:
                continue
            waiting_time = provider.waiting_time + provider.estimate_task_waiting_time(
                task
            )
            score = provider.min_cost + waiting_time * task.time_to_money_ratio
            if best_provider is None or score < min_score:
                min_score = score
                min_waiting_time = waiting_time
                best_provider = provider

        if best_provider is None:
            logger.info("Not found provider for task {id}".format(id=task.id))
            return False

        task.set_status(
            AssignedToProviderPayload(
                provider_id=best_provider.id,
                min_score=min_score,
                waiting_time=min_waiting_time,
            )
        )
        best_provider.schedule_task(task)
        self.calculate_min_cost()
        return True

    def pull_task(self) -> None:
        task = self._entry_queue.pop_task(self._min_cost)
        if task is None:
            logger.warn("Queue is empty")
            return

        task.set_status(TaskStatusPayload(
            task_status=TaskStatus.PULLED_BY_DISPATCHER))
        is_scheduled = self._schedule_task(task)
        if not is_scheduled:
            logger.warn("Task {id} failed to be scheduled".format(id=task.id))
            task.add_failed_attempt()
            if task.num_failed_attempts < TASK_NUM_MAX_ATTEMPTS:
                self._entry_queue.add_task(task, task.priority)
            else:
                task.set_status(TaskStatusPayload(
                    task_status=TaskStatus.REJECTED))
                task.fail()

    def task_added_callback(self, task: Task) -> None:
        if task.max_cost < self._min_cost:
            logger.warn(
                "Task {id} rejected by dispatcher: cost too low".format(
                    id=task.id)
            )
            task.set_status(TaskStatusPayload(task_status=TaskStatus.REJECTED))
            return
        self.pull_task()

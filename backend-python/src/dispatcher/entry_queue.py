from dispatcher.task import Task
from dispatcher.task_info import TaskStatus, TaskStatusPayload
from dispatcher.util.logger import logger

from bisect import insort
import typing


class EntryQueue:
    def __init__(self):
        self._queue: list[Task] = list()
        self._on_task_added = None

    def add_task(self, task: Task, task_priority: int):
        task.set_priority(task_priority)
        insort(self._queue, task, key= lambda t: -t.priority) # descending order
        task.set_status(TaskStatusPayload(task_status=TaskStatus.PUSHED_INTO_QUEUE))
        self.on_task_added(task)

    def remove_task(self, task: Task):
        self._queue = [t for t in self._queue if t.id != task.id]

    # Returns the first task from the priority queue with the max_cost > min_cost
    def pop_task(self, min_cost = None) -> Task | None:
        if len(self._queue) == 0:
            return None

        if min_cost == None:
            return self._queue.pop()

        task = None
        for t in reversed(self._queue):
            if t.max_cost > min_cost:
                task = t
                break
        if task != None:
            self.remove_task(task)

        return task

    def set_on_task_added(self, callback):
        self._on_task_added = callback
                
    def on_task_added(self, task: Task):
        if self._on_task_added == None:
            logger.error("No on_task_added callback")
            return
        self._on_task_added(task)


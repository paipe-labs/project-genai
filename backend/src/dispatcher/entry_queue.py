from heapq import Heap
from task import Task, TaskStatus
from dispatcher.utils.noop import NOOP
from typing import Callable

MAX_PRIORITY = 2**53 - 1  # Number.MAX_SAFE_INTEGER

class EntryQueue:
    def init(self):
        self.queue = Heap(lambda a, b: a.getPriority() - b.getPriority())
    
    def addTask(self, task: Task, priority: int) -> None:
        task.setPriority(priority)
        self.queue.add(task)
        
        task.setStatus(TaskStatus.PushedIntoQueue)
        self.taskAdded(task)
    
    def removeTask(self, task: Task) -> None:
        self.queue.remove(task)
    
    def popTask(self, min_price: int = None) -> Task or None:
        for task in self.queue:
            if min_price is None or task.getMaxPrice() > min_price:
                self.queue.remove(task)
                return task
        return None

    taskAdded: Callable[[Task], None] = NOOP

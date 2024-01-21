from typing import List, Dict
from dispatcher.utils.runtime import warnIf
from dispatcher.provider import Provider
from dispatcher.task import Task, TaskStatus
from dispatcher.entry_queue import EntryQueue

DISABLE_DISPATCHER_QUEUE_THRESHOLD = 50
TASK_MAX_ATTEMPTS = 5

def isBusyProvider(provider: Provider) -> bool:
    return provider.getQueueLength() > DISABLE_DISPATCHER_QUEUE_THRESHOLD

class Dispatcher:
    def __init__(self, entryQueue: EntryQueue):
        self.providers = set()
        self.providersMap = {}
        self.minCost = float('inf')
        self.entry_queue = entryQueue
        self.entry_queue.taskAdded = self.taskAddedCb

    def addProvider(self, provider: Provider) -> None:
        if warnIf(provider in self.providers, f"Provider with id {provider.id} already added"):
            return
        self.providersMap[provider.id] = provider
        self.providers.add(provider)
        self.calcMinCost()
        provider.onClosed = lambda: (self.removeProvider(provider), self.calcMinCost())
        provider.onUpdated = self.calcMinCost

    def removeProvider(self, provider: Provider) -> None:
        if warnIf(provider not in self.providers, f"Provider with id {provider.id} wasn't added"):
            return
        del self.providersMap[provider.id]
        self.providers.remove(provider)
        self.calcMinCost()

    def minCostUpdated(self, provider: Provider) -> None:
        self.calcMinCost()

    def calcMinCost(self) -> None:
        self.minCost = float('inf')
        for provider in self.providers:
            if isBusyProvider(provider):
                continue
            if warnIf(provider.getMinCost() > float('inf'), f"Min cost in provider {provider.id} is larger than limit"):
                continue
            self.minCost = min(self.minCost, provider.getMinCost())

    def getMinCost(self) -> float:
        return self.minCost

    def scheduleTask(self, task: Task) -> bool:
        bestProvider = None
        lowestScore = float('inf')
        lowestWaitingTime = float('inf')
        for provider in self.providers:
            if isBusyProvider(provider):
                continue

            cost = provider.getMinCost()

            if cost > task.getMaxPrice():
                continue

            waitingTime = provider.estimator.getWaitingTime() + provider.estimator.estimateTaskWaitingTime(task)
            score = cost + waitingTime * task.getMoneyTimeRatio()

            if score < lowestScore:
                lowestScore = score
                lowestWaitingTime = waitingTime
                bestProvider = provider

        if bestProvider:
            task.setStatus(TaskStatus.SetToProvider, {
                'providerId': bestProvider.id,
                'minScore': lowestScore,
                'waitingTime': lowestWaitingTime
            })
            bestProvider.scheduleTask(task)
            self.calcMinCost()
            return True
        return False
    def pullTask(self) -> None:
        task = self.entry_queue.popTask(self.getMinCost())
        if not task:
            return

        task.setStatus(TaskStatus.PulledByDispatcher)

        scheduled = self.scheduleTask(task)
        if warnIf(not scheduled, f"Task {task.id} wasn't scheduled"):
            task.addFailedAttempt()
            if task.getFailedAttempts() < TASK_MAX_ATTEMPTS:
                self.entry_queue.addTask(task, task.getPriority())
            else:
                task.setStatus(TaskStatus.RejectedByDispatcher)
                task.fail()

    def taskAddedCb(self, task: Task) -> None:
        if task.getMaxPrice() < self.getMinCost():
            print(f"Task rejected by dispatcher {task.id}")
            task.setStatus(TaskStatus.RejectedByDispatcher)
            return
        self.pullTask()


from dispatcher.protocol.meta import PrivateMetaInfo, PublicMetaInfo
from dispatcher.task import Task
from dispatcher.utils.runtime import warnIf

class ProviderEstimator:
    def init(self, public_meta: PublicMetaInfo, private_meta: PrivateMetaInfo):
        self.estimatedTime = {}
        self.totalEstimatedTime = 0
        self.public_meta = public_meta
        self.private_meta = private_meta
    
    def updatePublicMeta(self, public_meta: PublicMetaInfo) -> None:
        self.public_meta = public_meta
    
    def updatePrivateMeta(self, private_meta: PrivateMetaInfo) -> None:
        self.private_meta = private_meta
    
    def addTask(self, task: Task) -> None:
        estimatedTime = self.estimateTaskWaitingTime(task)
        self.estimatedTime[task] = estimatedTime
        self.totalEstimatedTime += estimatedTime
    
    def removeTask(self, task: Task) -> None:
        if task not in self.estimatedTime:
            warnIf(True, f"Task {task.id} is not in the estimator queue")
            return
        estimatedTime = self.estimatedTime[task]
        del self.estimatedTime[task]
        self.totalEstimatedTime -= estimatedTime
    
    def getWaitingTime(self) -> int:
        return self.totalEstimatedTime
    
    def estimateTaskWaitingTime(self, task: Task) -> int:
        # TODO: Do business logic here, estimate time based on the task and provider meta
        return 4  # milliseconds

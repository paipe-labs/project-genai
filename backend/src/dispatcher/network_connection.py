from typing import Callable
from dispatcher.protocol.meta import PublicMetaInfo
from dispatcher.protocol.task import TaskResult, Task, TaskStatus
from dispatcher.utils.noop import NOOP

class NetworkConnection:
    async def sendTask(self, task: Task) -> None:
        await task.setStatus(TaskStatus.SentToProvider)
  
    async def abortTask(self, task: Task) -> None:
        task.setStatus(TaskStatus.Aborted)
    
    async def close(self) -> None:
        pass
  
    onMetaUpdated: Callable[[PublicMetaInfo], None] = NOOP

    onLostConnection: Callable[[], None] = NOOP

    onConnectionRestored: Callable[[], None] = NOOP

    onTaskCompleted: Callable[[Task, TaskResult], None] = NOOP

    onTaskFailed: Callable[[Task, str], None] = NOOP

  # onTaskTimeout: Callable[[Task], None] = NOOP

  # onTaskRejected, onTaskAccepted, onProgressUpdate

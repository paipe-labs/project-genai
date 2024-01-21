from dispatcher.network_connection import NetworkConnection 
from dispatcher.protocol.meta import PrivateMetaInfo, PublicMetaInfo 
from dispatcher.protocol.task import TaskResult 
from dispatcher.provider_estimator import ProviderEstimator 
from dispatcher.task import Task, TaskStatus 
from dispatcher.utils.logger import logger 
from dispatcher.utils.noop import NOOP
from src.utils.timeouts import setTimeout, clearTimeout

RETRY_ATTEMPTS = 3 
OFFLINE_TIMEOUT = 3000 # 3 seconds

class Provider: 
    def init(self, id, public_meta: PublicMetaInfo, private_meta: PrivateMetaInfo, network_connection: NetworkConnection): 
        self.id = id 
        self.estimator = ProviderEstimator(public_meta, private_meta)

        self.online = True
        self.offline_timeout = None
        self.in_progress = set()

        self.public_meta = public_meta
        self.private_meta = private_meta
        self.network_connection = network_connection

        network_connection.on_meta_updated = self.update_public_meta
        network_connection.on_lost_connection = self.start_offline
        network_connection.on_connection_restored = self.stop_offline
        network_connection.on_task_completed = self.task_completed
        network_connection.on_task_failed = self.task_failed

def start_offline(self):
    if self.offline_timeout:
        return
    self.offline_timeout = setTimeout(self.dispose, 1000)
    self.online = False
    self.on_updated()

def dispose(self):
    self.network_connection.close()
    for task in self.in_progress:
        task.set_status(TaskStatus.FailedByProvider, {"reason": "Provider is offline"})
        task.fail()
    self.on_closed()

def stop_offline(self):
    if not self.offline_timeout:
        return
    clearTimeout(self.offline_timeout)
    self.offline_timeout = None
    self.online = True
    self.on_updated()

def update_public_meta(self, public_meta: PublicMetaInfo):
    self.public_meta = public_meta
    self.estimator.update_public_meta(public_meta)
    self.on_updated()

def update_private_meta(self, private_meta: PrivateMetaInfo):
    self.private_meta = private_meta
    self.estimator.update_private_meta(private_meta)
    self.on_updated()

def get_queue_length(self):
    return len(self.in_progress)

def schedule_task(self, task: Task):
    task.set_provider_id(self.id)
    print(f"Task {task.id} scheduled in provider {self.id}")
    self.estimator.add_task(task)
    self.async_schedule_task(task)

async def async_schedule_task(self, task: Task):
    for i in range(RETRY_ATTEMPTS):
        try:
            await self.network_connection.send_task(task)
            self.in_progress.add(task)
            return
        except:
            task.set_status(TaskStatus.SentFailed, {"attempt": i})
    self.task_failed(task, "Failed to send task")

def abort_task(self, task: Task):
    self.task_finished(task)

    async def abort():
        try:
            await self.network_connection.abort_task(task)
        except Exception as e:
            logger.error(e)
    
    abort()

def task_finished(self, task: Task):
    self.estimator.remove_task(task)
    self.in_progress.remove(task)

def task_failed(self, task: Task, reason = None):
    if task not in self.in_progress:
        return
    self.task_finished(task)
    task.add_failed_attempt()
    task.set_status(TaskStatus.FailedByProvider, {"reason": reason})
    task.fail()

def task_completed(self, task: Task, result: TaskResult):
    if task not in self.in_progress:
        return
    self.task_finished(task)
    task.set_status(TaskStatus.Completed)
    task.complete(result)

def get_min_cost(self):
    if not self.online:
        return float('inf')
    return self.public_meta.min_cost

def set_on_closed(self, callback):
    self.on_closed = callback

def set_on_updated(self, callback):
    self.on_updated = callback
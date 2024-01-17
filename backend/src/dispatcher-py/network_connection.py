from meta_info import PublicMetaInfo
from task import Task
from task_info import TaskStatusPayload, TaskStatus, TaskResult
from util.logger import logger

import typing


class NetworkConnection:
    def __init__(self):
        self._on_task_failed = None
        self._on_public_meta_info_updated = None
        self._on_connection_lost = None
        self._on_connection_restored = None
        self._on_task_completed = None
        self._on_task_failed = None

    # these return Promise<void> in ts - call with await
    async def send_task(self, task: Task):
        task.set_status(TaskStatusPayload(task_status=TaskStatus.SENT_TO_PROVIDER))
        # TODO

    async def abort_task(self, task: Task):
        task.set_status(TaskStatusPayload(task_status=TaskStatus.ABORTED))
        # TODO

    async def close(self):
        # TODO: drop websocket connection
        pass

    def set_on_meta_info_updated(self, callback):
        self._on_public_meta_info_updated = callback

    def set_on_connection_lost(self, callback):
        self._on_connection_lost = callback

    def set_on_connection_restored(self, callback):
        self._on_connection_restored = callback

    def set_on_task_completed(self, callback):
        self._on_task_completed = callback

    def set_on_task_failed(self, callback):
        self._on_task_failed = callback

    def on_meta_info_updated(self, meta_info: PublicMetaInfo):
        if self._on_public_meta_info_updated == None:
            logger.warn("on_meta_info_updated callback is empty")
            return
        self._on_public_meta_info_updated(meta_info)
        
    def on_connection_lost(self):
        if self._on_connection_lost == None:
            logger.warn("on_connection_lost callback is empty")
            return
        self._on_connection_lost()

    def on_connection_restored(self):
        if self._on_connection_restored == None:
            logger.warn("on_connection_restored callback is empty")
            return
        self._on_connection_restored()

    def on_task_completed(self, task: Task, task_result: TaskResult):
        if self._on_task_completed == None:
            logger.warn("on_task_completed callback is empty")
            return
        self._on_task_completed(task, task_result)


    def on_task_failed(self, task: Task, reason: str):
        if self._on_task_failed == None:
            logger.warn("on_task_failed callback is empty")
            return
        self._on_task_failed(task, reason)

    def on_task_timeout(self, task: Task):
        pass

    def on_task_rejected(self, task: Task):
        pass

    def on_task_accepted(self, task: Task):
        pass

    def on_progress_update(self):
        pass


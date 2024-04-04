from math import inf
from typing import Callable, Optional

import flask_sock

from dispatcher.meta_info import PublicMetaInfo, PrivateMetaInfo
from dispatcher.network_connection import NetworkConnection
from dispatcher.task import Task
from dispatcher.task_info import (
    FailedByProvider,
    TaskStatusPayload,
    TaskStatus,
    TaskResult,
)
from dispatcher.util.logger import logger


class Provider:
    def __init__(
            self,
            provider_id: str,
            public_meta_info: PublicMetaInfo,
            private_meta_info: PrivateMetaInfo,
            network_connection: NetworkConnection,
    ):
        self._id = provider_id
        self._pub_meta_info = public_meta_info
        self._pr_meta_info = private_meta_info
        self._is_online = True

        self._on_closed_callback: Optional[Callable[[], None]] = None
        self._on_updated_callback: Optional[Callable[[], None]] = None

        self._in_progress: set[Task] = set()

        self._network_connection = network_connection
        self._network_connection.set_on_meta_info_updated(
            self.update_public_meta_info)
        self._network_connection.set_on_connection_lost(self.start_offline)
        self._network_connection.set_on_connection_restored(self.stop_offline)
        self._network_connection.set_on_task_completed(self.task_completed)
        self._network_connection.set_on_task_failed(self.task_failed)

    @property
    def id(self):
        return self._id

    @property
    def network_connection(self):
        return self._network_connection

    @property
    def queue_length(self):
        return len(self._in_progress)

    @property
    def waiting_time(self):
        return self.queue_length

    @property
    def tasks_in_progress(self):
        return self._in_progress

    def start_offline(self):
        if self._offline_timeout is not None:
            return
        self._is_online = False
        self.on_updated()

    def dispose(self):
        # TODO
        # self._network_connection.close()
        for task in self._in_progress:
            task.set_status(FailedByProvider(reason="Provider is offline"))
            self.on_closed()

    def stop_offline(self):
        if self._offline_timeout is None:
            return
        # TODO
        # clearTimeout(self._offline_timeout)
        self._offline_timeout = None
        self._is_online = True
        self.on_updated()

    def update_public_meta_info(self, meta_info: PublicMetaInfo):
        self._pub_meta_info = meta_info
        self.on_updated()

    def update_private_meta_info(self, meta_info: PrivateMetaInfo):
        self._pr_meta_info = meta_info
        self.on_updated()

    def schedule_task(self, task: Task):
        # logger.info("Task {task} scheduled in provider {provider}".format(task.id, self._id))
        self.async_schedule_task(task)

    def async_schedule_task(self, task: Task):  # TODO make async)))
        try:
            # Assuming send_task is an async method of network_connection
            self._in_progress.add(task)
            self.network_connection.send_task(task)
            task.in_progress = True
            return
        except flask_sock.ConnectionClosed:
            logger.warn(
                "got ConnectionClosed exception on send_task in provider {id}".format(id=self._id))
            self.on_closed()
            return
        except Exception as e:
            logger.error("unhandled exception in async_schedule_task:", e)
            return

    def abort_task(self, task: Task):
        self.task_finished(task)
        # TODO
        # (async () => {
        #  try {
        #    await this.network_connection.abortTask(task);
        #  } catch (e) {
        #    logger.error(e);
        #  }
        # })();

    def task_finished(self, task: Task):
        self._in_progress.remove(task)
        self.on_updated()

    def task_failed(self, task: Task, fail_reason: str):
        if task not in self._in_progress:
            return
        self.task_finished(task)
        task.set_status(FailedByProvider(reason=fail_reason))
        task.fail()

    def task_completed(self, task: Task, result: TaskResult):
        if task not in self._in_progress:
            return
        self.task_finished(task)
        task.set_status(TaskStatusPayload(task_status=TaskStatus.COMPLETED))
        task.complete(result)

    def set_on_closed(self, callback: Callable[[], None]):
        self._on_closed_callback = callback

    def set_on_updated(self, callback: Callable[[], None]):
        self._on_updated_callback = callback

    def on_closed(self):
        if self._on_closed_callback is None:
            logger.warn(
                "On updated callback not set in provider {id}".format(
                    id=self._id)
            )
            return
        self._on_closed_callback()

    def on_updated(self):
        if self._on_updated_callback is None:
            logger.warn(
                "On updated callback not set in provider {id}".format(
                    id=self._id)
            )
            return
        self._on_updated_callback()

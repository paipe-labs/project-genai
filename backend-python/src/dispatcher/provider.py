import flask_sock

from dispatcher.provider_estimator import ProviderEstimator
from dispatcher.network_connection import NetworkConnection
from dispatcher.task import Task
from dispatcher.task_info import (
    FailedByProvider,
    TaskStatusPayload,
    TaskStatus,
    TaskResult,
)
from dispatcher.util.logger import logger
from dispatcher.meta_info import PublicMetaInfo, PrivateMetaInfo
import asyncio

import typing
from math import inf

# TODO: reevaluate & move
NUM_RETRY_ATTEMPTS = 3
OFFLINE_TIMEOUT = 3000


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
        self._offline_timeout = None  # NodeJS.Timeout

        self._on_closed_callback = None
        self._on_updated_callback = None

        self._in_progress: set[Task] = set()
        self._estimator = ProviderEstimator(self._pub_meta_info, self._pr_meta_info)

        self._network_connection = network_connection
        self._network_connection.set_on_meta_info_updated(self.update_public_meta_info)
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
    def estimator(self):
        return self._estimator

    @property
    def queue_length(self):  # used to be a method
        return len(self._in_progress)

    @property
    def waiting_time(self):
        return self._estimator.waiting_time

    @property
    def min_cost(self):  # used to be a method
        if not self._is_online:
            return inf
        return self._pub_meta_info.min_cost

    def start_offline(self):
        if self._offline_timeout is not None:
            return
        # TODO
        # self._offline_timeot = setTimeout(
        # call dispose, on_closed
        # 1000
        # )

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

    # why is it mutable?
    def update_public_meta_info(self, meta_info: PublicMetaInfo):
        self._pub_meta_info = meta_info
        self._estimator.update_public_meta_info(meta_info)
        self.on_updated()

    def update_private_meta_info(self, meta_info: PrivateMetaInfo):
        self._pr_meta_info = meta_info
        self._estimator.update_private_meta_info(meta_info)
        self.on_updated()

    def schedule_task(self, task: Task):
        # logger.info("Task {task} scheduled in provider {provider}".format(task.id, self._id))
        self._estimator.add_task(task)
        self.async_schedule_task(task)

    def async_schedule_task(self, task: Task):  # TODO make async)))
        try:
            # Assuming send_task is an async method of network_connection
            self.network_connection.send_task(task)
            task.in_progress = True
            return
        except flask_sock.ConnectionClosed:
            # TODO: make sure task is rescheduled somewhere
            logger.warn("got ConnectionClosed exception on send_task in provider {id}".format(id=self._id))
            self.on_closed()
            return
        except Exception as e:
            logger.error("unhandled exception in async_schedule_task:", e)
            return

    def estimate_task_waiting_time(self, task: Task) -> int:
        return self._estimator.estimate_task_time(task)

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
        self._estimator.remove_task(task)
        self._in_progress.remove(task)

    def task_failed(self, task: Task, fail_reason: str):
        if task not in self._in_progress:
            return
        self.task_finished(task)
        task.add_failed_attempt()
        task.set_status(FailedByProvider(reason=fail_reason))
        task.fail()
        self.on_updated()

    def task_completed(self, task: Task, result: TaskResult):
        if task not in self._in_progress:
            return
        self.task_finished(task)
        task.set_status(TaskStatusPayload(task_status=TaskStatus.COMPLETED))
        task.complete(result)
        self.on_updated()

    def set_on_closed(self, callback):
        self._on_closed_callback = callback

    def set_on_updated(self, callback):
        self._on_updated_callback = callback

    def on_closed(self):
        if self._on_closed_callback is None:
            logger.warn(
                "On updated callback not set in provider {id}".format(id=self._id)
            )
            return
        self._on_closed_callback()

    def on_updated(self):
        if self._on_updated_callback is None:
            logger.warn(
                "On updated callback not set in provider {id}".format(id=self._id)
            )
            return
        self._on_updated_callback()

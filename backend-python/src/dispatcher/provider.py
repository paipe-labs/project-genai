from dispatcher.util.logger import logger
from dispatcher.meta_info import PublicMetaInfo, PrivateMetaInfo
from dispatcher.network_connection import NetworkConnection
from dispatcher.task import Task
from dispatcher.task_info import (
    FailedByProvider,
    TaskStatusPayload,
    TaskStatus
)

from typing import Callable, Optional, Awaitable
from websockets.exceptions import ConnectionClosed
from fastapi import WebSocket, WebSocketDisconnect
import asyncio


OFFLINE_TIMEOUT = 3


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
        self._in_progress: set[Task] = set()

        self._network_connection = network_connection
        self._is_online = True
        self._offline_event: asyncio.Event

        self._on_closed_callback: Optional[Callable[[
        ], Awaitable[None]]] = None
        self._on_connection_lost_callback: Optional[Callable[[
        ], Awaitable[None]]] = None

    @property
    def id(self):
        return self._id

    @property
    def queue_length(self):
        return len(self._in_progress)

    @property
    def waiting_time(self):
        return self.queue_length

    @property
    def is_online(self):
        return self._is_online

    @property
    def tasks_in_progress(self):
        return self._in_progress

    async def start_offline(self):
        if not self._is_online:
            logger.warning("start_offline called twice")
            return

        self._is_online = False
        self._offline_event = asyncio.Event()
        try:
            await asyncio.wait_for(self._offline_event.wait(), OFFLINE_TIMEOUT)
        except TimeoutError:
            for task in self._in_progress:
                task.set_status(FailedByProvider(reason="Provider is offline"))
            await self.on_closed()

    def stop_offline(self):
        if self._is_online:
            logger.warning("stop_offline called twice")
            return
        self._is_online = True
        self._offline_event.set

    def restore_connection(self, ws: WebSocket):
        self._network_connection.restore_connection(ws)
        self.stop_offline()

    def update_public_meta_info(self, meta_info: PublicMetaInfo):
        self._pub_meta_info = meta_info

    def update_private_meta_info(self, meta_info: PrivateMetaInfo):
        self._pr_meta_info = meta_info

    async def schedule_task(self, task: Task):
        try:
            self._in_progress.add(task)
            await self._network_connection.send_task(task)
        except (ConnectionClosed, WebSocketDisconnect):
            logger.warning(
                "got ConnectionClosed exception on send_task in provider {id}".format(id=self._id))
            await self.on_closed()
        except Exception as e:
            logger.error(f"unhandled exception in schedule_task: {e}")
            await self.on_closed()

    async def abort_task(self, task: Task):
        if task not in self._in_progress:
            logger.warning(
                f"abort_task called on task {task.id} not in progress")
            return

        try:
            self._in_progress.remove(task)
            task.set_status(TaskStatusPayload(task_status=TaskStatus.ABORTED))
            await self._network_connection.abort_task(task)
        except (ConnectionClosed, WebSocketDisconnect):
            logger.warning(
                "got ConnectionClosed exception on abort_task in provider {id}".format(id=self._id))
            await self.on_closed()
        except Exception as e:
            logger.error(f"unhandled exception in abort_task: {e}")
            await self.on_closed()

    def task_failed(self, task: Task, fail_reason: str):
        if task not in self._in_progress:
            return
        self._in_progress.remove(task)
        task.set_status(FailedByProvider(reason=fail_reason))

    def task_completed(self, task: Task):
        if task not in self._in_progress:
            return
        self._in_progress.remove(task)
        task.set_status(TaskStatusPayload(task_status=TaskStatus.COMPLETED))

    def set_on_closed(self, callback: Callable[[], None]):
        self._on_closed_callback = callback

    def set_on_connection_lost(self, callback: Callable[[], None]):
        self._on_connection_lost_callback = callback

    async def on_closed(self):
        if self._on_closed_callback is None:
            logger.warning(
                "On updated callback not set in provider {id}".format(
                    id=self._id)
            )
            return
        await self._on_closed_callback()

    async def on_connection_lost(self):
        if self._on_connection_lost_callback is None:
            logger.warning(
                "On connection lost callback not set in provider {id}".format(
                    id=self._id)
            )
            return
        await self.start_offline()
        await self._on_connection_lost_callback()

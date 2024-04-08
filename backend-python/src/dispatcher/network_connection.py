from dispatcher.task import Task
from dispatcher.task_info import TaskStatusPayload, TaskStatus

import typing


class NetworkConnection:
    def __init__(self):
        pass

    async def send_task(self, task: Task):
        task.set_status(TaskStatusPayload(
            task_status=TaskStatus.SENT_TO_PROVIDER))

    async def abort_task(self, task: Task):
        task.set_status(TaskStatusPayload(task_status=TaskStatus.ABORTED))

    async def close(self):
        pass

    def restore_connection(self, connection_object):
        pass

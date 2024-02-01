from dispatcher.network_connection import NetworkConnection
from dispatcher.task_info import TaskOptions
from dispatcher.task import Task
from dispatcher.util.logger import logger
from dataclasses import asdict
import websocket
import json

class WSConnection(NetworkConnection):
    def __init__(self, ws: websocket.WebSocket):
        super().__init__()
        self.ws = ws

    def restoreConnection(self, ws: websocket.WebSocket):
        self.ws = ws
        self.onConnectionRestored()

    def send_task(self, task: Task):
        clientTask = {
          'options': {k: v for k, v in asdict(task.task_options).items() if v is not None},
          'taskId': task.id,
        }
        self.ws.send(json.dumps(clientTask))

        return None 

    def abortTask(self, task: Task):
        self.ws.send(json.dumps({
          'type': 'abort',
          'task_id': task.id,
        }))
        return None 

class ClientTask:
    def __init__(self, options: TaskOptions, taskId: str):
        self.options = options
        self.taskId = taskId

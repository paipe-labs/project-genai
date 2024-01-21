from dispatcher.network_connection import NetworkConnection
from dispatcher.protocol.task import TaskOptions
from dispatcher.task import Task
import websocket
import json

class WSConnection(NetworkConnection):
    def __init__(self, ws: websocket.WebSocket):
        super().__init__()
        self.ws = ws

    def restoreConnection(self, ws: websocket.WebSocket):
        self.ws = ws
        self.onConnectionRestored()

    def sendTask(self, task: Task):
        clientTask = {
          'options': task.getTaskOptions(),
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

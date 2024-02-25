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
        def options_as_dict(pipeline):
            if not pipeline:
                return None
            return {k: v for k, v in asdict(pipeline).items() if v is not None} 
            
        clientTask = {
          'options': options_as_dict(task.task_options.standard_pipeline),
          'comfyOptions': options_as_dict(task.task_options.comfy_pipeline),
          'taskId': task.id,
        }
        self.ws.send(json.dumps(clientTask))

    def abortTask(self, task: Task):
        self.ws.send(json.dumps({
          'type': 'abort',
          'task_id': task.id,
        }))

from dispatcher.network_connection import NetworkConnection
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

    def send_task(self, task: Task):
        clientTask = {'taskId': task.id}

        if task.task_options.standard_pipeline:
            clientTask['options'] = {
                'prompt': task.task_options.standard_pipeline.prompt,
                'model': task.task_options.standard_pipeline.model,
                'size': task.task_options.standard_pipeline.size,
                'steps': task.task_options.standard_pipeline.steps,
            }

        if task.task_options.comfy_pipeline:
            clientTask['comfyOptions'] = {
                'pipelineData': task.task_options.comfy_pipeline.pipeline_data,
                'pipelineDependencies': task.task_options.comfy_pipeline.pipeline_dependencies,
            }
        self.ws.send(json.dumps(clientTask))

    def abortTask(self, task: Task):
        self.ws.send(
            json.dumps(
                {
                    "type": "abort",
                    "task_id": task.id,
                }
            )
        )

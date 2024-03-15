import websocket
import json
import jsonschema

from constants.static import TASK_RESULT_SCHEMA_PATH, TASK_SCHEMA_PATH
from dispatcher.network_connection import NetworkConnection
from dispatcher.task import Task
import websocket
import json
from dispatcher.util.logger import logger
from dataclasses import asdict


class WSConnection(NetworkConnection):
    def __init__(self, ws: websocket.WebSocket):
        super().__init__()
        self.ws = ws

        with open(TASK_SCHEMA_PATH) as task_schema:
            self.task_schema = json.load(task_schema)
        with open(TASK_RESULT_SCHEMA_PATH) as task_result_schema:
            self.task_result_schema = json.load(task_result_schema)

    def restoreConnection(self, ws: websocket.WebSocket):
        self.ws = ws
        self.onConnectionRestored()

    def send_task(self, task: Task):
        clientTask = {"taskId": task.id}

        clientTask["options"] = (
            {
                "prompt": task.task_options.standard_pipeline.prompt,
                "model": task.task_options.standard_pipeline.model,
                "size": task.task_options.standard_pipeline.size,
                "steps": task.task_options.standard_pipeline.steps,
            }
            if task.task_options.standard_pipeline
            else None
        )

        clientTask["comfyOptions"] = (
            {
                "pipelineData": task.task_options.comfy_pipeline.pipeline_data,
                "pipelineDependencies": task.task_options.comfy_pipeline.pipeline_dependencies,
            }
            if task.task_options.comfy_pipeline
            else None
        )

        try:
            jsonschema.validate(instance=clientTask, schema=self.task_schema)
            self.ws.send(json.dumps(clientTask))
        except Exception as e:
            logger.warn(
                f"Task {task.id} was not sent due to schema validation error: {e}"
            )

    def abortTask(self, task: Task):
        clientTaskAbort = {
            "type": "abort",
            "taskId": task.id,
        }

        try:
            jsonschema.validate(instance=clientTaskAbort, schema=self.task_schema)
            self.ws.send(json.dumps(clientTaskAbort))
        except Exception as e:
            logger.warn(
                f"Task {task.id} was not aborted due to schema validation error: {e}"
            )

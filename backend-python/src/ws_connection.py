from constants.static import TASK_SCHEMA

from dispatcher.util.logger import logger
from dispatcher.network_connection import NetworkConnection
from dispatcher.task import Task

from fastapi import WebSocket
import jsonschema


class WSConnection(NetworkConnection):
    def __init__(self, ws: WebSocket):
        super().__init__()
        self.ws = ws

    async def restore_connection(self, ws: WebSocket):
        self.ws = ws

    async def send_task(self, task: Task):
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
            jsonschema.validate(instance=clientTask, schema=TASK_SCHEMA)
        except Exception as e:
            logger.error(
                f"Task {clientTask} was not sent due to schema validation error: {e}"
            )
            return

        await self.ws.send_json(clientTask)

    async def abortTask(self, task: Task):
        clientTaskAbort = {
            "type": "abort",
            "taskId": task.id,
        }
        await self.ws.send_json(clientTaskAbort)

import sys
sys.path.append("/backend-python/src")

from ws_connection import WSConnection
from dispatcher.task import build_task_from_query
import copy
import pytest
import json


COMMON_TASK_ID = "1"
COMMON_TASK_DATA = {"max_cost": 15, "time_to_money_ratio": 1}

pytest_plugins = ("pytest_asyncio",)


class WSConnectionEchoMock:
    def __init__(self) -> None:
        self.payload = ""

    async def send_json(self, payload):
        self.payload = json.dumps(payload)

    async def recv(self) -> str:
        payload = self.payload
        self.payload = ""
        return payload


@pytest.mark.asyncio
async def test_ws_connection_valid_schema_standard():
    task_data = copy.deepcopy(COMMON_TASK_DATA)
    standard_pipeline_options = {
        "standard_pipeline": {
            "prompt": "space surfer",
            "model": "SD2.1",
            "size": {"height": 512, "width": 512},
            "steps": None,
        }
    }
    task_data.update(standard_pipeline_options)
    task = build_task_from_query(COMMON_TASK_ID, **task_data)

    echo = WSConnectionEchoMock()
    ws_connection = WSConnection(echo)

    await ws_connection.send_task(task)
    assert (
        await echo.recv()
        == """{"taskId": "1", "options": {"prompt": "space surfer", "model": "SD2.1", "size": {"height": 512, "width": 512}, "steps": null}, "comfyOptions": null}"""
    )


@pytest.mark.asyncio
async def test_ws_connection_invalid_schema_standard():
    task_data = copy.deepcopy(COMMON_TASK_DATA)
    standard_pipeline_options = {
        "standard_pipeline": {
            "prompt": "space surfer",
            "model": "SD2.1",
            "size": 512,
        }
    }
    task_data.update(standard_pipeline_options)
    task = build_task_from_query(COMMON_TASK_ID, **task_data)

    echo = WSConnectionEchoMock()
    ws_connection = WSConnection(echo)

    await ws_connection.send_task(task)
    assert await echo.recv() == ""


@pytest.mark.asyncio
async def test_ws_connection_valid_schema_comfy():
    task_data = copy.deepcopy(COMMON_TASK_DATA)
    comfy_pipeline_options = {
        "comfy_pipeline": {
            "pipelineData": "somePipeline",
            "pipelineDependencies": {"images": "imageNameToImage map"},
        }
    }
    task_data.update(comfy_pipeline_options)
    task = build_task_from_query(COMMON_TASK_ID, **task_data)

    echo = WSConnectionEchoMock()
    ws_connection = WSConnection(echo)
    await ws_connection.send_task(task)
    assert (
        await echo.recv()
        == """{"taskId": "1", "options": null, "comfyOptions": {"pipelineData": "somePipeline", "pipelineDependencies": {"images": "imageNameToImage map"}}}"""
    )


@pytest.mark.asyncio
async def test_ws_connection_invalid_schema_comfy():
    task_data = copy.deepcopy(COMMON_TASK_DATA)
    comfy_pipeline_options = {
        "comfy_pipeline": {
            "pipelineDependencies": None,
        }
    }
    task_data.update(comfy_pipeline_options)
    task = build_task_from_query(COMMON_TASK_ID, **task_data)

    echo = WSConnectionEchoMock()
    ws_connection = WSConnection(echo)
    await ws_connection.send_task(task)
    assert await echo.recv() == ""

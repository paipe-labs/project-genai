from constants.env import ENFORCE_JWT_AUTH, HTTP_WS_PORT, WS_TASK_TIMEOUT
from constants.static import TASK_RESULT_SCHEMA

from dispatcher.util.logger import logger
from dispatcher.dispatcher import Dispatcher
from dispatcher.meta_info import PrivateMetaInfo, PublicMetaInfo
from dispatcher.provider import Provider
from dispatcher.task import build_task_from_query
from utils.query_check_result import QueryValidationResult

from storage import StorageManager, UsersStorage
from verification import verify
from ws_connection import WSConnection

import json
import jsonschema
import uuid
import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, Request, Response, status, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from websockets.exceptions import ConnectionClosed


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"]
)

dispatcher = Dispatcher()

storage_manager = StorageManager()
users_storage = UsersStorage()

registered_providers = {}

connections = {}
task_ready = {}


def find_key_by_value(dict, value):
    return next((k for k, v in dict.items() if v == value), None)


def check_data_and_state(
    data: dict, from_comfy_inf: bool = False
) -> QueryValidationResult:
    token = data.get("token")
    if ENFORCE_JWT_AUTH and not verify(token):
        return QueryValidationResult(
            is_ok=False,
            error_data={"ok": False, "error": "operation is not permitted"},
            error_code=401,
        )

    if len(registered_providers) == 0:
        return QueryValidationResult(
            is_ok=False,
            error_data={"ok": False, "error": "no nodes available"},
            error_code=403,
        )

    if from_comfy_inf:
        pipeline_data = data.get("pipelineData")
        if not pipeline_data:
            return QueryValidationResult(
                is_ok=False,
                error_data={"ok": False,
                            "error": "image pipeline is not specified"},
                error_code=404,
            )
    else:
        comfy_pipeline = data.get("comfyPipeline")
        standard_pipeline = data.get("standardPipeline")
        if not standard_pipeline and not comfy_pipeline:
            return QueryValidationResult(
                is_ok=False,
                error_data={"ok": False,
                            "error": "image pipeline is not specified"},
                error_code=404,
            )

        if standard_pipeline:
            prompt = standard_pipeline.get("prompt")
            if not prompt:
                return QueryValidationResult(
                    is_ok=False,
                    error_data={
                        "ok": False,
                        "error": "prompt cannot be null or undefined",
                    },
                    error_code=404,
                )
            if len(prompt) == 0:
                return QueryValidationResult(
                    is_ok=False,
                    error_data={"ok": False,
                                "error": "prompt length cannot be 0"},
                    error_code=404,
                )
        if comfy_pipeline:
            pipeline_data = comfy_pipeline.get("pipelineData")
            if not pipeline_data:
                return QueryValidationResult(
                    is_ok=False,
                    error_data={
                        "ok": False,
                        "error": "pipelineData cannot be null or undefined",
                    },
                    error_code=404,
                )
    return QueryValidationResult(is_ok=True)


@app.get("/v1/client/hello/", status_code=200)
@app.post("/v1/client/hello/", status_code=200)
async def hello():
    return {"ok": True, "url": "ws://genai.edenvr.link/ws"}


@app.post("/v1/inference/comfyPipeline", status_code=202)
async def add_comfy_task(request: Request, response: Response):
    data = await request.get_json()
    query_validation_res = check_data_and_state(data, True)
    if not query_validation_res.is_ok:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return query_validation_res.error_data

    task_id = str(uuid.uuid4())
    task = build_task_from_query(
        task_id,
        max_cost=data.get("max_cost", 15),
        time_to_money_ratio=data.get("time_to_money_ratio", 1),
        comfy_pipeline={
            "pipelineData": data.get("pipelineData"),
            "pipelineDependencies": data.get("pipelineDependencies"),
        },
    )

    token = data.get("token")
    storage_manager.add_task(users_storage.get_user_id(token), task_id, task)

    await dispatcher.add_task(task)

    return {"ok": True, "message": "Task submitted successfully", "task_id": task_id}


@app.get("/v1/nodes/health/", status_code=200)
async def health(response: Response):
    if len(registered_providers) != 0:
        return {"availableNodesCount": len(registered_providers), "status": "ok"}
    
    response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    return {"availableNodesCount": 0, "status": "error"}


@app.post("/v1/images/generation/", status_code=202)
async def generate_image(request: Request, response: Response):
    data = await request.json()
    query_validation_res = check_data_and_state(data, False)
    if not query_validation_res.is_ok:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return query_validation_res.error_data

    task_id = str(uuid.uuid4())
    task = build_task_from_query(
        task_id,
        max_cost=data.get("max_cost", 15),
        time_to_money_ratio=data.get("time_to_money_ratio", 1),
        standard_pipeline=data.get("standardPipeline"),
        comfy_pipeline=data.get("comfyPipeline"),
    )

    token = data.get("token")
    storage_manager.add_task(users_storage.get_user_id(token), task_id, task)

    await dispatcher.add_task(task)

    task_ready[task_id] = asyncio.Event()
    try:
        await asyncio.wait_for(task_ready[task_id].wait(), WS_TASK_TIMEOUT)
    except TimeoutError:
        response.status_code = status.HTTP_504_GATEWAY_TIMEOUT
        return {"error": "Timeout waiting for WebSocket response"}

    if connections[task_id]["status"] == "ready":
        return {"ok": True, "result": {"images": connections[task_id]}}
    else:
        return {"ok": False, "error": connections[task_id]["error"]}


@app.post("/v1/tasks/", status_code=201)
async def add_task(request: Request, response: Response):
    data = await request.json()
    query_validation_res = check_data_and_state(data, False)
    if not query_validation_res.is_ok:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return query_validation_res.error_data

    task_id = str(uuid.uuid4())
    task = build_task_from_query(
        task_id,
        max_cost=data.get("max_cost", 15),
        time_to_money_ratio=data.get("time_to_money_ratio", 1),
        standard_pipeline=data.get("standardPipeline"),
        comfy_pipeline=data.get("comfyPipeline"),
    )

    token = data.get("token")
    storage_manager.add_task(users_storage.get_user_id(token), task_id, task)

    await dispatcher.add_task(task)

    return {"ok": True, "message": "Task submitted successfully", "task_id": task_id}


@app.get("/v1/tasks/{task_id}", status_code=201)
async def get_task_info(task_id, request: Request, response: Response):
    token = request.headers.get("token")

    if ENFORCE_JWT_AUTH and not verify(token):
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"ok": False, "error": "operation is not permitted"}

    task_data = storage_manager.get_task_data_with_verification(
        users_storage.get_user_id(token), task_id
    )

    if not task_data:
        response.status_code = status.HTTP_403_FORBIDDEN
        return {"ok": False, "error": "No such task for this user"}

    return {
        "ok": True,
        "status": task_data["status"],
        "result": task_data.get("result"),
    }


@app.get("/v1/tasks/", status_code=200)
async def get_tasks(request: Request, response: Response):
    token = request.headers.get("token")

    if ENFORCE_JWT_AUTH and not verify(token):
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"ok": False, "error": "operation is not permitted"}

    tasks = storage_manager.get_tasks(users_storage.get_user_id(token))

    if not tasks:
        response.status_code = status.HTTP_403_FORBIDDEN
        return {"ok": False, "error": "No tasks for this user"}

    tasks_to_return = {
        task_id: {"status": task_data["status"],
                  "result": task_data.get("result")}
        for task_id, task_data in tasks.items()
    }
    return {"ok": True, "count": len(tasks), "data": tasks_to_return}


@app.websocket("/")
async def websocket_connection(ws: WebSocket):
    await ws.accept()
    while True:
        try:
            data = await ws.receive_text()
        except (WebSocketDisconnect, ConnectionClosed):
            if ws in registered_providers:
                id_ = registered_providers[ws]
                print(f"Node {id_} disconnected")
                registered_providers.pop(ws)
                provider = dispatcher.providers.get(id_)
                if provider:
                    await provider.on_connection_lost()
            break
        except Exception as e:
            logger.error(str(e))
            break

        if data == "close":
            if ws in registered_providers:
                id_ = registered_providers[ws]
                print(f"Node {id_} disconnected")
                registered_providers.pop(ws)
                provider = dispatcher.providers.get(id_)
                if provider:
                    await provider.on_connection_lost()
            break

        data_json = json.loads(data)
        msg_type = data_json.get("type")
        if msg_type == "register":
            node_id = data_json.get("node_id")
            try:
                metadata = data_json["metadata"]
                public_meta = PublicMetaInfo(
                    models=metadata.get("models", []),
                    gpu_type=metadata.get("gpu_type", ""),
                    ncpu=metadata.get("ncpu", 0),
                    ram=metadata.get("ram", 0)
                )
            except Exception as e:
                ws.close(
                    reason=1008, message="No metadata received on register")
                print(f"Skipping node without metadata info: {e}")
                break

            print(f"Node {node_id} connected")
            if node_id in dispatcher.providers:
                existing_provider = dispatcher.providers[node_id]
                existing_provider.update_public_meta_info(public_meta)
                existing_provider.restore_connection(ws=ws)
                print(f"Updated ws for {node_id}")
            else:
                private_meta = PrivateMetaInfo()
                network_connection = WSConnection(ws)
                provider = Provider(node_id, public_meta,
                                    private_meta, network_connection)
                dispatcher.add_provider(provider)

            previous_ws = find_key_by_value(registered_providers, node_id)
            if previous_ws is not None and previous_ws != ws:
                registered_providers.pop(previous_ws)
                logger.warn(
                    f"Disconnected provider connection found saved in registered")

            registered_providers[ws] = node_id

            print(f"Registered providers: {registered_providers.values()}")

        elif msg_type == "result" or msg_type == "error":
            try:
                jsonschema.validate(instance=data_json,
                                    schema=TASK_RESULT_SCHEMA)
            except Exception as e:
                logger.error(
                    f"Task result {data_json} was not recieved due to schema validation error: {e}")

            task_id = data_json.get("taskId")
            id_ = registered_providers.get(ws)
            if id_ is None:
                logger.warn(f"Not registered provider sent result: {ws}")
                break

            provider = dispatcher.providers.get(id_)
            if provider is not None:
                task_data = storage_manager.get_task_data(task_id)
                if task_data:
                    task = task_data.get("task")
                    if task:
                        if msg_type == "result":
                            provider.task_completed(task)
                            storage_manager.add_result(
                                task_id, data_json.get("resultsUrl"))
                        else:
                            provider.task_failed(task, data_json.get("error"))
                            # TODO: add to storage manager

            if task_id in task_ready:
                connections[task_id] = data_json
                task_ready[task_id].set()

        else:
            logger.warn(f"Unknown message type: {msg_type}")


if __name__ == "__main__":
    uvicorn.run("run:app", host="0.0.0.0", port=HTTP_WS_PORT, reload=True)

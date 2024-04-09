from constants.env import ENFORCE_JWT_AUTH, HTTP_WS_PORT, WS_TASK_TIMEOUT
from constants.static import TASK_RESULT_SCHEMA

from dispatcher.dispatcher import Dispatcher
from dispatcher.entry_queue import EntryQueue
from dispatcher.meta_info import PrivateMetaInfo, PublicMetaInfo
from dispatcher.provider import Provider
from dispatcher.task import build_task_from_query
from dispatcher.task_info import TaskResult
from dispatcher.util.logger import logger
from utils.query_check_result import QueryValidationResult

from storage import StorageManager, UsersStorage
from verification import verify
from ws_connection import WSConnection

from concurrent.futures import Future
from gevent import monkey
from gevent.pywsgi import WSGIServer
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sock import Sock

import json
import jsonschema
import uuid

monkey.patch_all()

app = Flask(__name__)
CORS(
    app,
    allow_headers="*",
    origins="*",
    methods="GET, POST, PATCH, PUT, DELETE, OPTIONS",
)
sock = Sock(app)

entry_queue = EntryQueue()
dispatcher = Dispatcher(entry_queue)
storage_manager = StorageManager()
users_storage = UsersStorage()

registered_providers = {}

connections = {}


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


@app.route("/v1/client/hello/", methods=["POST"])
def hello():
    return (jsonify({"ok": True, "url": "ws://genai.edenvr.link/ws"}), 200)


@app.route("/v1/inference/comfyPipeline", methods=["POST"])
def add_comfy_task():
    data = request.get_json()
    query_validation_res = check_data_and_state(data, True)
    if not query_validation_res.is_ok:
        return (
            jsonify(query_validation_res.error_data),
            query_validation_res.error_code,
        )

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

    entry_queue.add_task(task, 0)

    return (
        jsonify(
            {"ok": True, "message": "Task submitted successfully", "task_id": task_id}
        ),
        202,
    )


@app.route("/v1/nodes/health/", methods=["GET"])
def health():
    if registered_providers != {}:
        return (jsonify({"ok": True}), 200)
    return (jsonify({"ok": False}), 500)


@app.route("/v1/images/generation/", methods=["POST"])
def generate_image():
    data = request.get_json()
    query_validation_res = check_data_and_state(data, False)
    if not query_validation_res.is_ok:
        return (
            jsonify(query_validation_res.error_data),
            query_validation_res.error_code,
        )

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

    entry_queue.add_task(task, 0)

    future = Future()
    connections[task_id] = future

    try:
        response = connections[task_id].result(timeout=WS_TASK_TIMEOUT)
    except Exception as e:
        return (jsonify({"error": "Timeout waiting for WebSocket response"}), 504)

    del connections[task_id]

    return (jsonify({"ok": True, "result": {"images": response}}), 202)


@app.route("/v1/tasks/", methods=["POST"])
def add_task():
    data = request.get_json()
    query_validation_res = check_data_and_state(data, False)
    if not query_validation_res.is_ok:
        return (
            jsonify(query_validation_res.error_data),
            query_validation_res.error_code,
        )

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

    entry_queue.add_task(task, 0)

    return (
        jsonify(
            {"ok": True, "message": "Task submitted successfully", "task_id": task_id}
        ),
        201,
    )


@app.route("/v1/tasks/<task_id>", methods=["GET"])
def get_task_info(task_id):
    token = request.headers.get("token")

    if ENFORCE_JWT_AUTH and not verify(token):
        return (jsonify({"ok": False, "error": "operation is not permitted"}), 401)

    task_data = storage_manager.get_task_data_with_verification(
        users_storage.get_user_id(token), task_id
    )

    if not task_data:
        return (jsonify({"ok": False, "error": "No such task for this user"}), 403)

    return (
        jsonify(
            {
                "ok": True,
                "status": task_data["status"],
                "result": task_data.get("result"),
            }
        ),
        201,
    )


@app.route("/v1/tasks/", methods=["GET"])
def get_tasks():
    token = request.headers.get("token")

    if ENFORCE_JWT_AUTH and not verify(token):
        return (jsonify({"ok": False, "error": "operation is not permitted"}), 401)

    tasks = storage_manager.get_tasks(users_storage.get_user_id(token))

    if not tasks:
        return (jsonify({"ok": False, "error": "No tasks for this user"}), 403)

    tasks_to_return = {
        task_id: {"status": task_data["status"],
                  "result": task_data.get("result")}
        for task_id, task_data in tasks.items()
    }
    return (jsonify({"ok": True, "count": len(tasks), "data": tasks_to_return}), 200)


@sock.route("/")
def websocket_connection(ws):
    while True:
        data = ws.receive()
        if data == "close":
            if ws in registered_providers:
                id_ = registered_providers[ws]
                print(f"Node {id_} disconnected")
                provider = dispatcher.providers_map.get(id_)
                if provider:
                    provider.network_connection.on_connection_lost()
            break
        else:
            data_json = json.loads(data)
            msg_type = data_json.get("type")
            if msg_type == "register":
                node_id = data_json.get("node_id")
                metadata = data_json.get("metadata", dict())
                public_meta = PublicMetaInfo(
                    models=metadata.get("models", []),
                    gpu_type=metadata.get("gpu_type", ""),
                    ncpu=metadata.get("ncpu", 0),
                    ram=metadata.get("ram", 0),
                    min_cost=10,
                )
                print(f"Node {node_id} connected")
                if node_id in dispatcher.providers_map:
                    existing_provider = dispatcher.providers_map[node_id]
                    existing_provider.update_public_meta_info(public_meta)
                    existing_provider.network_connection.restore_connection(ws)

                    previous_ws = find_key_by_value(registered_providers, node_id)
                    registered_providers.pop(previous_ws)

                    registered_providers[ws] = node_id
                else:
                    private_meta = PrivateMetaInfo()
                    network_connection = WSConnection(ws)
                    provider = Provider(
                        node_id, public_meta, private_meta, network_connection
                    )
                    dispatcher.add_provider(provider)
                    registered_providers[ws] = node_id

                print(
                    f"Registered providers: {dispatcher.providers_map.keys()}")
            elif msg_type == "result":
                try:
                    jsonschema.validate(instance=data_json,
                                        schema=TASK_RESULT_SCHEMA)
                except Exception as e:
                    logger.error(
                        f"Task {data_json} was not recieved due to schema validation error: {e}"
                    )

                task_id = data_json.get("taskId")
                results_url = data_json.get("resultsUrl")
                id_ = registered_providers[ws]
                provider = dispatcher.providers_map.get(id_)

                if provider is not None:
                    task_data = storage_manager.get_task_data(task_id)
                    if task_data:
                        task = task_data.get("task")
                        if task:
                            task_result = TaskResult(results_url)
                            provider.network_connection.on_task_completed(
                                task, task_result
                            )
                            storage_manager.add_result(task_id, results_url)

                if task_id in connections:
                    connections[task_id].set_result(results_url)


if __name__ == "__main__":
    http_server = WSGIServer(("0.0.0.0", HTTP_WS_PORT), app)
    http_server.serve_forever()
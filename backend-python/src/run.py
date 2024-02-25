from constants.env import ENFORCE_JWT_AUTH, HTTP_WS_PORT
from dispatcher.dispatcher import Dispatcher
from dispatcher.entry_queue import EntryQueue
from dispatcher.meta_info import PrivateMetaInfo, PublicMetaInfo
from dispatcher.provider import Provider
from dispatcher.task import TaskStatus, build_task_from_query
from dispatcher.task_info import TaskResult

from storage import StorageManager
from verification import verify
from ws_connection import WSConnection

from concurrent.futures import Future
from gevent import monkey
from gevent.pywsgi import WSGIServer
from flask import Flask, request, jsonify
from flask_sock import Sock

from dispatcher.util.logger import logger

import json
import uuid

monkey.patch_all()

app = Flask(__name__)
sock = Sock(app)

entry_queue = EntryQueue()
dispatcher = Dispatcher(entry_queue)
storage_manager = StorageManager()

registered_providers = {}

connections = {}  # task_id to future, remove after migration to newer API


def check_data_and_state(data: dict, from_comfy_inf: bool = False) -> tuple: # TODO add error codes
    token = data.get('token')
    if ENFORCE_JWT_AUTH and not verify(token):
        return False, {'ok': False, 'error': 'operation is not permitted'}
    
    if len(registered_providers) == 0:
        return False, {'ok': False, 'error': 'no nodes available'}
    
    if from_comfy_inf:
        pipeline_data = data.get('pipelineData')
        if not pipeline_data:
            return False, {'ok': False, 'error': 'image pipeline is not specified'}
    else:
        comfy_pipeline = data.get('comfyPipeline')
        standard_pipeline = data.get('standardPipeline')
        if not standard_pipeline and not comfy_pipeline:
            return False, {'ok': False, 'error': 'image pipeline is not specified'}

        if standard_pipeline:
            prompt = standard_pipeline.get('prompt')
            if not prompt:
                return False, {'ok': False, 'error': 'prompt cannot be null or undefined'}
            if len(prompt) == 0:
                return False, {'ok': False, 'error': 'prompt length cannot be 0'}
        if comfy_pipeline:
            pipeline_data = comfy_pipeline.get('pipelineData')
            if not pipeline_data:
                return False, {'ok': False, 'error': 'pipelineData cannot be null or undefined'}
    return True, None


@app.route('/v1/client/hello/', methods=['POST'])
def hello():
    return jsonify({'ok': True, 'url': 'ws://genai.edenvr.link/ws'})


@app.route('/v1/inference/comfyPipeline', methods=['POST'])
def add_comfy_task():
    data = request.get_json()
    success, error_msg = check_data_and_state(data, True)
    if not success:
        return jsonify(error_msg)

    task_id = str(uuid.uuid4())
    task = build_task_from_query(task_id, max_cost=data.get('max_cost', 15), time_to_money_ratio=data.get('time_to_money_ratio', 1), comfy_pipeline={'pipelineData': data.get('pipelineData'), 'pipelineDependencies': data.get('pipelineDependencies')})

    token = data.get('token')
    storage_manager.add_task(token, task_id, task)

    def on_failed():
        task.set_status(TaskStatus.ABORTED)

    def on_completed(result: TaskResult):
        task.set_status(TaskStatus.COMPLETED)
        return jsonify({'ok': True, 'result': result})

    task.set_on_failed(on_failed)
    task.set_on_completed(on_completed)

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
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 500


@app.route("/v1/images/generation/", methods=["POST"])
def generate_image():
    data = request.get_json()
    success, error_msg = check_data_and_state(data)
    if not success:
        return jsonify(error_msg)

    task_id = str(uuid.uuid4())
    task = build_task_from_query(task_id, 
                                 max_cost=data.get('max_cost', 15), 
                                 time_to_money_ratio=data.get('time_to_money_ratio', 1), 
                                 standard_pipeline=data.get('standardPipeline'),
                                 comfy_pipeline=data.get('comfyPipeline'))

    token = data.get('token')
    storage_manager.add_task(token, task_id, task)

    def on_failed():
        task.set_status(TaskStatus.ABORTED)

    def on_completed(result: TaskResult):
        task.set_status(TaskStatus.COMPLETED)
        return jsonify({'ok': True, 'result': result})

    task.set_on_failed(on_failed)
    task.set_on_completed(on_completed)

    entry_queue.add_task(task, 0)

    future = Future()
    connections[task_id] = future

    try:
        response = connections[task_id].result(timeout=10)
    except Exception as e:
        return jsonify({"error": "Timeout waiting for WebSocket response"}), 504

    del connections[task_id]

    return jsonify({"ok": True, "result": {"images": response}})

@app.route("/v1/tasks/", methods=["POST"])
def add_task():
    data = request.get_json()
    success, error_msg = check_data_and_state(data)
    if not success:
        return jsonify(error_msg)

    task_id = str(uuid.uuid4())
    task = build_task_from_query(task_id, {
        'max_cost': data.get('max_cost', 15),
        'time_to_money_ratio': data.get('time_to_money_ratio', 1),
        'standard_pipeline': data.get('standardPipeline'),
        'comfy_pipeline': data.get('comfyPipeline'),
    })

    token = data.get('token')
    storage_manager.add_task(token, task_id, task)

    def on_failed():
        task.set_status(TaskStatus.ABORTED)

    def on_completed(result: TaskResult):
        task.set_status(TaskStatus.COMPLETED)
        return jsonify({'ok': True, 'result': result})

    task.set_on_failed(on_failed)
    task.set_on_completed(on_completed)

    entry_queue.add_task(task, 0)

    return (
        jsonify(
            {"ok": True, "message": "Task submitted successfully", "task_id": task_id}
        ),
        201,
    ) 

@app.route("/v1/tasks/{task_id}", methods=["GET"])
def get_task_info(task_id):
    data = request.get_json()
    token = data.get('token')
    if ENFORCE_JWT_AUTH and not verify(token):
        return jsonify({'ok': False, 'error': 'operation is not permitted'})

    task_data = storage_manager.get_task_data_with_verification(token, task_id)

    if not task_data:
        return jsonify({'ok': False, 'error': 'No such task for this user'})

    return jsonify({'ok': True, 'status': task_data['status'], 'result': task_data.get('result')})

@app.route("/v1/tasks/", methods=["GET"])
def get_tasks():
    data = request.get_json()
    token = data.get('token')
    if ENFORCE_JWT_AUTH and not verify(token):
        return jsonify({'ok': False, 'error': 'operation is not permitted'})

    tasks = storage_manager.get_tasks(token)

    if not tasks:
        return jsonify({'ok': False, 'error': 'No tasks for this user'})

    return jsonify({'ok': True, 'count': len(tasks), 'data': tasks})


@sock.route("/")
def websocket_connection(ws):
    while True:
        data = ws.receive()
        if data == "close":
            if ws in registered_providers:
                id_ = registered_providers[ws]
                provider = dispatcher.providers_map.get(id_)
                if provider:
                    provider.network_connection.on_connection_lost()
            break
        else:
            data_json = json.loads(data)
            msg_type = data_json.get("type")
            if msg_type == "register":
                node_id = data_json.get("node_id")
                public_meta = PublicMetaInfo(10)
                if node_id in dispatcher.providers_map:
                    existing_provider = dispatcher.providers_map[node_id]
                    existing_provider.update_public_meta_info(public_meta)
                    existing_provider.network_connection.on_connection_restored()
                else:
                    private_meta = PrivateMetaInfo()
                    network_connection = WSConnection(ws)
                    provider = Provider(
                        node_id, public_meta, private_meta, network_connection
                    )
                    dispatcher.add_provider(provider)
                    registered_providers[ws] = node_id
            elif msg_type == "result":
                task_id = data_json.get("taskId")
                results_url = data_json.get("resultsUrl")
                id_ = registered_providers[ws]
                provider = dispatcher.providers_map.get(id_)

                print(f'TASK_ID{task_id}')
                
                if provider:
                    task_data = storage_manager.get_task_data(task_id)
                    print(f'TASK_DATA {task_data}')
                    if task_data:
                        task = task_data.get('task')
                        print(f'TASK_DATA {task}')
                        if task:
                            task_result = TaskResult(results_url)
                            provider.network_connection.on_task_completed(task, task_result)
                            storage_manager.add_result(task_id, results_url)


                if task_id in connections:
                    connections[task_id].set_result(results_url)
                


if __name__ == "__main__":
    http_server = WSGIServer(("0.0.0.0", HTTP_WS_PORT), app)
    http_server.serve_forever()

from flask import Flask, request, jsonify
import uuid
from dispatcher.provider import Provider
from dispatcher.meta_info import PrivateMetaInfo, PublicMetaInfo
from dispatcher.entry_queue import EntryQueue
from dispatcher.dispatcher import Dispatcher
from dispatcher.task import Task, TaskStatus
from ws_connection import WSConnection
from dispatcher.task_info import TaskResult, TaskInfo, TaskOptions
import json
from gevent.pywsgi import WSGIServer
from verification import verify
from constants.env import ENFORCE_JWT_AUTH, HTTP_WS_PORT
from flask_sock import Sock
from gevent import monkey
from concurrent.futures import Future

monkey.patch_all()

app = Flask(__name__)
sock = Sock(app)

entryQueue = EntryQueue()
dispatcher = Dispatcher(entryQueue)

connections = {}
registered_providers = {}

tasks = {}

@app.route('/v1/client/hello/', methods=['POST'])
def hello():
    return jsonify({'ok': True, 'url': 'ws://genai.edenvr.link/ws'})

@app.route('/v1/nodes/health/', methods=['GET'])
def health():
    if registered_providers != {}:
        return jsonify({'ok': True})
    return jsonify({'ok': False}), 500

@app.route('/v1/images/generation/', methods=['POST'])
def generate_image():
    data = request.get_json()
    prompt = data.get('prompt')
    model = data.get('model')
    image_url = data.get('image_url')
    size = data.get('size')
    steps = data.get('steps')
    token = data.get('token')

    if ENFORCE_JWT_AUTH and not verify(token):
        return jsonify({'ok': False, 'error': 'operation is not permitted'})

    if not prompt:
        return jsonify({'ok': False, 'error': 'prompt cannot be null or undefined'})

    if len(prompt) == 0:
        return jsonify({'ok': False, 'error': 'prompt length cannot be 0'})

    task_id = uuid.uuid4()
    task = Task(TaskInfo(**{'id': str(task_id), 'max_cost': 15, 'time_to_money_ratio': 1, 'task_options': TaskOptions(**{'prompt': prompt, 'model': model, 'size': size, 'steps': steps})}))
    tasks[str(task_id)] = task

    def on_failed():
        task.set_status(TaskStatus.ABORTED)

    def on_completed(result: TaskResult):
        task.set_status(TaskStatus.COMPLETED)
        return jsonify({'ok': True, 'result': result})

    task.set_on_failed(on_failed)
    task.set_on_completed(on_completed)

    entryQueue.add_task(task, 0)

    future = Future()
    connections[str(task_id)] = future

    try:
        response = connections[str(task_id)].result(timeout=10)
    except Exception as e:
        return jsonify({'error': 'Timeout waiting for WebSocket response'}), 504

    del connections[str(task_id)]

    return jsonify({'ok': True, "result": {"image": response}})

@sock.route('/')
def websocket_connection(ws):

    while True:
        data = ws.receive()
        if data == 'close':
            if ws in registered_providers:
                id_ = registered_providers[ws]
                provider = dispatcher.providers_map.get(id_)
                if provider:
                    provider.network_connection.on_connection_lost()
            break
        else:
            data_json = json.loads(data)
            msg_type = data_json.get('type')
            if msg_type == 'register':
                node_id = data_json.get('node_id')
                public_meta = PublicMetaInfo(10)
                if node_id in dispatcher.providers_map:
                    existing_provider = dispatcher.providers_map[node_id]
                    existing_provider.update_public_meta_info(public_meta)
                    existing_provider.network_connection.on_connection_restored()
                else:
                    private_meta = PrivateMetaInfo()
                    network_connection = WSConnection(ws)
                    provider = Provider(node_id, public_meta, private_meta, network_connection)
                    dispatcher.add_provider(provider)
                    registered_providers[ws] = node_id
            elif msg_type == 'result':
                task_id = data_json.get('taskId')
                results_url = data_json.get('resultsUrl')[0]
                id_ = registered_providers[ws]
                provider = dispatcher.providers_map.get(id_)

                if provider:
                    task = tasks.get(task_id)
                    if task:
                        task_result = TaskResult(results_url)
                        provider.network_connection.on_task_completed(task, task_result)

                if task_id in connections:
                    connections[task_id].set_result(results_url)


if __name__ == '__main__':
    http_server = WSGIServer(('0.0.0.0', HTTP_WS_PORT), app)
    http_server.serve_forever()

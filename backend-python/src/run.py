from flask import Flask, request, jsonify
import uuid
from dispatcher.provider import Provider
from dispatcher.meta_info import PrivateMetaInfo, PublicMetaInfo
from dispatcher.entry_queue import EntryQueue
from dispatcher.dispatcher import Dispatcher
from dispatcher.task import Task, TaskStatus
from ws_connection import WSConnection
from dispatcher.task_info import TaskResult, TaskInfo, TaskOptions, ComfyPipelineOptions, StandardPipelineOptions
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

@app.route('/v1/inference/comfyPipeline', methods=['POST'])
def add_comfy_task():
    data = request.json
    token = data.get('token')
    pipeline_data = data.get('pipelineData')
    pipeline_images = data.get('pipelineImages')

    if ENFORCE_JWT_AUTH and not verify(token):
        return jsonify({'ok': False, 'error': 'operation is not permitted'})
    
    if not pipeline_data:
        return jsonify({'ok': False, 'error': 'image pipeline is not specified'}), 400

    if len(registered_providers) == 0:
        return jsonify({'ok': False, 'error': 'no nodes available'}), 503

    task_id = uuid.uuid4()
    task = Task(TaskInfo(**{
        'id': str(task_id),
        'max_cost': 15,
        'time_to_money_ratio': 1,
        'task_options': TaskOptions(**{
            'comfy_pipeline': ComfyPipelineOptions(**{
                'pipeline_data': pipeline_data,
                'pipeline_images': pipeline_images,
                })
            }
        )
    }))
    tasks[str(task_id)] = task

    def on_failed():
        # TODO: Reschedule if not rejected by dispatcher, or rejected by timeout...
        task.set_status(TaskStatus.Aborted)

    def on_completed(result):
        # TODO: Process result
        return jsonify({'ok': True, 'result': result})

    task.on_failed = on_failed
    task.on_completed = on_completed

    entryQueue.add_task(task, 0)  # Assuming similar method signature and functionality

    return jsonify({'ok': True, 'message': 'Task submitted successfully', 'task_id': task_id}), 202

@app.route('/v1/nodes/health/', methods=['GET'])
def health():
    if registered_providers != {}:
        return jsonify({'ok': True})
    return jsonify({'ok': False}), 500

@app.route('/v1/images/generation/', methods=['POST'])
def generate_image():
    data = request.get_json()
    comfy_pipeline = data.get('comfyPipeline')
    pipeline_data = None
    if comfy_pipeline:
        pipeline_data = comfy_pipeline.get('pipelineData')
        pipeline_images = comfy_pipeline.get('pipelineImages')

    standard_pipeline = data.get('standardPipeline')
    prompt, model, image_url, size, steps = None, None, None, None, None
    if standard_pipeline:
        prompt = standard_pipeline.get('prompt')
        model = standard_pipeline.get('model')
        image_url = standard_pipeline.get('image_url')
        size = standard_pipeline.get('size')
        steps = standard_pipeline.get('steps')

    token = data.get('token')

    if ENFORCE_JWT_AUTH and not verify(token):
        return jsonify({'ok': False, 'error': 'operation is not permitted'})

    if not standard_pipeline and not comfy_pipeline:
        return jsonify({'ok': False, 'error': 'image pipeline is not specified'})
    
    if standard_pipeline and not comfy_pipeline:
        if not prompt:
            return jsonify({'ok': False, 'error': 'prompt cannot be null or undefined'})
        if len(prompt) == 0:
            return jsonify({'ok': False, 'error': 'prompt length cannot be 0'})
    
    if comfy_pipeline:
        if not pipeline_data:
            return jsonify({'ok': False, 'error': 'pipelineData cannot be null or undefined'})

    if not registered_providers:
        return jsonify({'ok': False, 'error': 'no nodes available'})

    task_id = uuid.uuid4()
    task = Task(
        TaskInfo(**{
            'id': str(task_id),
            'max_cost': 15,
            'time_to_money_ratio': 1,
            'task_options': TaskOptions(**{
                'standard_pipeline': StandardPipelineOptions(**{
                    'prompt': prompt,
                    'model': model,
                    'size': size,
                    'steps': steps
                }) if standard_pipeline else None,
                'comfy_pipeline': ComfyPipelineOptions(**{
                    'pipeline_data': pipeline_data,
                    'pipeline_images': pipeline_images,
                }) if comfy_pipeline else None
            })
        })
    )
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

    return jsonify({'ok': True, "result": {"images": response}})

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
                results_url = data_json.get('resultsUrl')
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

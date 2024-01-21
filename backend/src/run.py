import os
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import asyncio
import uuid
from dispatcher.provider import Provider
from dispatcher.protocol.meta import PrivateMetaInfo, PublicMetaInfoV1
from dispatcher.entry_queue import EntryQueue
from dispatcher.dispatcher import Dispatcher
from dispatcher.task import Task, TaskStatus
from ws_connection import WSConnection
from dispatcher.protocol.task import TaskResult
from typing import Dict
from flask_socketio import SocketIO, send, emit
import json
from gevent.pywsgi import WSGIServer
from verification import verify
from constants import ENFORCE_JWT_AUTH, HTTP_WS_PORT

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

entryQueue = EntryQueue()
dispatcher = Dispatcher(entryQueue)

connections = []
registeredProviders = {}

tasks = {}

@app.route('/v1/client/hello/', methods=['POST'])
def hello():
    return jsonify({'ok': True, 'url': 'ws://genai.edenvr.link/ws'})

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
    task = Task({'_v': 1, 'id': str(task_id), 'max_price': 15, 'time_to_money_ratio': 1, 'task_options': {'prompt': prompt, 'model': model, 'size': size, 'steps': steps}})
    tasks[task_id] = task

    def onFailed():
        task.setStatus(TaskStatus.Aborted)

    def onCompleted(result: TaskResult):
        return jsonify({'ok': True, 'result': result})

    task.onFailed = onFailed
    task.onCompleted = onCompleted
    entryQueue.addTask(task, 0)
    return jsonify({'ok': True})

@socketio.on('connect')
def handle_connect():
    print('Node connected')

@socketio.on('disconnect')
def handle_disconnect():
    global registeredProviders
    ws = request.sid
    if ws in registeredProviders:
        id = registeredProviders[ws]
        provider = dispatcher.providersMap.get(id)
        if provider:
            provider.network_connection.onLostConnection()

@socketio.on('message')
def handle_message(message):
    data = json.loads(message)
    type = data.get('type')

    if type == 'register':
        node_id = data.get('node_id')
        public_meta = PublicMetaInfoV1({'_v': 1, 'min_cost': 10})
        if node_id in dispatcher.providersMap:
            existingProvider = dispatcher.providersMap[node_id]
            existingProvider.updatePublicMeta(public_meta)
            existingProvider.network_connection.onConnectionRestored()
        else:
            private_meta = PrivateMetaInfo({'_v': 1})
            network_connection = WSConnection(request.sid)
            provider = Provider(node_id, public_meta, private_meta, network_connection)
            print('Provider created', node_id )
            dispatcher.addProvider(provider)
            registeredProviders[request.sid] = node_id

    elif type == 'result':
        taskId = data.get('taskId')
        resultsUrl = data.get('resultsUrl')[0]
        ws = registeredProviders[request.sid]
        provider = dispatcher.providersMap.get(ws)
        if provider:
            task = tasks.get(taskId)
            if task:
                taskResult = TaskResult({'image': resultsUrl, '_v': 1})
                provider.network_connection.onTaskCompleted(task, taskResult)

    elif type == 'status':
        status = data.get('status')

if __name__ == '__main__':
    print('pupupu')
    server = WSGIServer(('localhost', HTTP_WS_PORT), app)
    server.serve_forever()
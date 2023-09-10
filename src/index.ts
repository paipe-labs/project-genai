import 'dotenv/config';

import express from 'express';
import bodyParser from 'body-parser';
import { WebSocket, WebSocketServer } from 'ws';
import cors from 'cors';
import { HTTP_PORT, WS_PORT } from 'constants/env';
import { verify } from 'verification';
import { Provider } from 'dispatcher/provider';
import { PrivateMetaInfo } from 'dispatcher/protocol/meta';
import { EntryQueue } from 'dispatcher/entry-queue';
import { Dispatcher } from 'dispatcher/dispatcher';
import { Task, TaskStatus } from 'dispatcher/task';
import { WSConenction } from 'ws-connection';
import { TaskResult } from 'dispatcher/protocol/task';

// Entry example
const entryQueue = new EntryQueue();
const dispatcher = new Dispatcher(entryQueue);

const connections: WebSocket[] = [];
const app = express();
app.options('*', cors());
app.use(cors());

app.use(bodyParser.urlencoded({ extended: false }));
app.use(bodyParser.json());

const wss = new WebSocketServer({ port: WS_PORT });

const registeredProviders = new WeakMap<WebSocket, string>();

const tasks = new Map<string, Task>();

wss.on('connection', (ws: WebSocket) => {
  console.log('Node connected');
  connections.push(ws);
  ws.on('close', () => {
    const index = connections.indexOf(ws);
    if (index !== -1) {
      connections.splice(index, 1);
    }

    if (registeredProviders.has(ws)) {
      const id = registeredProviders.get(ws)!;
      const provider = dispatcher.providersMap.get(id);
      if (provider) provider.network_connection.onLostConnection();
    }
  });

  ws.on('message', async (message: string) => {
    const data = JSON.parse(message);
    const { type, request_id } = data;

    switch (type) {
      case 'register': {
        const { id, public_meta } = data;

        if (dispatcher.providersMap.has(id)) {
          const existingProvider = dispatcher.providersMap.get(id)!;
          existingProvider.updatePublicMeta(public_meta);
          existingProvider.network_connection.onConnectionRestored();
        }
        // TODO: public_meta verification
        // TODO: private_meta from db
        const private_meta: PrivateMetaInfo = { _v: 1 };
        const network_connection = new WSConenction(ws);
        const provider = new Provider(
          id,
          public_meta,
          private_meta,
          network_connection
        );
        dispatcher.addProvider(provider);

        registeredProviders.set(ws, id);
        break;
      }

      case 'result': {
        const {task_id, result} = data;

        const provider = dispatcher.providersMap.get(registeredProviders.get(ws)!);
        if (provider) {
          const task = tasks.get(task_id);
          if (task) {
            provider.network_connection.onTaskCompleted(task, result);
          }
        } else {
          // TODO: restore connection
        }
        break;
      }
    }

    // TODO: Remove
    if (type === 'status') {
      const { status } = data;
      if (status === 'ready') {
        // can process request_id
      }
      if (status === 'busy') {
        // cannot process request_id
      }
    }
    if (type === 'result') {
      const { result_url } = data;
      // result for { request_id };
    }
    if (type === 'error') {
      // failure for { request_id }
    }
    if (type === 'greetings') {
      console.log(data.node_id);
    }
  });
});

app.post('/v1/client/hello', async (req, res) => {
  return res.json({ ok: true, url: 'ws://genai.edenvr.link/ws' });
});

app.post('/v1/images/generation/', async (req, res) => {
  const { prompt, model, image_url, size, token, task_id } = req.body;

  if (!verify(token)) {
    return res.json({ ok: false, error: 'operation is not permitted' });
  }

  if (!prompt) {
    return res.json({ ok: false, error: 'prompt cannot be null or undefined' });
  }
  if (prompt.length === 0) {
    return res.json({ ok: false, error: 'prompt length cannot be 0' });
  }

  // TODO:
  const task = new Task();
  tasks.set(task_id, task);

  task.onFailed = () => {
    // TODO: Reschedule if not rejected by dispatcher, or rejected by timeout...

    task.setStatus(TaskStatus.Aborted);
  }
  task.onCompleted = (result: TaskResult) => {
    // TODO: Process result
  }

  entryQueue.addTask(task, Date.now());
});

// Start the server
const server = app.listen(HTTP_PORT, () => {
  console.log(`HTTP started on port ${HTTP_PORT}`);
  console.log(`WS started on port ${WS_PORT}`);
});

// Handle errors that occur during the startup process
server.on('error', error => {
  console.error(error);
});

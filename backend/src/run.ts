import 'dotenv/config';

import express from 'express';
import bodyParser from 'body-parser';
import { WebSocket } from 'ws';
import { createServer } from 'http';
import cors from 'cors';
import { ENFORCE_JWT_AUTH, HTTP_WS_PORT } from 'constants/env';
import { verify } from 'verification';
import { Provider } from 'dispatcher/provider';
import { PrivateMetaInfo, PublicMetaInfoV1 } from 'dispatcher/protocol/meta';
import { EntryQueue } from 'dispatcher/entry-queue';
import { Dispatcher } from 'dispatcher/dispatcher';
import { Task, TaskStatus } from 'dispatcher/task';
import { WSConenction } from 'ws-connection';
import { TaskResult, TaskResultClient } from 'dispatcher/protocol/task';
import { v4 as uuid } from 'uuid';

import process from 'process';

// Entry example
const entryQueue = new EntryQueue();
const dispatcher = new Dispatcher(entryQueue);

const connections: WebSocket[] = [];
const app = express();
app.options('*', cors());
app.use(cors());

app.use(bodyParser.urlencoded({ extended: false }));
app.use(bodyParser.json());

const server = createServer(app);

const wss = new WebSocket.Server({ server });

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
    const { type } = data;

    switch (type) {
      case 'register': {
        const { node_id } = data;
        const public_meta: PublicMetaInfoV1 = {
          _v: 1,
          min_cost: 10,
        };

        if (dispatcher.providersMap.has(node_id)) {
          const existingProvider = dispatcher.providersMap.get(node_id)!;
          existingProvider.updatePublicMeta(public_meta);
          existingProvider.network_connection.onConnectionRestored();
        }
        // TODO: public_meta verification
        // TODO: private_meta from db
        const private_meta: PrivateMetaInfo = { _v: 1 };
        const network_connection = new WSConenction(ws);
        const provider = new Provider(
          node_id,
          public_meta,
          private_meta,
          network_connection
        );
        console.log('Provider created', node_id )
        dispatcher.addProvider(provider);

        registeredProviders.set(ws, node_id);
        break;
      }

      case 'result': {
        const { taskId, resultsUrl} = data as TaskResultClient;

        const provider = dispatcher.providersMap.get(registeredProviders.get(ws)!);
        if (provider) {
          const task = tasks.get(taskId);
          if (task) {
            const taskResult: TaskResult = {
              image: resultsUrl[0],
              _v: 1,
            };
            provider.network_connection.onTaskCompleted(task, taskResult);
          }
        } else {
          // TODO: restore connection
        }
        break;
      }
      case 'status': {
        const { status } = data;

      }
    }
  });
});

app.post('/v1/client/hello/', async (req, res) => {
  return res.json({ ok: true, url: 'ws://genai.edenvr.link/ws' });
});

app.post('/v1/images/generation/', async (req, res) => {
  const { prompt, model, image_url, size, steps, token } = req.body;

  if (ENFORCE_JWT_AUTH && !verify(token)) {
    return res.json({ ok: false, error: 'operation is not permitted' });
  }

  if (!prompt) {
    return res.json({ ok: false, error: 'prompt cannot be null or undefined' });
  }
  if (prompt.length === 0) {
    return res.json({ ok: false, error: 'prompt length cannot be 0' });
  }
  // TODO:
  const task_id = uuid();
  const task = new Task({_v: 1, id: task_id, max_price: 15, time_to_money_ratio: 1, task_options: { prompt, model, size, steps}});
  tasks.set(task_id, task);

  task.onFailed = () => {
    // TODO: Reschedule if not rejected by dispatcher, or rejected by timeout...

    task.setStatus(TaskStatus.Aborted);
  }
  task.onCompleted = (result: TaskResult) => {
    // TODO: Process result

    res.json({ ok: true, result: result });
  }

  entryQueue.addTask(task, 0);
});

// Start the server
server.listen(HTTP_WS_PORT, () => {
  console.log(`HTTP and WS started on port ${HTTP_WS_PORT}`);
});

// Handle errors that occur during the startup process
server.on('error', error => {
  console.error(error);
});

process.on('SIGINT', () => {
  server.close(() => {
    console.log('Server is gracefully shutting down');
    process.exit(0);
  });
});

process.on('SIGTERM', () => {
  server.close(() => {
    console.log('Server is gracefully shutting down');
    process.exit(0);
  });
});

import { NetworkConnection } from 'dispatcher/network-connection';
import { Task } from 'dispatcher/task';
import { WebSocket } from 'ws';

export class WSConenction extends NetworkConnection {
  constructor(private ws: WebSocket) {super();}

  restoreConnection(ws: WebSocket) {
    this.ws = ws;
    this.onConnectionRestored();
  }

  sendTask(task: Task): Promise<void> {
    this.ws.send(JSON.stringify({
      type: 'task',
      task_id: task.id,
      task_info: task.task_info,
    }));
    return Promise.resolve();
  }

  abortTask(task: Task): Promise<void> {
    this.ws.send(JSON.stringify({
      type: 'abort',
      task_id: task.id,
    }));
    return Promise.resolve();
  }
}

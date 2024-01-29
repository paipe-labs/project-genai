import { NetworkConnection } from 'dispatcher/network-connection';
import { TaskOptions } from 'dispatcher/protocol/task';
import { Task } from 'dispatcher/task';
import { WebSocket } from 'ws';

export class WSConenction extends NetworkConnection {
  constructor(private ws: WebSocket) {
    super();
  }

  restoreConnection(ws: WebSocket) {
    this.ws = ws;
    this.onConnectionRestored();
  }

  sendTask(task: Task): Promise<void> {
    const taskOptions = task.getTaskOptions();

    const clientTask: ClientTask = {
      options: taskOptions?.standardPipeline,
      comfyOptions: taskOptions?.comfyPipeline,
      taskId: task.id,
    }

    this.ws.send(JSON.stringify(clientTask));
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

export type ClientTask = {
  options?: TaskOptions['standardPipeline'],
  comfyOptions?: TaskOptions['comfyPipeline'],
  taskId: string,
};
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
    const clientTask: ClientTask = {
      options: task.getTaskOptions(),
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

// export const TaskZod = z.object({
//   options: z.object({
//       prompt: z.string(),
//       model: z.string(),
//       size: z.string().optional(),
//       steps: z.number().optional(),
//   }),
//   taskId: z.string(),
// });

//Typescript type from comment above
export type ClientTask = {
  options?: TaskOptions,
  taskId: string,
};
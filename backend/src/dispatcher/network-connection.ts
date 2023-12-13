import { PublicMetaInfo } from "./protocol/meta";
import { TaskResult } from "./protocol/task";
import { Task, TaskStatus } from "./task";
import { NOOP } from "./utils/noop";


// TODO: Refactor to interface
export class NetworkConnection {
  async sendTask(task: Task): Promise<void> {
    // do await
    task.setStatus(TaskStatus.SentToProvider);
  }

  async abortTask(task: Task): Promise<void> {
    task.setStatus(TaskStatus.Aborted);
    // do await
  }

  async close(): Promise<void> {
    // drop websocket connection
  }

  onMetaUpdated: (meta: PublicMetaInfo) => void = NOOP;

  onLostConnection: () => void = NOOP;

  onConnectionRestored: () => void = NOOP;

  onTaskCompleted: (task: Task, result: TaskResult) => void = NOOP;

  onTaskFailed: (task: Task, reason: string) => void = NOOP;

  // TODO:
  // onTaskTimeout: (task: Task) => void = NOOP;

  // TODO: onTaskRejected, onTaskAccepted, onProgressUpdate
}
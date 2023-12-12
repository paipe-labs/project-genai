import { NetworkConnection } from "./network-connection";
import { PrivateMetaInfo, PublicMetaInfo } from "./protocol/meta";
import { TaskResult } from "./protocol/task";
import { ProviderEstimator } from "./provider-estimator";
import { Task, TaskStatus } from "./task";
import { logger } from "./utils/logger";
import { NOOP } from "./utils/noop";

export const RETRY_ATTEMPTS = 3;
export const OFFLINE_TIMEOUT = 3000; // 3 seconds

export class Provider {
  public readonly estimator: ProviderEstimator;

  private online = true;

  private offlineTimeout: NodeJS.Timeout | undefined = undefined;

  private inProgress = new Set<Task>();

  constructor(
    public readonly id: string,
    private public_meta: PublicMetaInfo,
    private private_meta: PrivateMetaInfo,
    public readonly network_connection: NetworkConnection
  ) {
    this.estimator = new ProviderEstimator(public_meta, private_meta);

    network_connection.onMetaUpdated = (meta) => {
      this.updatePublicMeta(meta);
    };

    network_connection.onLostConnection = () => {
      this.startOffline();
    };

    network_connection.onConnectionRestored = () => {
      this.stopOffline();
    };

    network_connection.onTaskCompleted = (task, result) => {
      this.taskCompleted(task, result);
      this.onUpdated();
    };

    network_connection.onTaskFailed = (task, reason) => {
      this.taskFailed(task);
      this.onUpdated();
    };
  }

  private startOffline(): void {
    if (this.offlineTimeout) return;
    this.offlineTimeout = setTimeout(() => {
      this.dispose();
      this.onClosed();
    }, 1000);
    this.online = false;
    this.onUpdated();
  }

  private dispose(): void {
    this.network_connection.close();
    for (const task of this.inProgress) {
      task.setStatus(TaskStatus.FailedByProvider, { reason: "Provider is offline" });
      task.fail();
    }
    this.onClosed();
  }

  private stopOffline(): void {
    if (!this.offlineTimeout) return;
    clearTimeout(this.offlineTimeout);
    this.offlineTimeout = undefined;
    this.online = true;
    this.onUpdated();
  }

  updatePublicMeta(public_meta: PublicMetaInfo) {
    this.public_meta = public_meta;
    this.estimator.updatePublicMeta(public_meta);
    this.onUpdated();
  }

  updatePrivateMeta(private_meta: PrivateMetaInfo) {
    this.private_meta = private_meta;
    this.estimator.updatePrivateMeta(private_meta);
    this.onUpdated();
  }

  getQueueLength(): number {
    return this.inProgress.size;
  }

  scheduleTask(task: Task): void {
    task.setProviderId(this.id);
    console.log(`Task ${task.id} scheduled in provider ${this.id}`);
    this.estimator.addTask(task);
    this.asyncScheduleTask(task);
  }

  // TODO: Optimization batch sending
  private async asyncScheduleTask(task: Task): Promise<void> {
    for (let i = 0; i < RETRY_ATTEMPTS; i++) {
      try {
        await this.network_connection.sendTask(task);
        this.inProgress.add(task);
        return;
      } catch {
        task.setStatus(TaskStatus.SentFailed, { attempt: i });
      }
    }
    this.taskFailed(task, "Failed to send task");
  }

  abortTask(task: Task): void {
    this.taskFinished(task);

    (async () => {
      try {
        await this.network_connection.abortTask(task);
      } catch (e) {
        logger.error(e);
      }
    })();
  }

  taskFinished(task: Task): void {
    this.estimator.removeTask(task);
    this.inProgress.delete(task);
  }

  taskFailed(task: Task, reason?: string): void {
    if (!this.inProgress.has(task)) return;
    this.taskFinished(task);
    task.addFailedAttempt();
    task.setStatus(TaskStatus.FailedByProvider, { reason });
    task.fail();
  }

  taskCompleted(task: Task, result: TaskResult): void {
    if (!this.inProgress.has(task)) return;
    this.taskFinished(task);
    task.setStatus(TaskStatus.Completed);
    task.complete(result);
  }

  getMinCost(): number {
    if (!this.online) return Number.MAX_SAFE_INTEGER;
    return this.public_meta.min_cost;
  }

  onClosed: () => void = NOOP;

  onUpdated: () => void = NOOP;
}

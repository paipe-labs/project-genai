import { TaskInfo, TaskResult } from "./protocol/task";
import { NOOP } from "./utils/noop";

export enum TaskStatus {
  Initial,
  PushedIntoQueue,
  PulledByDispatcher,
  RejectedByDispatcher,
  SetToProvider,
  SentFailed,
  SentToProvider,
  FailedByProvider,
  Aborted,
  Completed,
  Timeout,
}

export type TaskStatusPayload = {
  [TaskStatus.SetToProvider]: [{ providerId: string }];
  [TaskStatus.SentFailed]: [{ attempt: number }];
  [TaskStatus.FailedByProvider]: [{ reason?: string }];
} & {
  [taskStatus: number | string | symbol]: [];
};

export class Task {
  private failedAttempts = 0;

  private priority = 0;

  private providerId: string | undefined = undefined;

  readonly status: TaskStatus = TaskStatus.Initial;

  private log: string[] = [];

  constructor(readonly task_info: TaskInfo) {}

  get id(): string {
    return this.task_info.id;
  }

  getMaxPrice(): number {
    return this.task_info.max_price;
  }

  /** Returns time to money ratio */
  getMoneyTimeRatio(): number {
    return this.task_info.time_to_money_ratio;
  }

  addFailedAttempt(): void {
    this.failedAttempts++;
  }

  getFailedAttempts(): number {
    return this.failedAttempts;
  }

  // Priority queue related methods

  setPriority(priority: number): void {
    this.priority = priority;
  }

  getPriority(): number {
    return this.priority;
  }

  // Profiling related methods

  setStatus<T extends TaskStatus>(
    event: T,
    ...payload: TaskStatusPayload[T]
  ): void {
    // TODO:
    // We can add any profiling logic here, to analyze life cycle of a task

    this.log.push(`[${new Date().toISOString()}] ${event}: ${payload.join(", ")}`);
  }

  getLog(): string[] {
    return this.log;
  }

  setProviderId(providerId: string): void {
    this.providerId = providerId;
  }

  getProviderId(): string | undefined {
    return this.providerId;
  }

  complete(result: TaskResult): void {
    this.onCompleted(result);
  }

  fail(): void {
    this.onFailed();
  }

  onCompleted: (result: TaskResult) => void = NOOP;
  onFailed: () => void = NOOP;
}

import { PrivateMetaInfo, PublicMetaInfo } from "./protocol/meta";
import { Task } from "./task";
import { warnIf } from "./utils/runtime";

export class ProviderEstimator {
  private estimatedTime = new Map<Task, number>();
  private totalEstimatedTime = 0;

  constructor(
    private public_meta: PublicMetaInfo,
    private private_meta: PrivateMetaInfo)
  {}

  updatePublicMeta(public_meta: PublicMetaInfo): void {
    this.public_meta = public_meta;
  }

  updatePrivateMeta(private_meta: PrivateMetaInfo) {
    this.private_meta = private_meta;
  }

  addTask(task: Task): void {
    const estimatedTime = this.estimateTaskWaitingTime(task);
    this.estimatedTime.set(task, estimatedTime);
    this.totalEstimatedTime += estimatedTime;
  }

  removeTask(task: Task): void {
    if (warnIf(!this.estimatedTime.has(task), `Task ${task.id} is not in the estimator queue`)) return;
    const estimatedTime = this.estimatedTime.get(task)!;
    this.estimatedTime.delete(task);
    this.totalEstimatedTime -= estimatedTime;
  }

  /** Returns time when a new task can be started */
  getWaitingTime(): number {
    return this.totalEstimatedTime;
  }

  /** Returns estimated time for the specific task */
  estimateTaskWaitingTime(task: Task): number {
    // TODO: Do business logic here, estimate time based on the task and provider meta
    return 4; // milliseconds
  }
}
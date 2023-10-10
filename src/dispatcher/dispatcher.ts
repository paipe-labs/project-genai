import { warnIf } from './utils/runtime';
import { Provider } from './provider';
import { Task, TaskStatus } from './task';
import { EntryQueue } from './entry-queue';

const DISABLE_DISPATCHER_QUEUE_THRESHOLD = 50;
const TASK_MAX_ATTEMPTS = 5;

const isBusyProvider = (provider: Provider): boolean =>
  provider.getQueueLength() > DISABLE_DISPATCHER_QUEUE_THRESHOLD;

export class Dispatcher {
  private providers = new Set<Provider>();

  readonly providersMap = new Map<string, Provider>();

  private minCost: number = Number.MAX_SAFE_INTEGER;

  constructor(private entryQueue: EntryQueue) {
    this.entryQueue.taskAdded = this.taskAddedCb.bind(this);
  }

  addProvider(provider: Provider): void {
    if (
      warnIf(
        this.providers.has(provider),
        `Provider with id ${provider.id} already added`
      )
    )
      return;
    this.providersMap.set(provider.id, provider);
    this.providers.add(provider);
    this.calcMinCost();
    provider.onClosed = () => {
      this.removeProvider(provider);
      this.calcMinCost();
    };
    provider.onUpdated = () => {
      this.calcMinCost();
    };
  }

  removeProvider(provider: Provider): void {
    if (
      warnIf(
        !this.providers.has(provider),
        `Provider with id ${provider.id} wasn't added`
      )
    )
      return;
    this.providersMap.delete(provider.id);
    this.providers.delete(provider);
    this.calcMinCost();
  }

  minCostUpdated(_provider: Provider): void {
    this.calcMinCost();
  }

  private calcMinCost(): void {
    this.minCost = Number.MAX_SAFE_INTEGER;
    for (const provider of this.providers.values()) {
      if (isBusyProvider(provider)) continue;
      warnIf(
        provider.getMinCost() > Number.MAX_SAFE_INTEGER,
        `Min cost in provider ${provider.id} is larger than limit`
      );
      this.minCost = Math.min(this.minCost, provider.getMinCost());
    }
  }

  getMinCost(): number {
    return this.minCost;
  }

  scheduleTask(task: Task): boolean {
    // NOTE: This loop can be optimized from O(N) to O(log N) if we assume that task estimation depends on provider only, and not on the task
    // Then we can store providers in Li-Chao tree as lines Kx + B, when K is waiting time and B is minimum cost, x is time to money coefficient
    let bestProvider: Provider | undefined = undefined;
    let lowestScore: number = Number.MAX_VALUE;
    let lowestWaitingTime: number = Number.MAX_VALUE;
    for (const provider of this.providers.values()) {
      // TODO: Can optimize to not iterate over busy providers
      if (isBusyProvider(provider)) continue;

      // We assume cost doesn't depend on a task (we can tune it later)
      const cost = provider.getMinCost();

      // TODO: We can iterate over filtered values only
      if (cost > task.getMaxPrice()) continue;

      const waitingTime =
        provider.estimator.getWaitingTime() +
        provider.estimator.estimateTaskWaitingTime(task);

      const score = cost + waitingTime * task.getMoneyTimeRatio();

      if (score < lowestScore) {
        lowestScore = score;
        lowestWaitingTime = waitingTime;
        bestProvider = provider;
      }
    }

    if (bestProvider) {
      task.setStatus(TaskStatus.SetToProvider, {
        providerId: bestProvider.id,
        minScore: lowestScore,
        waitingTime: lowestWaitingTime
      });
      bestProvider.scheduleTask(task);
      this.calcMinCost();
      return true;
    }
    return false;
  }

  pullTask(): void {
    // TODO: Add call logic
    const task = this.entryQueue.popTask(this.getMinCost());
    if (!task) return;

    task.setStatus(TaskStatus.PulledByDispatcher);

    const scheduled = this.scheduleTask(task);
    if (warnIf(!scheduled, `Task ${task.id} wasn't scheduled`)) {
      task.addFailedAttempt();
      if (task.getFailedAttempts() < TASK_MAX_ATTEMPTS)
        this.entryQueue.addTask(task, task.getPriority());
      else {
        task.setStatus(TaskStatus.RejectedByDispatcher);
        task.fail();
      }
    }
  }

  taskAddedCb(task: Task): void {
    if (task.getMaxPrice() < this.getMinCost()) {
      task.setStatus(TaskStatus.RejectedByDispatcher);
      return;
    }
    this.pullTask();
  }
}

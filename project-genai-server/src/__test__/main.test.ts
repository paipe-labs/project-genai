import { describe, expect, test } from '@jest/globals';
import { Dispatcher } from 'dispatcher/dispatcher';
import { EntryQueue } from 'dispatcher/entry-queue';
import { NetworkConnection } from 'dispatcher/network-connection';
import { PrivateMetaInfo, PublicMetaInfo } from 'dispatcher/protocol/meta';
import { TaskInfo, TaskResult, TaskResultV1 } from 'dispatcher/protocol/task';
import { Provider } from 'dispatcher/provider';
import { Task, TaskStatus } from 'dispatcher/task';
import { delay } from 'utils/delay';
import { v4 as uuid } from 'uuid';

class MockExecutor extends NetworkConnection {
  queue = new Set<Task>();

  async sendTask(task: Task): Promise<void> {
    await super.sendTask(task);
    this.queue.add(task);
    this.processTask(task);
  }

  async abortTask(task: Task): Promise<void> {
    await super.abortTask(task);
    this.queue.delete(task);
  }

  asyncQueue = Promise.resolve();
  private processTask(task: Task, failedReason?: string): void {
    this.asyncQueue = this.asyncQueue.then(async () => {
      await delay(10);
      if (this.queue.has(task)) {
        if (failedReason === undefined) {
          const result: TaskResultV1 = { _v: 1, image: 'image' };
          this.onTaskCompleted(task, result);
        } else {
          this.onTaskFailed(task, failedReason);
        }
      }
    });
  }

  loseConnection(): void {
    this.onLostConnection();
  }

  restoreConnection(): void {
    this.restoreConnection();
  }
}

describe('Full pipeline test', () => {
  const entryQueue = new EntryQueue();
  const dispatcher = new Dispatcher(entryQueue);

  const createProvider = (min_cost: number): Provider => {
    const private_meta: PrivateMetaInfo = { _v: 1 };
    const public_meta: PublicMetaInfo = { _v: 1, min_cost };
    const id = uuid();
    return new Provider(id, public_meta, private_meta, new MockExecutor());
  };

  const createTask = (max_price: number, time_to_money_ratio: number) => {
    const id = uuid();
    const task_info: TaskInfo = { _v: 1, max_price, time_to_money_ratio, id };
    return new Task(task_info);
  };

  const provider1 = createProvider(10);
  const provider2 = createProvider(20);
  dispatcher.addProvider(provider1);
  dispatcher.addProvider(provider2);

  const task1 = createTask(15, 1);
  const task2 = createTask(30, 15);

  test('Task 1', done => {
    task1.onCompleted = (result: TaskResult) => {
      done();
    };
  }, 1000);

  test('Task 2', done => {
    task2.onCompleted = (result: TaskResult) => {
      done();
    };
  }, 1000);

  entryQueue.addTask(task1, 0);
  entryQueue.addTask(task2, 0);

  test('Empty queue', async () => {
    await new Promise(process.nextTick);
    console.log(task1.getLogString());
    console.log(task2.getLogString());

    expect(entryQueue['queue'].size()).toBe(0);
    expect(task1.getLog().at(-1)![1]).toBe(TaskStatus.Completed);
    expect(task2.getLog().at(-1)![1]).toBe(TaskStatus.Completed);

    expect(task1.getLog().at(-3)!).toMatchObject([expect.any(Date), TaskStatus.SetToProvider, [{waitingTime: 4}] as any]);
  }, 1000);
});

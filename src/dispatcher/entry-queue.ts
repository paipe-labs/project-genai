import Heap from "heap-js";
import { Task, TaskStatus } from "./task";
import { NOOP } from "./utils/noop";

export const MAX_PRIORITY = Number.MAX_SAFE_INTEGER;

/** Priority queue with filter by min_price */
export class EntryQueue {

  // Priority might be a timestamp + delta depends on priority, so old tasks are always first
  private queue = new Heap((a: Task, b: Task) => a.getPriority() - b.getPriority());

  addTask(task: Task, priority: number): void {
    task.setPriority(priority);
    this.queue.add(task);

    task.setStatus(TaskStatus.PushedIntoQueue);
    this.taskAdded(task);
  }

  removeTask(task: Task): void {
    this.queue.remove(task);
  }

  /** Returns the first task from the priority queue with the max_price > min_price */
  popTask(min_price?: number): Task | undefined {
    for (const task of this.queue) {
      if (min_price === undefined || task.getMaxPrice() > min_price) {
        this.queue.remove(task);
        return task;
      }
    }
    return undefined;
  }

  taskAdded: (task: Task) => void = NOOP;
}
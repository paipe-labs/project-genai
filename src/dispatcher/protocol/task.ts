
export type TaskInfoV1 = {
  _v: 1,
  task_options?: TaskOptions,
  id: string,
  max_price: number,
  time_to_money_ratio: number,
}

export type TaskResultV1 = {
  _v: 1,
  image: string,
}

export type TaskInfo = TaskInfoV1;
export type TaskResult = TaskResultV1;

export type TaskOptions = {
    prompt: string,
    model: string,
    size?: string,
    steps?: number,
};

export type TaskResultClient = {
  resultsUrl: string[],
  taskId: string,
  error?: string,
  type: 'result' | 'error' | 'status',
  status?: 'ready' | 'inProgress',
};
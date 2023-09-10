
export type TaskInfoV1 = {
  _v: 1,

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
from dispatcher.task import Task
from dispatcher.task_info import PublicTaskStatus, TaskResult

import uuid


class StorageManager:  # TODO switch to database
    def __init__(self):
        self._users_to_tasks = dict() 
        self._tokens_to_users = dict()
        self._task_to_users = dict()
    
    def maybe_add_user(self, token: str) -> int:
        if token not in self._tokens_to_users:
            self._tokens_to_users[token] = uuid.uuid4().int
        return self._tokens_to_users[token]
    
    def get_user_id(self, token: str) -> int:
        return self._tokens_to_users.get(token)

    def add_task(self, user_id: int, task_id: int, task: Task):
        if user_id not in self._users_to_tasks:
            self._users_to_tasks[user_id] = {}
        self._users_to_tasks[user_id][task_id] = {'task': task, 'status': PublicTaskStatus.PENDING}
        self._task_to_users[task_id] = user_id
    
    def get_task_data(self, task_id: int) -> Task:
        if task_id not in self._task_to_users:
            return None

        return self._users_to_tasks[self._task_to_users[task_id]]

    def add_result(self, task_id: int, result: TaskResult):
        if task_id not in self._task_to_users:
            return
        user_id = self._task_to_users[task_id]
        self._users_to_tasks[user_id][task_id]['status'] = PublicTaskStatus.SUCCESS
        self._users_to_tasks[user_id][task_id]['result'] = result
    

        


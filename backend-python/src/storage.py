from dispatcher.task import Task
from dispatcher.task_info import PublicTaskStatus

import uuid


class StorageManager:
    def __init__(self):
        self._users_to_tasks = dict()
        self._task_to_users = dict()

    def add_task(self, user_id: int, task_id: str, task: Task):
        if user_id not in self._users_to_tasks:
            self._users_to_tasks[user_id] = {}
        self._users_to_tasks[user_id][task_id] = {
            'task': task, 'status': PublicTaskStatus.PENDING.name}
        self._task_to_users[task_id] = user_id

    def get_task_data(self, task_id: str) -> dict:
        if task_id not in self._task_to_users:
            return None

        return self._users_to_tasks[self._task_to_users[task_id]][task_id]

    def get_task_data_with_verification(self, user_id: int, task_id: str) -> dict:
        if user_id not in self._users_to_tasks or task_id not in self._users_to_tasks[user_id]:
            return None

        return self._users_to_tasks[user_id][task_id]

    def get_tasks(self, user_id: int) -> dict:
        if user_id not in self._users_to_tasks:
            return None

        return self._users_to_tasks[user_id]

    def add_result(self, task_id: str, result_image_url: str):
        if task_id not in self._task_to_users:
            return
        user_id = self._task_to_users[task_id]
        self._users_to_tasks[user_id][task_id]['status'] = PublicTaskStatus.SUCCESS.name
        self._users_to_tasks[user_id][task_id]['result'] = {
            'images': result_image_url}


class UsersStorage:
    def __init__(self):
        self._tokens_to_users = dict()

    def get_user_id(self, token: str) -> int:
        if token not in self._tokens_to_users:
            self._tokens_to_users[token] = uuid.uuid4().int
        return self._tokens_to_users[token]

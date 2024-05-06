from constants.env import SUPABASE_URL, SUPABASE_KEY
from dispatcher.task import Task
from dispatcher.task_info import TaskInfo, TaskOptions, TaskStatus, TaskStatusPayload, StandardPipelineOptions, ComfyPipelineOptions, get_public_status
from utils.uuid import get_64bit_uuid


from supabase import create_client, Client
import json
import dataclasses
import uuid

url: str = SUPABASE_URL
key: str = SUPABASE_KEY
supabase: Client = create_client(url, key)


def build_task(data: dict) -> Task:
    info = json.loads(data.get('info', '{}'))
    opts = info.get('task_options')
    standard_pipeline = opts.get('standard_pipeline', None) if opts else None
    comfy_pipeline = opts.get('comfy_pipeline', None) if opts else None
    task = Task(
        TaskInfo(**{
            'id': info.get('id', 0),
            'max_cost': info.get('max_cost', 0),
            'time_to_money_ratio': info.get('time_to_money_ratio', 0),
            'task_options': TaskOptions(**{
                'standard_pipeline': StandardPipelineOptions(**standard_pipeline) if standard_pipeline else None,
                'comfy_pipeline': ComfyPipelineOptions(**{
                    'pipeline_data': comfy_pipeline.get('pipelineData'),
                    'pipeline_dependencies': comfy_pipeline.get('pipelineDependencies'),
                }) if comfy_pipeline else None
            })
        })
    )
    status = TaskStatus(data.get('status', 0))
    if status == TaskStatus.ASSIGNED_TO_PROVIDER:
        status_payload = AssignedToProviderPayload(
            task_status=status, provider_id=data.get('provider_id', 0))
    elif status == TaskStatus.SENT_FAILED:
        status_payload = SentFailedPayload(
            attempt_num=data.get('num_failed_attempts', 0))
    else:
        status_payload = TaskStatusPayload(task_status=status)
    task.set_status(TaskStatusPayload(task_status=status))
    task.set_priority(data.get('priority', 0))
    return task


class StorageManager:
    def __init__(self, table_name='TasksV1_tests', use_supabase=True):
        self._use_supabase = use_supabase
        if self._use_supabase:
            self._table_name = table_name
        else:
            self._users_to_tasks = dict()
            self._task_to_users = dict()

    def add_task(self, user_id: int, task_id: int, task: Task):
        if self._use_supabase:
            _, _ = supabase.table(self._table_name).upsert({
                'id': task_id,
                'user_id': user_id,
                'priority': task.priority,
                'num_failed_attempts': task.num_failed_attempts,
                'provider_id': task.provider_id,
                'status': task.status.value,
                'info': task.task_info.json,
                'log': json.dumps(task.log)}).execute()
        else:
            if user_id not in self._users_to_tasks:
                self._users_to_tasks[user_id] = {}
            self._users_to_tasks[user_id][task_id] = {
                'task': task, 'status': PublicTaskStatus.PENDING.name}
            self._task_to_users[task_id] = user_id

    def get_task_data(self, task_id: int) -> dict:
        if self._use_supabase:
            data, _ = supabase.table(self._table_name).select(
                'priority', 'status', 'provider_id', 'num_failed_attempts', 'info', 'log', 'result').eq('id', task_id).execute()

            if len(data[1]) == 0:
                return None
            result = data[1][0].get('result', '{}')
            task = build_task(data[1][0])
            return {
                'task': task,
                'status': get_public_status(task.status).name,
                'result': json.loads(result) if result else None
            }
        else:
            return self._users_to_tasks[self._task_to_users[task_id]][task_id]

    def get_task_data_with_verification(self, user_id: int, task_id: str) -> dict:
        if self._use_supabase:
            data, _ = supabase.table(self._table_name).select('priority', 'status', 'provider_id',
                                                              'num_failed_attempts', 'info', 'log', 'result').eq('id', task_id).eq('user_id', user_id).execute()

            if len(data[1]) == 0:
                return None
            result = data[1][0].get('result', '{}')
            task = build_task(data[1][0])
            return {
                'task': task,
                'status': get_public_status(task.status).name,
                'result': json.loads(result) if result else None
            }
        else:
            if user_id not in self._users_to_tasks or task_id not in self._users_to_tasks[user_id]:
                return None

            return self._users_to_tasks[user_id][task_id]

    def get_tasks(self, user_id: int) -> dict:
        if self._use_supabase:
            data, _ = supabase.table(self._table_name).select('priority', 'status', 'provider_id',
                                                              'num_failed_attempts', 'info', 'log', 'result').eq('user_id', user_id).execute()

            if len(data[1]) == 0:
                return None
            result = []
            for raw_task in data[1]:
                task = build_task(raw_task)
                result.append({
                    'task': task,
                    'status': get_public_status(task.status).name,
                    'result': json.loads(task.get('result', {}))
                })
            return result
        else:
            if user_id not in self._users_to_tasks or task_id not in self._users_to_tasks[user_id]:
                return None
            return self._users_to_tasks[user_id]

    def add_result(self, task_id: str, result_image_url: str):
        if self._use_supabase:
            print('adding res')
            data, count = supabase.table(self._table_name).upsert({
                'id': task_id,
                'status': task.status.value,
                'result': json.dumps({'images': result_image_url})}).execute()
        else:
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
            self._tokens_to_users[token] = get_64bit_uuid()
        return self._tokens_to_users[token]

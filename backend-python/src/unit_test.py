from dispatcher.task import build_task_from_query, Task
from dispatcher.task_info import (
    ComfyPipelineOptions,
    PublicTaskStatus,
    StandardPipelineOptions,
    TaskInfo,
    TaskOptions
)
from storage import StorageManager, UsersStorage

from copy import deepcopy

COMMON_TASK_ID = '1'
COMMON_TASK_DATA = {
    'max_cost': 15,
    'time_to_money_ratio': 1
}


def test_standart_pipeline_build():
    task_data = deepcopy(COMMON_TASK_DATA)
    standard_pipeline_options = {
        'standard_pipeline': {
            'prompt': 'space surfer',
            'model': 'SD2.1',
            'size': 512,
            'steps': 25,
        }
    }
    task_data.update(standard_pipeline_options)
    task = build_task_from_query(COMMON_TASK_ID, **task_data)

    assert isinstance(task, Task)
    assert task.id == COMMON_TASK_ID
    assert task.max_cost == task_data['max_cost']
    assert task.time_to_money_ratio == task_data['time_to_money_ratio']
    assert task.task_options == TaskOptions(**{'standard_pipeline': StandardPipelineOptions(**standard_pipeline_options['standard_pipeline'])})


def test_comfy_pipeline_build():
    task_data = deepcopy(COMMON_TASK_DATA)
    comfy_pipeline_options = {
        'comfy_pipeline': {
            'pipelineData': 'some_pipeline',
            'pipelineDependencies': {'some key': 'some val'},
        }
    }
    task_data.update(comfy_pipeline_options)
    task = build_task_from_query(COMMON_TASK_ID, **task_data)

    assert isinstance(task, Task)
    assert task.id == COMMON_TASK_ID
    assert task.max_cost == task_data['max_cost']
    assert task.time_to_money_ratio == task_data['time_to_money_ratio']
    assert task.task_options == TaskOptions(**{'comfy_pipeline': ComfyPipelineOptions(**{
        'pipeline_data': comfy_pipeline_options['comfy_pipeline'].get('pipelineData'),
        'pipeline_dependencies': comfy_pipeline_options['comfy_pipeline'].get('pipelineDependencies'),
    })})

def test_storage_manager():
    manager = StorageManager()
    users_storage = UsersStorage()
    uid1 = users_storage.get_user_id('token1')
    uid2 = users_storage.get_user_id('token2')
    manager.add_task(uid1, '1', Task(TaskInfo(id='1', max_cost=1, time_to_money_ratio=10)))
    manager.add_task(uid2, '2', Task(TaskInfo(id='2', max_cost=2, time_to_money_ratio=20)))
    
    task_info = manager.get_task_data('1')
    task_info['status'] == PublicTaskStatus.PENDING.name
    assert isinstance(task_info['task'], Task)
    assert task_info['task'].id == '1'
    assert task_info['task'].max_cost == 1
    assert task_info['task'].time_to_money_ratio == 10

    task_info = manager.get_task_data('2')
    task_info['status'] == PublicTaskStatus.PENDING.name
    assert isinstance(task_info['task'], Task)
    assert task_info['task'].id == '2'
    assert task_info['task'].max_cost == 2
    assert task_info['task'].time_to_money_ratio == 20

    task_info = manager.get_task_data_with_verification(uid2, '2')
    task_info['status'] == PublicTaskStatus.PENDING.name
    assert isinstance(task_info['task'], Task)
    assert task_info['task'].id == '2'
    assert task_info['task'].max_cost == 2
    assert task_info['task'].time_to_money_ratio == 20

    task_info = manager.get_task_data_with_verification(uid1, '2')
    assert task_info == None

    manager.add_result('2', 'result_image_url')
    task_info = manager.get_task_data_with_verification(uid2, '2')
    task_info['status'] == PublicTaskStatus.SUCCESS.name
    assert isinstance(task_info['task'], Task)
    assert task_info['task'].id == '2'
    assert task_info['task'].max_cost == 2
    assert task_info['task'].time_to_money_ratio == 20
    assert task_info['result'] == {'images': 'result_image_url'}

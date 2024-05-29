import sys
sys.path.append("/backend-python/src")


from utils.uuid import get_64bit_uuid
from storage import StorageManager, UsersStorage
from dispatcher.task_info import TaskInfo
from dispatcher.task import Task

def test_storage_manager():
    manager = StorageManager(use_supabase=False)
    users_storage = UsersStorage()
    uid1 = users_storage.get_user_id("token1")
    uid2 = users_storage.get_user_id("token2")
    uuid1 = get_64bit_uuid()
    uuid2 = get_64bit_uuid()
    manager.add_task(
        uid1, uuid1, Task(
            TaskInfo(id=uuid1, max_cost=1, time_to_money_ratio=10))
    )
    manager.add_task(
        uid2, uuid2, Task(
            TaskInfo(id=uuid2, max_cost=2, time_to_money_ratio=20))
    )

    task_info = manager.get_task_data(uuid1)
    assert isinstance(task_info["task"], Task)
    assert task_info["task"].id == uuid1
    assert task_info["task"].max_cost == 1
    assert task_info["task"].time_to_money_ratio == 10

    task_info = manager.get_task_data(uuid2)
    assert isinstance(task_info["task"], Task)
    assert task_info["task"].id == uuid2
    assert task_info["task"].max_cost == 2
    assert task_info["task"].time_to_money_ratio == 20

    task_info = manager.get_task_data_with_verification(uid2, uuid2)
    assert isinstance(task_info["task"], Task)
    assert task_info["task"].id == uuid2
    assert task_info["task"].max_cost == 2
    assert task_info["task"].time_to_money_ratio == 20

    task_info = manager.get_task_data_with_verification(uid1, uuid2)
    assert task_info is None

    manager.add_result(uuid2, "result_image_url")
    task_info = manager.get_task_data_with_verification(uid2, uuid2)
    assert isinstance(task_info["task"], Task)
    assert task_info["task"].id == uuid2
    assert task_info["task"].max_cost == 2
    assert task_info["task"].time_to_money_ratio == 20
    assert task_info["result"] == {"images": "result_image_url"}

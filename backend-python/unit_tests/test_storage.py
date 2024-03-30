import sys
sys.path.append("/backend-python/src")

from dispatcher.task import Task
from dispatcher.task_info import PublicTaskStatus, TaskInfo
from storage import StorageManager, UsersStorage


def test_storage_manager():
    manager = StorageManager()
    users_storage = UsersStorage()
    uid1 = users_storage.get_user_id("token1")
    uid2 = users_storage.get_user_id("token2")
    manager.add_task(
        uid1, "1", Task(TaskInfo(id="1", max_cost=1, time_to_money_ratio=10))
    )
    manager.add_task(
        uid2, "2", Task(TaskInfo(id="2", max_cost=2, time_to_money_ratio=20))
    )

    task_info = manager.get_task_data("1")
    task_info["status"] == PublicTaskStatus.PENDING.name
    assert isinstance(task_info["task"], Task)
    assert task_info["task"].id == "1"
    assert task_info["task"].max_cost == 1
    assert task_info["task"].time_to_money_ratio == 10

    task_info = manager.get_task_data("2")
    task_info["status"] == PublicTaskStatus.PENDING.name
    assert isinstance(task_info["task"], Task)
    assert task_info["task"].id == "2"
    assert task_info["task"].max_cost == 2
    assert task_info["task"].time_to_money_ratio == 20

    task_info = manager.get_task_data_with_verification(uid2, "2")
    task_info["status"] == PublicTaskStatus.PENDING.name
    assert isinstance(task_info["task"], Task)
    assert task_info["task"].id == "2"
    assert task_info["task"].max_cost == 2
    assert task_info["task"].time_to_money_ratio == 20

    task_info = manager.get_task_data_with_verification(uid1, "2")
    assert task_info is None

    manager.add_result("2", "result_image_url")
    task_info = manager.get_task_data_with_verification(uid2, "2")
    task_info["status"] == PublicTaskStatus.SUCCESS.name
    assert isinstance(task_info["task"], Task)
    assert task_info["task"].id == "2"
    assert task_info["task"].max_cost == 2
    assert task_info["task"].time_to_money_ratio == 20
    assert task_info["result"] == {"images": "result_image_url"}

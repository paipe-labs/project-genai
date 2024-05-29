import sys
sys.path.append("/backend-python/src")

import pytest
import asyncio

from dispatcher.dispatcher import Dispatcher
from dispatcher.meta_info import PrivateMetaInfo, PublicMetaInfo
from dispatcher.provider import Provider, OFFLINE_TIMEOUT
from dispatcher.network_connection import NetworkConnection
from dispatcher.task import Task
from dispatcher.task_info import TaskInfo, TaskStatus, TaskStatusPayload

pytest_plugins = ('pytest_asyncio',)

@pytest.mark.asyncio
async def test_add_task():
    dispatcher = Dispatcher()
    t1 = Task(task_info=TaskInfo(id="1", max_cost=1, time_to_money_ratio = 1))
    t2 = Task(task_info=TaskInfo(id="2", max_cost=2, time_to_money_ratio = 2))
    pub_meta_info = PublicMetaInfo(models=[], gpu_type="gpu1", ncpu=8, ram=32)
    p1 = Provider("1", pub_meta_info, PrivateMetaInfo(), NetworkConnection())
    p2 = Provider("2", pub_meta_info, PrivateMetaInfo(), NetworkConnection())
    p3 = Provider("3", pub_meta_info, PrivateMetaInfo(), NetworkConnection())

    await dispatcher.add_task(t1)
    assert t1.status == TaskStatus.FAILED

    dispatcher.add_provider(p1)
    dispatcher.add_provider(p2)
    dispatcher.add_provider(p3)
    assert len(dispatcher.providers) == 3

    await dispatcher.add_task(t1)
    prev = p1 if t1 in p1.tasks_in_progress else (p2 if t1 in p2.tasks_in_progress else p3)
    assert t1.status == TaskStatus.SENT and t1.provider_id == prev.id
    assert prev.queue_length == 1  and p1.queue_length + p2.queue_length + p3.queue_length == 1
    await dispatcher.add_task(t2)
    assert  t2.status == TaskStatus.SENT and t2.provider_id != prev.id
    assert prev.queue_length == 1 and p1.queue_length + p2.queue_length + p3.queue_length == 2


@pytest.mark.asyncio
async def test_reschedule_task():
    dispatcher = Dispatcher()
    t1 = Task(task_info=TaskInfo(id="1", max_cost=1, time_to_money_ratio = 1))
    pub_meta_info = PublicMetaInfo(models=[], gpu_type="gpu1", ncpu=8, ram=32)
    p1 = Provider("1", pub_meta_info, PrivateMetaInfo(), NetworkConnection())
    p2 = Provider("2", pub_meta_info, PrivateMetaInfo(), NetworkConnection())
    p3 = Provider("3", pub_meta_info, PrivateMetaInfo(), NetworkConnection())

    dispatcher.add_provider(p1)
    dispatcher.add_provider(p2)

    # reschedule on connection lost
    await dispatcher.add_task(t1)
    assert t1.status == TaskStatus.SENT and p1.queue_length + p2.queue_length == 1
    scheduled_to1 = p1 if p1.id ==  t1.provider_id else p2
    await scheduled_to1.on_connection_lost()
    assert t1.status == TaskStatus.SENT and t1.provider_id != scheduled_to1.id
    assert scheduled_to1.is_online == False and scheduled_to1.queue_length == 0 and p1.queue_length + p2.queue_length == 1

    await asyncio.sleep(OFFLINE_TIMEOUT)
    assert len(dispatcher.providers) == 1 and scheduled_to1.id not in dispatcher.providers

    # reschedule on closed
    dispatcher.add_provider(p3)
    t1.set_status(TaskStatusPayload(task_status=TaskStatus.UNSCHEDULED))
    await dispatcher.add_task(t1)
    assert t1.status == TaskStatus.SENT and p1.queue_length + p2.queue_length == 1
    scheduled_to2 = p1 if p1.id == t1.provider_id else (p2 if p2.id == t1.provider_id else p3)
    await scheduled_to2.on_closed()
    assert len(dispatcher.providers) == 1
    assert t1.status == TaskStatus.SENT and t1.provider_id != scheduled_to2.id and t1.provider_id != scheduled_to1.id
    assert scheduled_to1.queue_length == 0 and scheduled_to2.queue_length == 0 and p1.queue_length + p2.queue_length + p3.queue_length == 1


@pytest.mark.asyncio
async def test_abort_task():
    dispatcher = Dispatcher()
    t1 = Task(task_info=TaskInfo(id="1", max_cost=1, time_to_money_ratio = 1))
    pub_meta_info = PublicMetaInfo(models=[], gpu_type="gpu1", ncpu=8, ram=32)
    p1 = Provider("1", pub_meta_info, PrivateMetaInfo(), NetworkConnection())

    dispatcher.add_provider(p1)
    assert len(dispatcher.providers) == 1

    # abort task
    await dispatcher.add_task(t1)
    assert t1.status == TaskStatus.SENT and p1.queue_length == 1
    await p1.abort_task(t1)
    assert t1.status == TaskStatus.ABORTED and p1.queue_length == 0

    # fail task
    await dispatcher.add_task(t1)
    assert t1.status == TaskStatus.SENT and p1.queue_length == 1
    p1.task_failed(t1, "test failure")
    assert t1.status == TaskStatus.FAILED and p1.queue_length == 0


@pytest.mark.asyncio
async def test_providers_simple():
    dispatcher = Dispatcher()
    pub_meta_info = PublicMetaInfo(models=[], gpu_type="gpu1", ncpu=8, ram=32)
    p1 = Provider("1", pub_meta_info, PrivateMetaInfo(), NetworkConnection())
    p2 = Provider("2", pub_meta_info, PrivateMetaInfo(), NetworkConnection())
    p3 = Provider("3", pub_meta_info, PrivateMetaInfo(), NetworkConnection())

    dispatcher.add_provider(p1)
    assert len(dispatcher.providers) == 1
    dispatcher.add_provider(p1)
    assert len(dispatcher.providers) == 1
    assert p1.queue_length == 0
    assert dispatcher.providers["1"] == p1 and p1.id == "1" and  dispatcher.providers[p1.id] == p1

    dispatcher.add_provider(p2)
    dispatcher.add_provider(p3)
    assert len(dispatcher.providers) == 3
    assert dispatcher.providers[p2.id] == p2 and dispatcher.providers[p3.id] == p3

    await dispatcher.remove_provider(p1.id)
    assert len(dispatcher.providers) == 2 and p1.id not in dispatcher.providers
    await dispatcher.remove_provider(p2.id)
    await dispatcher.remove_provider(p3.id)
    assert len(dispatcher.providers) == 0

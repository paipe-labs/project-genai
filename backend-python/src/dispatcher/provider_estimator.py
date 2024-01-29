from dispatcher.meta_info import PublicMetaInfo, PrivateMetaInfo
from dispatcher.util.logger import logger
from dispatcher.task import Task

import typing


class ProviderEstimator:
    def __init__(self, public_meta_info: PublicMetaInfo, private_meta_info: PrivateMetaInfo):
        self._private_meta_info = private_meta_info
        self._public_meta_info = public_meta_info
        self._estimated_time: dict[Task,int] = dict()
        self._total_estimated_time = 0

    @property
    def waiting_time(self):
        return self._total_estimated_time

    # why is it mutable?
    def update_public_meta_info(self, public_meta_info: PublicMetaInfo):
        self._public_meta_info = public_meta_info

    def update_private_meta_info(self, private_meta_info: PrivateMetaInfo):
        self._private_meta_info = private_meta_info

    def add_task(self, task: Task):
        if task in self._estimated_time.keys():
            logger.warning("adding task {id} duplicate".format(id=task.id))
            return
        estimated_time = self.estimate_task_time(task)
        self._estimated_time[task] = estimated_time
        self._total_estimated_time += estimated_time

    def remove_task(self, task: Task):
        if task not in self._estimated_time.keys():
            logger.warning("trying to remove task {id} that wasn't added".format(id=task.id))
            return
        self._total_estimated_time -= self._estimated_time.pop(task)

    def estimate_task_time(self, task: Task) -> int: # in milliseconds
        # TODO
        return 4


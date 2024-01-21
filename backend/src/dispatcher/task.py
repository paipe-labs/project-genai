from typing import Dict, Union, Tuple
from datetime import datetime
from dispatcher.utils.noop import NOOP
import json

class TaskStatus:
    Initial = 0
    PushedIntoQueue = 1
    PulledByDispatcher = 2
    RejectedByDispatcher = 3
    SetToProvider = 4
    SentFailed = 5
    SentToProvider = 6
    FailedByProvider = 7
    Aborted = 8
    Completed = 9
    Timeout = 10

TaskStatusPayload = Dict[
    Union[
      TaskStatus.SetToProvider,
      TaskStatus.SentFailed,
      TaskStatus.FailedByProvider
    ],
    Tuple[Dict[str, Union[str, int]], ...]
] 

class Task:
	def init(self, task_info):
		self.failedAttempts = 0
		self.priority = 0
		self.providerId = None
		self.status = TaskStatus.Initial
		self.log = []

		self.task_info = task_info

	def addFailedAttempt(self):
		self.failedAttempts += 1

	def getFailedAttempts(self):
		return self.failedAttempts

	def setPriority(self, priority):
		self.priority = priority

	def getPriority(self):
		return self.priority

	def setStatus(self, event, *payload):
		self.log.append([datetime.now(), event, payload])

	def getLog(self):
		return self.log

	def getLogString(self):
		log_string = ""
		for entry in self.log:
			timestamp = entry[0].isoformat()
			status = TaskStatus(entry[1]).name
			payload = ', '.join([json.dumps(v) for v in entry[2]])
			log_string += f"[{timestamp}] {status}: {payload}\n"
		return log_string

	def setProviderId(self, providerId):
		self.providerId = providerId

	def getProviderId(self):
		return self.providerId

	def complete(self, result):
		self.onCompleted(result)

	def fail(self):
		self.onFailed()

	onCompleted = NOOP
	onFailed = NOOP

	@property
	def id(self):
		return self.task_info['id']

	def getTaskOptions(self):
		return self.task_info.get('task_options')

	def getMaxPrice(self):
		return self.task_info['max_price']

	def getMoneyTimeRatio(self):
		return self.task_info['time_to_money_ratio']

import json
import sys
sys.path.append("/backend-python/src")

TASK_RESULT_SCHEMA_PATH = "src/schemas/task_result_schema.json"
TASK_SCHEMA_PATH = "src/schemas/task_schema.json"

with open(TASK_RESULT_SCHEMA_PATH) as task_result_schema:
    TASK_RESULT_SCHEMA = json.load(task_result_schema)

with open(TASK_SCHEMA_PATH) as task_schema:
    TASK_SCHEMA = json.load(task_schema)

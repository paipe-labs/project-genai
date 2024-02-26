import os

from utils.parse import parse

DEBUG = parse(os.environ.get("DEBUG", ""), False, bool)
ENFORCE_JWT_AUTH = parse(os.environ.get("ENFORCE_JWT_AUTH", ""), True, bool)
HTTP_WS_PORT = parse(os.environ.get("HTTP_PORT", ""), 8080, int)
JWT_SECRET = os.environ.get("JWT_SECRET", "")
TASK_RESULT_SCHEMA_PATH = os.environ.get("TASK_RESULT_SCHEMA_PATH", "src/task_result_schema.json")
TASK_SCHEMA_PATH = os.environ.get("TASK_SCHEMA_PATH", "src/task_schema.json")

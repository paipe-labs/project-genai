import os

DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
ENFORCE_JWT_AUTH = os.environ.get("ENFORCE_JWT_AUTH", "true").lower() == "true"
HTTP_WS_PORT = int(os.environ.get("HTTP_PORT", "8080"))

WS_TASK_TIMEOUT = int(os.environ.get("WS_TASK_TIMEOUT", "60"))

JWT_SECRET = os.environ.get("JWT_SECRET", "")

import os

from utils.parse import parse

DEBUG = parse(os.environ.get("DEBUG", ""), False, bool)
ENFORCE_JWT_AUTH = parse(os.environ.get("ENFORCE_JWT_AUTH", ""), True, bool)
HTTP_WS_PORT = parse(os.environ.get("HTTP_PORT", ""), 8080, int)
JWT_SECRET = os.environ.get("JWT_SECRET", "")

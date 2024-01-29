import os
from utils.parse import parse

HTTP_WS_PORT = parse(os.environ.get('HTTP_PORT', ''), 8080, int)
ENFORCE_JWT_AUTH = parse(os.environ.get('ENFORCE_JWT_AUTH', ''), True, bool)
JWT_SECRET = os.environ.get('JWT_SECRET', '')
DEBUG = parse(os.environ.get('DEBUG', ''), False, bool)

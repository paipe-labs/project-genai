import jwt
from constants.env import JWT_SECRET

def jwt_verify(accessToken: str):
    try:
        return jwt.decode(accessToken, JWT_SECRET, algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return None

from utils.jwt import jwt_verify


def verify(token: str) -> bool:
    try:
        jwt = jwt_verify(token)
        if isinstance(jwt, str):
            return False
        # Expiration is checked automatically
        # Can check jwt['user_metadata']

        return True
    except:
        return False

from utils.jwt import jwtVerify

def verify(token: str) -> bool:
    try:
        jwt = jwtVerify(token)
        if isinstance(jwt, str):
            return False
        # Expiration is checked automatically
        # Can check jwt['user_metadata']

        return True
    except:
        return False
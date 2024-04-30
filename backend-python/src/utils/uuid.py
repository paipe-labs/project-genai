import uuid

def get_64bit_uuid() -> int:
    return ((1 << 63) - 1) & uuid.uuid4().int

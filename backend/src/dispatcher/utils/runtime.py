from utils.logger import logger

def warnIf(condition: bool, *data) -> bool:
    if condition:
        logger.warning(*data)
    return condition

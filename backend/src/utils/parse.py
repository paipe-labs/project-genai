def parse(value: str, default: any, dtype: type):
    try:
        return dtype(value)
    except (ValueError, TypeError):
        return default

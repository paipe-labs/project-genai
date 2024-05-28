import typing


class PublicMetaInfo(typing.NamedTuple):
    models: list[str]
    gpu_type: str
    ncpu: int
    ram: int


class PrivateMetaInfo(typing.NamedTuple):
    pass

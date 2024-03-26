import typing

class PublicMetaInfo(typing.NamedTuple):
    models: list[str]
    gpu_type: str
    ncpu: int
    ram: int

    min_cost: int # TODO: get rid of this


class PrivateMetaInfo(typing.NamedTuple):
    pass

from dataclasses import dataclass

@dataclass
class PublicMetaInfoV1:
    _v: int
    min_cost: float

@dataclass
class PrivateMetaInfoV1:
    _v: int

PublicMetaInfo = PublicMetaInfoV1
PrivateMetaInfo = PrivateMetaInfoV1

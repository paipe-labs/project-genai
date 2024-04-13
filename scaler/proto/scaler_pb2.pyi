from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class NodeInfo(_message.Message):
    __slots__ = ("node_id", "platform", "backend", "image")
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    PLATFORM_FIELD_NUMBER: _ClassVar[int]
    BACKEND_FIELD_NUMBER: _ClassVar[int]
    IMAGE_FIELD_NUMBER: _ClassVar[int]
    node_id: str
    platform: str
    backend: str
    image: str
    def __init__(self, node_id: _Optional[str] = ..., platform: _Optional[str] = ..., backend: _Optional[str] = ..., image: _Optional[str] = ...) -> None: ...

class CreateNodeRequest(_message.Message):
    __slots__ = ("platform", "backend", "image", "prov_script", "vastai_iid")
    PLATFORM_FIELD_NUMBER: _ClassVar[int]
    BACKEND_FIELD_NUMBER: _ClassVar[int]
    IMAGE_FIELD_NUMBER: _ClassVar[int]
    PROV_SCRIPT_FIELD_NUMBER: _ClassVar[int]
    VASTAI_IID_FIELD_NUMBER: _ClassVar[int]
    platform: str
    backend: str
    image: str
    prov_script: str
    vastai_iid: int
    def __init__(self, platform: _Optional[str] = ..., backend: _Optional[str] = ..., image: _Optional[str] = ..., prov_script: _Optional[str] = ..., vastai_iid: _Optional[int] = ...) -> None: ...

class CreateNodeResponse(_message.Message):
    __slots__ = ("node_id",)
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    node_id: str
    def __init__(self, node_id: _Optional[str] = ...) -> None: ...

class DeleteNodeRequest(_message.Message):
    __slots__ = ("node_id",)
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    node_id: str
    def __init__(self, node_id: _Optional[str] = ...) -> None: ...

class DeleteNodeResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ListNodesResponse(_message.Message):
    __slots__ = ("nodes",)
    NODES_FIELD_NUMBER: _ClassVar[int]
    nodes: _containers.RepeatedCompositeFieldContainer[NodeInfo]
    def __init__(self, nodes: _Optional[_Iterable[_Union[NodeInfo, _Mapping]]] = ...) -> None: ...

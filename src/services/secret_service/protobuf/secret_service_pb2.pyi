import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class InitStorageRequest(_message.Message):
    __slots__ = ("shares", "threshold")
    SHARES_FIELD_NUMBER: _ClassVar[int]
    THRESHOLD_FIELD_NUMBER: _ClassVar[int]
    shares: int
    threshold: int
    def __init__(self, shares: _Optional[int] = ..., threshold: _Optional[int] = ...) -> None: ...

class InitStorageResponse(_message.Message):
    __slots__ = ("shares",)
    SHARES_FIELD_NUMBER: _ClassVar[int]
    shares: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, shares: _Optional[_Iterable[str]] = ...) -> None: ...

class UnsealRequest(_message.Message):
    __slots__ = ("shares",)
    SHARES_FIELD_NUMBER: _ClassVar[int]
    shares: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, shares: _Optional[_Iterable[str]] = ...) -> None: ...

class SealRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PutSecretRequest(_message.Message):
    __slots__ = ("path", "json_value", "expires_at", "metadata", "if_version")
    PATH_FIELD_NUMBER: _ClassVar[int]
    JSON_VALUE_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_AT_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    IF_VERSION_FIELD_NUMBER: _ClassVar[int]
    path: _containers.RepeatedScalarFieldContainer[str]
    json_value: str
    expires_at: _timestamp_pb2.Timestamp
    metadata: _struct_pb2.Struct
    if_version: int
    def __init__(self, path: _Optional[_Iterable[str]] = ..., json_value: _Optional[str] = ..., expires_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., metadata: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., if_version: _Optional[int] = ...) -> None: ...

class GetSecretRequest(_message.Message):
    __slots__ = ("path",)
    PATH_FIELD_NUMBER: _ClassVar[int]
    path: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, path: _Optional[_Iterable[str]] = ...) -> None: ...

class GetSecretResponse(_message.Message):
    __slots__ = ("json_value", "created_at", "updated_at", "expires_at", "version", "metadata")
    JSON_VALUE_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_AT_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    json_value: str
    created_at: _timestamp_pb2.Timestamp
    updated_at: _timestamp_pb2.Timestamp
    expires_at: _timestamp_pb2.Timestamp
    version: int
    metadata: _struct_pb2.Struct
    def __init__(self, json_value: _Optional[str] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., updated_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., expires_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., version: _Optional[int] = ..., metadata: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class DeleteSecretRequest(_message.Message):
    __slots__ = ("path", "if_version")
    PATH_FIELD_NUMBER: _ClassVar[int]
    IF_VERSION_FIELD_NUMBER: _ClassVar[int]
    path: _containers.RepeatedScalarFieldContainer[str]
    if_version: int
    def __init__(self, path: _Optional[_Iterable[str]] = ..., if_version: _Optional[int] = ...) -> None: ...

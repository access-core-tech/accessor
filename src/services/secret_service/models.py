# services/secret_service/models.py
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from google.protobuf import struct_pb2, timestamp_pb2


@dataclass
class InitStorageRequest:
    shares: int
    threshold: int


@dataclass
class InitStorageResponse:
    shares: List[str]


@dataclass
class UnsealRequest:
    shares: List[str]


@dataclass
class PutSecretRequest:
    path: List[str]
    json_value: Any
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    if_version: Optional[int] = None

    def to_proto_dict(self) -> Dict:
        """Преобразует модель в словарь для protobuf"""
        result = {
            'path': self.path,
            'json_value': json.dumps(self.json_value) if not isinstance(self.json_value, str) else self.json_value,
        }

        if self.expires_at:
            timestamp = timestamp_pb2.Timestamp()
            timestamp.FromDatetime(self.expires_at)
            result['expires_at'] = timestamp

        if self.metadata:
            struct = struct_pb2.Struct()
            struct.update(self.metadata)
            result['metadata'] = struct

        if self.if_version is not None:
            result['if_version'] = self.if_version

        return result


@dataclass
class GetSecretRequest:
    path: List[str]


@dataclass
class GetSecretResponse:
    json_value: dict
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    version: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_proto(cls, proto_response) -> 'GetSecretResponse':
        """Создает модель из protobuf response"""
        # Обработка JSON значения
        try:
            json_value = json.loads(proto_response.json_value)
        except (json.JSONDecodeError, AttributeError, TypeError):
            json_value = getattr(proto_response, 'json_value', None)

        # Вспомогательная функция для конвертации timestamp
        def convert_proto_timestamp(ts_proto):
            """Конвертирует protobuf Timestamp в datetime"""
            if not ts_proto:
                return None
            try:
                # Проверяем, не пустой ли timestamp (seconds=0 и nanos=0)
                if hasattr(ts_proto, 'seconds') and hasattr(ts_proto, 'nanos'):
                    if ts_proto.seconds == 0 and ts_proto.nanos == 0:
                        return None

                # Конвертируем
                if hasattr(ts_proto, 'ToDatetime'):
                    return ts_proto.ToDatetime()

                # Альтернативный способ для protobuf >= 3.12
                if hasattr(ts_proto, 'GetCurrentTime'):
                    import datetime as dt
                    from datetime import timezone

                    return dt.datetime.fromtimestamp(ts_proto.seconds + ts_proto.nanos / 1e9, tz=timezone.utc)

            except Exception as e:
                print(f'Warning: Failed to convert timestamp: {e}')
            return None

        # Конвертируем timestamp поля
        created_at = None
        updated_at = None
        expires_at = None

        if hasattr(proto_response, 'created_at'):
            created_at = convert_proto_timestamp(proto_response.created_at)

        if hasattr(proto_response, 'updated_at'):
            updated_at = convert_proto_timestamp(proto_response.updated_at)

        if hasattr(proto_response, 'expires_at'):
            expires_at = convert_proto_timestamp(proto_response.expires_at)

        # Получаем версию
        version = getattr(proto_response, 'version', None)

        # Получаем метаданные
        metadata = {}
        if hasattr(proto_response, 'metadata') and proto_response.metadata:
            try:
                metadata = dict(proto_response.metadata)
            except:
                metadata = {}

        return cls(
            json_value=json_value,
            created_at=created_at,
            updated_at=updated_at,
            expires_at=expires_at,
            version=version,
            metadata=metadata,
        )


@dataclass
class DeleteSecretRequest:
    path: List[str]
    if_version: Optional[int] = None

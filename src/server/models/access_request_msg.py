from uuid import UUID
from pydantic import BaseModel
from enum import StrEnum


class ResourceType(StrEnum):
    # Базы данных
    POSTGRESQL = "postgresql"
    MONGODB = 'mongodb'
    MARIA_DB = 'mariadb'
    CLICKHOUSE = 'clickhouse'

    # Кеши
    REDIS = "redis"


class ResourceAccesses(StrEnum):
    READ = 'read'
    WRITE = 'write'
    DELETE = 'delete'


class AccessRequest(BaseModel):
    """Запрос на создание доступа"""

    project_name: str
    resource_type: ResourceType
    resource_name: str
    accesses: set[ResourceAccesses]
    requester_uuid: UUID
    requester_login_email: str
    ttl_minutes: int

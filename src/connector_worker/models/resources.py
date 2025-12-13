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

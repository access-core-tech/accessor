from connector_worker.models.resources import ResourceType
from connector_worker.providers.db_providers.postgresql import PostgresSQLDBProvider
from connector_worker.providers.db_providers.mongodb import MongoDBProvider
from connector_worker.providers.db_providers.mariadb import MariaDBProvider
from connector_worker.providers.db_providers.clickhouse import ClickHouseProvider
from connector_worker.providers.db_providers.redis import RedisProvider
from connector_worker.providers.base import BaseProvider
from connector_worker.providers.errors import ResourceProviderNotExists

_provider_by_resource_type_map: dict[ResourceType, type[BaseProvider]] = {
    ResourceType.POSTGRESQL: PostgresSQLDBProvider,
    ResourceType.MONGODB: MongoDBProvider,
    ResourceType.MARIA_DB: MariaDBProvider,
    ResourceType.CLICKHOUSE: ClickHouseProvider,
    ResourceType.REDIS: RedisProvider,
}


def select_provider(resource_type: ResourceType) -> BaseProvider:
    provider_class = _provider_by_resource_type_map.get(resource_type)
    if not provider_class:
        raise ResourceProviderNotExists(f'Not found provider for resource type {resource_type}')

    return provider_class()

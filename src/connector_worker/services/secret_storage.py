import datetime

from connector_worker.config import settings
from connector_worker.models.configs.db_config import (
    ClickhouseDBConfig,
    MariaDBConfig,
    MongoDBConfig,
    PostgresSQLConfig,
    RedisDBConfig,
)
from services.secret_service.client import SecretStoreClient


class SecretStorageService:
    def __init__(self):
        self.secret_store_client = SecretStoreClient(
            host=settings.SECRET_STORE_GRPC_HOST, port=settings.SECRET_STORE_GRPC_PORT
        )

    async def get_postgressql_config(self, project: str, resource_type: str, resource_name: str) -> PostgresSQLConfig:
        raw_config = await self.get_resource_config(project, resource_type, resource_name)
        return PostgresSQLConfig(**raw_config.json_value)

    async def get_mongodb_config(self, project: str, resource_type: str, resource_name: str) -> MongoDBConfig:
        raw_config = await self.get_resource_config(project, resource_type, resource_name)
        return MongoDBConfig(**raw_config.json_value)

    async def get_mariadb_config(self, project: str, resource_type: str, resource_name: str) -> MariaDBConfig:
        raw_config = await self.get_resource_config(project, resource_type, resource_name)
        return MariaDBConfig(**raw_config.json_value)

    async def get_clickhouse_config(self, project: str, resource_type: str, resource_name: str) -> ClickhouseDBConfig:
        raw_config = await self.get_resource_config(project, resource_type, resource_name)
        return ClickhouseDBConfig(**raw_config.json_value)

    async def get_redis_config(self, project: str, resource_type: str, resource_name: str) -> RedisDBConfig:
        raw_config = await self.get_resource_config(project, resource_type, resource_name)
        return RedisDBConfig(**raw_config.json_value)

    async def get_resource_config(self, project: str, resource_type: str, resource_name: str):
        async with self.secret_store_client as client:
            config = await client.get_secret(
                path=[project, resource_type, resource_name, '_admin'],
            )

        return config

    async def save_user_access(
        self,
        project: str,
        resource_type: str,
        resource_name: str,
        user_uuid: str,
        user_access_payload: dict,
        expire_at: datetime.datetime,
        metadata: dict | None = None,
    ):
        async with self.secret_store_client as client:
            await client.put_secret(
                path=[project, resource_type, resource_name, user_uuid, 'config'],
                value=user_access_payload,
                expires_at=expire_at,
                metadata=metadata,
            )

    async def get_user_access_username(
        self,
        project: str,
        resource_type: str,
        resource_name: str,
        user_uuid: str,
    ) -> str | None:
        async with self.secret_store_client as client:
            secret = await client.get_secret(
                path=[project, resource_type, resource_name, user_uuid, 'config'],
            )
        if secret:
            return secret.json_value.get('username')

    async def delete_user_access(
        self,
        project: str,
        resource_type: str,
        resource_name: str,
        user_uuid: str,
    ):
        async with self.secret_store_client as client:
            return await client.delete_secret(path=[project, resource_type, resource_name, user_uuid, 'config'])

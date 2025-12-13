import redis.asyncio as redis
import sentry_sdk
from connector_worker.models.configs.db_config import RedisDBConfig
from connector_worker.models.resources import ResourceType
from connector_worker.providers.db_providers.base_db_provider import BaseDBProvider
from connector_worker.services.secret_storage import SecretStorageService


class RedisProvider(BaseDBProvider):
    resource_type = ResourceType.REDIS

    def __init__(self):
        self.secret_storage_service = SecretStorageService()

    async def get_connection_config(
        self,
        project_name: str,
        resource_type: ResourceType,
        resource_name: str,
    ) -> RedisDBConfig:
        return await self.secret_storage_service.get_redis_config(
            project=project_name,
            resource_type=resource_type,
            resource_name=resource_name,
        )

    async def test_connection(self, db_config: RedisDBConfig) -> bool:
        client = None
        try:
            client = self._make_client(db_config)
            await client.ping()
            return True
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return False
        finally:
            if client:
                await client.close()

    async def create_db_user(self, username: str, password: str, db_config: RedisDBConfig):
        client = None
        try:
            client = self._make_client(db_config)

            redis_username = username.replace('.', '_')

            await client.acl_setuser(
                username=redis_username,
                enabled=True,
                passwords=[f'+{password}'],
                commands=['+get', '+set', '+ping', '+exists', '+keys', '+ttl'],
                keys=['*'],
                channels=['*'],
            )

            print(f'Redis ACL user created: {redis_username}')

        except Exception as ex:
            sentry_sdk.capture_exception(ex)
            raise ex
        finally:
            if client:
                await client.close()

    async def delete_db_user(self, username: str, db_config: RedisDBConfig):
        client = None
        try:
            client = self._make_client(db_config)

            acl_users = await client.acl_users()

            if username in acl_users:
                await client.acl_deluser(username)

        finally:
            if client:
                await client.close()

    @staticmethod
    def _make_client(db_config: RedisDBConfig) -> redis.Redis:
        return redis.Redis(
            host=db_config.host,
            port=db_config.port,
            password=db_config.password,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
        )

import motor.motor_asyncio
import sentry_sdk
from connector_worker.models.configs.db_config import MongoDBConfig
from connector_worker.models.resources import ResourceType
from connector_worker.providers.db_providers.base_db_provider import BaseDBProvider
from connector_worker.services.secret_storage import SecretStorageService
from pymongo.errors import PyMongoError


class MongoDBProvider(BaseDBProvider):
    resource_type = ResourceType.MONGODB

    def __init__(self):
        self.secret_storage_service = SecretStorageService()

    async def get_connection_config(
        self,
        project_name: str,
        resource_type: ResourceType,
        resource_name: str,
    ) -> MongoDBConfig:
        """Получить конфигурацию подключения к MongoDB"""
        return await self.secret_storage_service.get_mongodb_config(
            project=project_name,
            resource_type=resource_type,
            resource_name=resource_name,
        )

    async def test_connection(self, db_config: MongoDBConfig) -> bool:
        client = None
        try:
            client = self._make_client(db_config)
            await client.admin.command('ping')
            return True
        except PyMongoError as e:
            sentry_sdk.capture_exception(e)
            return False
        finally:
            if client:
                client.close()

    async def create_db_user(self, username: str, password: str, db_config: MongoDBConfig):
        client = None
        try:
            client = self._make_client(db_config)

            await client[db_config.database].command(
                'createUser',
                username,
                pwd=password,
                roles=[
                    {'role': 'read', 'db': db_config.database},
                ],
            )

        except PyMongoError as e:
            sentry_sdk.capture_exception(e)
            raise
        finally:
            if client:
                client.close()

    async def delete_db_user(self, username: str, db_config: MongoDBConfig):
        client = None
        try:
            client = self._make_client(db_config)

            await client[db_config.database].command(
                'dropUser',
                username,
            )

        except PyMongoError as e:
            sentry_sdk.capture_exception(e)
            raise Exception(f'Failed to delete MongoDB user {username}: {str(e)}')

        finally:
            if client:
                client.close()

    def _make_client(self, db_config: MongoDBConfig) -> motor.motor_asyncio.AsyncIOMotorClient:
        auth_part = f'{db_config.user}:{db_config.password}@' if db_config.user and db_config.password else ''
        host_part = f'{db_config.host}:{db_config.port}'

        return motor.motor_asyncio.AsyncIOMotorClient(
            f'mongodb://{auth_part}{host_part}/',
            serverSelectionTimeoutMS=10000,
        )

import aiochclient
import aiohttp
import sentry_sdk

from connector_worker.models.resources import ResourceType
from connector_worker.models.configs.db_config import ClickhouseDBConfig
from connector_worker.providers.db_providers.base_db_provider import BaseDBProvider
from connector_worker.services.secret_storage import SecretStorageService


class ClickHouseProvider(BaseDBProvider):
    resource_type = ResourceType.CLICKHOUSE

    def __init__(self):
        self.secret_storage_service = SecretStorageService()

    async def get_connection_config(
        self,
        project_name: str,
        resource_type: ResourceType,
        resource_name: str,
    ) -> ClickhouseDBConfig:
        return await self.secret_storage_service.get_clickhouse_config(
            project=project_name,
            resource_type=resource_type,
            resource_name=resource_name,
        )

    async def test_connection(self, db_config: ClickhouseDBConfig) -> bool:
        client = None
        try:
            client = await self._make_client(db_config)
            await client.execute("SELECT 1")
            return True
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return False
        finally:
            if client:
                await client.close()

    async def create_db_user(self, username: str, password: str, db_config: ClickhouseDBConfig):
        client = None
        try:
            client = await self._make_client(db_config)

            # оказывается кликхаусе не могут быть точки в именИ)
            clickhouse_username = username.replace('.', '_')
            await client.execute(
                f"CREATE USER IF NOT EXISTS {clickhouse_username} IDENTIFIED WITH plaintext_password BY '{password}'"
            )

        except Exception as ex:
            sentry_sdk.capture_exception(ex)
            raise ex
        finally:
            if client:
                await client.close()

    async def delete_db_user(self, username: str, db_config: ClickhouseDBConfig):
        client = None
        try:
            client = await self._make_client(db_config)

            await client.execute(f"DROP USER IF EXISTS {username}")

            # завершаем сессии пользовотеля
            await client.execute(
                f"""
                KILL QUERY 
                WHERE user = '{username}'
                SYNC
                """
            )
        finally:
            if client:
                await client.close()

    @staticmethod
    async def _make_client(db_config: ClickhouseDBConfig) -> aiochclient.ChClient:
        connector = aiohttp.TCPConnector()
        session = aiohttp.ClientSession(connector=connector)

        return aiochclient.ChClient(
            session,
            url=f'http://{db_config.host}:{db_config.port}/',
            user=db_config.user,
            password=db_config.password,
            database=db_config.database,
        )

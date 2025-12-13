import asyncpg
import sentry_sdk
from connector_worker.models.configs.db_config import PostgresSQLConfig
from connector_worker.models.resources import ResourceType
from connector_worker.providers.db_providers.base_db_provider import BaseDBProvider
from connector_worker.services.secret_storage import SecretStorageService


class PostgresSQLDBProvider(BaseDBProvider):
    resource_type = ResourceType.POSTGRESQL

    def __init__(self):
        self.secret_storage_service = SecretStorageService()

    async def get_connection_config(
        self,
        project_name: str,
        resource_type: ResourceType,
        resource_name: str,
    ) -> PostgresSQLConfig:
        return await self.secret_storage_service.get_postgressql_config(
            project=project_name,
            resource_type=resource_type,
            resource_name=resource_name,
        )

    async def test_connection(self, db_config: PostgresSQLConfig) -> bool:
        conn = None
        try:
            conn = await self._make_connect(db_config)
            return True
        except asyncpg.PostgresError as e:
            sentry_sdk.capture_exception(e)
            return False
        finally:
            if conn:
                await conn.close()

    async def create_db_user(self, username: str, password: str, db_config: PostgresSQLConfig):
        conn = None
        try:
            conn = await self._make_connect(db_config)

            await conn.execute(
                f"""
                CREATE USER "{username}" 
                WITH PASSWORD '{password}'
                NOCREATEDB
                NOCREATEROLE
                NOREPLICATION
                CONNECTION LIMIT 5;
            """
            )

        except Exception as ex:
            sentry_sdk.capture_exception(ex)
            raise ex
        finally:
            if conn:
                await conn.close()

    async def delete_db_user(self, username: str, db_config: PostgresSQLConfig):
        conn = None
        try:
            conn = await self._make_connect(db_config)

            user_exists = await conn.fetchval('SELECT 1 FROM pg_roles WHERE rolname = $1', username)

            if user_exists:
                await conn.execute(
                    """
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE usename = $1
                    """,
                    username,
                )

                await conn.execute(f'DROP USER IF EXISTS "{username}"')

            else:
                sentry_sdk.capture_message(f'User {username} does not exist in PostgreSQL, skipping deletion')

        except Exception as ex:
            sentry_sdk.capture_exception(ex)
            raise Exception(f'Failed to delete PostgreSQL user {username}: {str(ex)}')

        finally:
            if conn:
                await conn.close()

    @staticmethod
    async def _make_connect(db_config: PostgresSQLConfig) -> asyncpg.Connection:
        return await asyncpg.connect(
            host=db_config.host,
            port=db_config.port,
            user=db_config.user,
            password=db_config.password,
            database=db_config.database,
        )

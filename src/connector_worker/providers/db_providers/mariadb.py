import aiomysql
import sentry_sdk

from connector_worker.models.resources import ResourceType
from connector_worker.models.configs.db_config import MariaDBConfig
from connector_worker.providers.db_providers.base_db_provider import BaseDBProvider
from connector_worker.services.secret_storage import SecretStorageService


class MariaDBProvider(BaseDBProvider):
    resource_type = ResourceType.MARIA_DB

    def __init__(self):
        self.secret_storage_service = SecretStorageService()

    async def get_connection_config(
        self,
        project_name: str,
        resource_type: ResourceType,
        resource_name: str,
    ) -> MariaDBConfig:
        return await self.secret_storage_service.get_mariadb_config(
            project=project_name,
            resource_type=resource_type,
            resource_name=resource_name,
        )

    async def test_connection(self, db_config: MariaDBConfig) -> bool:
        conn = None
        try:
            conn = await self._make_connect(db_config)
            return True
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return False
        finally:
            if conn:
                conn.close()

    async def create_db_user(self, username: str, password: str, db_config: MariaDBConfig):
        conn = None
        try:
            conn = await self._make_connect(db_config)

            safe_password = password.replace("'", "''")

            async with conn.cursor() as cursor:
                await cursor.execute(f"CREATE USER '{username}'@'%' IDENTIFIED BY '{safe_password}'")
        except Exception as ex:
            sentry_sdk.capture_exception(ex)
            raise ex
        finally:
            if conn:
                conn.close()

    async def delete_db_user(self, username: str, db_config: MariaDBConfig):
        conn = None
        try:
            conn = await self._make_connect(db_config)

            async with conn.cursor() as cursor:
                await cursor.execute(f"SELECT 1 FROM mysql.user WHERE user = '{username}' AND host = '%'")
                user_exists = await cursor.fetchone()

                if user_exists:
                    await cursor.execute(
                        f"""
                        SELECT CONCAT('KILL ', id, ';') 
                        FROM information_schema.processlist 
                        WHERE user = '{username}'
                        """
                    )
                    kill_commands = await cursor.fetchall()

                    for kill_cmd in kill_commands:
                        try:
                            await cursor.execute(kill_cmd[0])
                        except Exception as ex:
                            # Логируем ошибки убийства соединений, но продолжаем
                            sentry_sdk.capture_exception(ex)

                    await cursor.execute(f"DROP USER IF EXISTS '{username}'@'%'")

                    await cursor.execute("FLUSH PRIVILEGES")

        except Exception as ex:
            sentry_sdk.capture_exception(ex)
            raise Exception(f"Failed to delete MariaDB user '{username}'@'%': {str(ex)}")

        finally:
            if conn:
                conn.close()

    @staticmethod
    async def _make_connect(db_config: MariaDBConfig) -> aiomysql.Connection:
        return await aiomysql.connect(
            host=db_config.host,
            port=db_config.port,
            user=db_config.user,
            password=db_config.password,
            db=db_config.database,
        )

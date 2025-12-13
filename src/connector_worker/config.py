from datetime import timedelta, timezone
from logging import getLogger

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(extra='ignore')

    DEBUG: bool = False
    SENTRY_DSN: str = ''
    TIMEZONE: timezone = timezone(offset=timedelta(hours=3), name='Europe/Moscow')

    # Secret Store
    SECRET_STORE_GRPC_HOST: str = 'localhost'
    SECRET_STORE_GRPC_PORT: int = 6668

    # MQ
    KAFKA_URL: str = 'localhost:9092'
    CREATE_ACCESS_TOPIC_NAME: str = 'create_access'
    REVOKE_ACCESS_TOPIC_NAME: str = 'revoke_access'


settings = Settings(_env_file='.env')


logger = getLogger('connector_worker')

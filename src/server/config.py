from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost/postgres"

    KAFKA_URL: str = 'localhost:9092'
    CREATE_ACCESS_TOPIC_NAME: str = 'create_access'
    REVOKE_ACCESS_TOPIC_NAME: str = 'revoke_access'


settings = Settings()

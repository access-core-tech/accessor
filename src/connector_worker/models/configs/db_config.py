from pydantic import BaseModel


class BaseDBConfig(BaseModel):
    host: str
    port: int
    user: str
    password: str
    database: str


class PostgresSQLConfig(BaseDBConfig): ...


class MongoDBConfig(BaseDBConfig): ...


class MariaDBConfig(BaseDBConfig): ...


class ClickhouseDBConfig(BaseDBConfig): ...


class RedisDBConfig(BaseDBConfig):
    user: str = 'default'

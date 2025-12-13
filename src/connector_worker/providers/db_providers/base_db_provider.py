import datetime
from abc import ABC, abstractmethod

from connector_worker.models.access_requests import (
    AccessRequest,
    BaseAccessRequest,
    DeprovisionRequest,
)
from connector_worker.models.configs.db_config import BaseDBConfig
from connector_worker.models.resources import ResourceType
from connector_worker.providers.base import BaseProvider
from connector_worker.providers.errors import (
    ResourceNotAvailableException,
    ResourceUserConfigNotFound,
)
from connector_worker.services.secret_storage import SecretStorageService
from connector_worker.utils.secrets import generate_password, generate_username
from connector_worker.utils.users import get_user_login_from_email


class BaseDBProvider(BaseProvider, ABC):
    password_length: int = 32

    async def create_user(self, access_request: AccessRequest):
        # 1. Получаем креды к бд и проверяем
        db_config = await self.get_connection_config(
            access_request.project_name,
            access_request.resource_type,
            access_request.resource_name,
        )

        if not await self.test_connection(db_config):
            raise ResourceNotAvailableException(
                f'{access_request.resource_type} {access_request.resource_name} is not available. Check credentials.'
            )

        # 2. Генерируем креды
        user_login = get_user_login_from_email(access_request.requester_login_email)

        username = generate_username(prefix=f'{user_login}_{self.resource_type.lower()}')
        password = generate_password(length=self.password_length)

        # 3. Высчитываем, когда должен закончится доступ
        expire_at = self._calculate_expiry(access_request.ttl_minutes)

        # 4. Создаем пользователя в БД
        await self.create_db_user(username, password, db_config)

        # 5. В случае успеха, сохраняем информацию об этом в secret service
        await self.save_user_access(
            access_request,
            username,
            password,
            expire_at,
        )

    async def revoke_access(self, deprovision_request: DeprovisionRequest) -> bool:
        # 1. Получаем креды к бд и проверяем
        db_config = await self.get_connection_config(
            deprovision_request.project_name,
            deprovision_request.resource_type,
            deprovision_request.resource_name,
        )

        if not await self.test_connection(db_config):
            raise ResourceNotAvailableException(
                f'{deprovision_request.resource_type} {deprovision_request.resource_name} is not available. Check credentials.'
            )

        # 2. Получаем креды пользователя
        user_resource_username = await self.get_user_access(deprovision_request)
        if not user_resource_username:
            raise ResourceUserConfigNotFound(
                f'Not found config for: {deprovision_request.resource_type} {deprovision_request.resource_name}'
            )

        # 3. Удаляем пользвателя из бд
        await self.delete_db_user(user_resource_username, db_config)

        # 4. Удаляем запись о доступе из хранилища
        await SecretStorageService().delete_user_access(
            deprovision_request.project_name,
            deprovision_request.resource_type,
            deprovision_request.resource_name,
            str(deprovision_request.requester_uuid),
        )

    async def save_user_access(
        self,
        access_request: AccessRequest,
        username: str,
        password: str,
        expire_at: datetime.datetime,
    ):
        await SecretStorageService().save_user_access(
            access_request.project_name,
            access_request.resource_type,
            access_request.resource_name,
            user_uuid=str(access_request.requester_uuid),
            user_access_payload={
                'username': username,
                'password': password,
            },
            expire_at=expire_at,
            metadata={
                'request_id': access_request.request_id,
            },
        )

    async def get_user_access(self, access_request: BaseAccessRequest):
        return await SecretStorageService().get_user_access_username(
            project=access_request.project_name,
            resource_type=access_request.resource_type,
            resource_name=access_request.resource_name,
            user_uuid=str(access_request.requester_uuid),
        )

    @abstractmethod
    async def get_connection_config(
        self,
        project_name: str,
        resource_type: ResourceType,
        resource_name: str,
    ) -> BaseDBConfig:
        pass

    @abstractmethod
    async def test_connection(self, db_config: BaseDBConfig) -> bool:
        pass

    @abstractmethod
    async def create_db_user(self, username: str, password: str, db_config: BaseDBConfig): ...

    @abstractmethod
    async def delete_db_user(self, username: str, db_config: BaseDBConfig): ...

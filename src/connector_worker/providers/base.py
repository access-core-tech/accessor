import datetime
from abc import ABC, abstractmethod

from connector_worker.models.access_requests import AccessRequest, DeprovisionRequest
from connector_worker.models.resources import ResourceType


class BaseProvider(ABC):
    resource_type: ResourceType

    @abstractmethod
    async def create_user(self, access_request: AccessRequest):
        """Создать временного пользователя"""
        pass

    @abstractmethod
    async def revoke_access(self, deprovision_request: DeprovisionRequest) -> bool:
        """Отозвать доступ пользователя"""
        pass

    @staticmethod
    def _calculate_expiry(ttl_minutes: int) -> datetime:
        """Рассчитать время истечения доступа"""
        return datetime.datetime.now() + datetime.timedelta(minutes=ttl_minutes)

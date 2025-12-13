from uuid import UUID

from connector_worker.models.resources import ResourceAccesses, ResourceType
from pydantic import BaseModel


class BaseAccessRequest(BaseModel):
    request_id: str
    project_name: str
    resource_type: ResourceType
    resource_name: str
    requester_uuid: UUID


class AccessRequest(BaseAccessRequest):
    """Запрос на создание доступа"""

    accesses: set[ResourceAccesses]
    requester_login_email: str
    ttl_minutes: int


class DeprovisionRequest(BaseAccessRequest): ...

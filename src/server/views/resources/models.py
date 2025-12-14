from pydantic import BaseModel, field_validator
from uuid import UUID
from typing import Optional
import json

from server.utils import validate_null_item


class ResourceItem(BaseModel):
    project_id: UUID
    resource_type: str
    name: str


class ResourceItemWithId(ResourceItem):
    id: UUID


class ResourcesListRequest(BaseModel):
    user_uuid: UUID
    project_id: UUID


class ResourcesListResponse(BaseModel):
    resources: list[ResourceItemWithId]


class ResourceItemRequest(BaseModel):
    id: UUID


class ResourceItemResponse(BaseModel):
    resource: Optional[ResourceItemWithId] = None

    @field_validator('resource', mode='before')
    @classmethod
    def _validates_nulls(cls, v):
        return validate_null_item(v)


# CREATE
class ResourceItemCreateRequest(ResourceItem):
    description: Optional[str] = None
    admin_credentials: Optional[bytes] = None  # JSON в виде bytes

    @field_validator(
        'admin_credentials',
        'description',
        mode='before',
    )
    @classmethod
    def _validates_nulls(cls, v):
        return validate_null_item(v)

    def get_admin_credentials_dict(self) -> Optional[dict]:
        if not self.admin_credentials:
            return None
        try:
            return json.loads(self.admin_credentials.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ValueError(f"Invalid admin_credentials JSON: {e}")


class ResourceItemUpdateRequest(BaseModel):
    id: UUID
    name: Optional[str] = None
    description: Optional[str] = None
    admin_credentials: Optional[bytes] = None  # JSON в виде bytes

    @field_validator(
        'name',
        'admin_credentials',
        'description',
        mode='before',
    )
    @classmethod
    def _validates_nulls(cls, v):
        return validate_null_item(v)

    def get_admin_credentials_dict(self) -> Optional[dict]:
        if not self.admin_credentials:
            return None
        try:
            return json.loads(self.admin_credentials.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ValueError(f"Invalid admin_credentials JSON: {e}")


# DELETE
class ResourceDeleteRequest(BaseModel):
    id: UUID

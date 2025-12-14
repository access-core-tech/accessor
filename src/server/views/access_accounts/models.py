from pydantic import BaseModel, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional

from server.utils import validate_null_item


class AccessAccountResponse(BaseModel):
    id: UUID
    resource_id: UUID
    resource_name: str
    resource_type: str
    project_id: UUID
    user_uuid: UUID
    access_level: str
    granted_by: UUID
    granted_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool

    @field_validator('expires_at', mode='before')
    @classmethod
    def _validates_nulls(cls, v):
        return validate_null_item(v)


# LIST
class ResourcesAccessAccountsListRequest(BaseModel):
    user_uuid: UUID
    project_id: Optional[UUID] = None

    @field_validator('project_id', mode='before')
    @classmethod
    def _validates_nulls(cls, v):
        return validate_null_item(v)


class ResourcesAccessAccountsListResponse(BaseModel):
    access_accounts: list[AccessAccountResponse]


# ITEM
class ResourceAccessAccountItemRequest(BaseModel):
    id: UUID


class ResourceAccessAccountItemResponse(BaseModel):
    access_account: Optional[AccessAccountResponse] = None

    @field_validator('access_account', mode='before')
    @classmethod
    def _validates_nulls(cls, v):
        return validate_null_item(v)

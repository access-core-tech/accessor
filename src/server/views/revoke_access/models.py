from pydantic import BaseModel, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional

from server.utils import validate_null_item


class RevokeRequestResponse(BaseModel):
    id: UUID
    access_account_id: UUID
    requester_uuid: UUID
    reason: str
    status: str  # pending, completed, failed
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime

    @field_validator('completed_at', 'error_message', mode='before')
    @classmethod
    def _validates_nulls(cls, v):
        return validate_null_item(v)


# LIST
class RevokeRequestsListRequest(BaseModel):
    user_uuid: UUID
    project_id: Optional[UUID] = None

    @field_validator('project_id', mode='before')
    @classmethod
    def _validates_nulls(cls, v):
        return validate_null_item(v)


class RevokeRequestsListResponse(BaseModel):
    revoke_requests: list[RevokeRequestResponse]


# ITEM
class RevokeRequestItemRequest(BaseModel):
    id: UUID


class RevokeRequestItemResponse(BaseModel):
    revoke_request: Optional[RevokeRequestResponse] = None

    @field_validator('revoke_request', mode='before')
    @classmethod
    def _validates_nulls(cls, v):
        return validate_null_item(v)


# REVOKE
class RevokeAccessRequest(BaseModel):
    access_account_id: UUID
    reason: str
    requester_uuid: UUID

from pydantic import BaseModel, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional

from server.utils import validate_null_item


class AccessRequestItem(BaseModel):
    resource_id: UUID
    requester_uuid: UUID
    request_name: str
    ttl_minutes: Optional[int] = None

    @field_validator('ttl_minutes', mode='before')
    @classmethod
    def _validates_nulls(cls, v):
        return validate_null_item(v)


# LIST
class AccessRequestsListRequest(BaseModel):
    user_uuid: UUID
    project_id: UUID


class AccessRequestsListResponse(BaseModel):
    access_requests: list['AccessRequestItemResponse']


class AccessRequestItemResponse(BaseModel):
    id: UUID
    resource_id: UUID
    resource_type: str
    resource_name: str
    requester_uuid: UUID
    request_name: str
    status: str  # pending, approved, denied
    ttl_minutes: Optional[int] = None
    created_at: datetime

    @field_validator('ttl_minutes', mode='before')
    @classmethod
    def _validates_nulls(cls, v):
        return validate_null_item(v)


# ITEM
class AccessRequestItemRequest(BaseModel):
    id: UUID


class AccessRequestItemSingleResponse(BaseModel):
    access_request: Optional[AccessRequestItemResponse] = None

    @field_validator('access_request', mode='before')
    @classmethod
    def _validates_nulls(cls, v):
        return validate_null_item(v)


# CREATE
class AccessRequestCreateRequest(AccessRequestItem):
    pass


# STATUS UPDATE
class AccessRequestStatusUpdateRequest(BaseModel):
    id: UUID
    reviewer_uuid: UUID
    comment: Optional[str] = None

    @field_validator('comment', mode='before')
    @classmethod
    def _validates_nulls(cls, v):
        return validate_null_item(v)


class AccessRequestStatusUpdateResponse(BaseModel):
    access_request: Optional[AccessRequestItemResponse] = None

    @field_validator('access_request', mode='before')
    @classmethod
    def _validates_nulls(cls, v):
        return validate_null_item(v)

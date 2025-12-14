from pydantic import BaseModel
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, List
from enum import StrEnum


class AccessRequestStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"


class AccessRequestItem(BaseModel):
    resource_id: UUID
    requester_uuid: UUID
    request_name: str
    ttl_minutes: Optional[int] = None


# LIST
class AccessRequestsListRequest(BaseModel):
    user_uuid: UUID
    project_name: str


class AccessRequestItemResponse(BaseModel):
    id: UUID
    resource_id: UUID
    resource_type: str
    resource_name: str
    requester_uuid: UUID
    request_name: str
    status: str
    ttl_minutes: Optional[int] = None
    created_at: datetime


class AccessRequestsListResponse(BaseModel):
    access_requests: List[AccessRequestItemResponse]


# ITEM
class AccessRequestItemRequest(BaseModel):
    id: UUID


class AccessRequestItemSingleResponse(BaseModel):
    access_request: Optional[AccessRequestItemResponse]


# CREATE
class AccessRequestCreateRequest(AccessRequestItem):
    pass


# STATUS UPDATE
class AccessRequestStatusUpdateRequest(BaseModel):
    id: UUID
    reviewer_uuid: UUID
    comment: Optional[str] = None


class AccessRequestStatusUpdateResponse(BaseModel):
    access_request: Optional[AccessRequestItemResponse]


class AccessRequestView:
    mock_access_request = {
        UUID('da47b870-d8bc-11f0-b558-0800200c9a66'): AccessRequestItemResponse(
            id=UUID('da47b870-d8bc-11f0-b558-0800200c9a66'),
            resource_id=UUID('da47b870-d8bc-11f0-b558-0800200c9a66'),
            resource_type='postgresql',
            resource_name='postgresql-main',
            requester_uuid=UUID('fa47b870-d8bc-11f0-b558-0800200c9a66'),
            request_name='Access to production DB',
            status=AccessRequestStatus.PENDING,
            ttl_minutes=60,
            created_at=datetime(2024, 1, 15, 10, 30, 0),
        ),
        UUID('da47b871-d8bc-11f0-b558-0800200c9a66'): AccessRequestItemResponse(
            id=UUID('da47b871-d8bc-11f0-b558-0800200c9a66'),
            resource_id=UUID('da47b871-d8bc-11f0-b558-0800200c9a66'),
            resource_type='mariadb',
            resource_name='mariadb-main',
            requester_uuid=UUID('fa47b871-d8bc-11f0-b558-0800200c9a66'),
            request_name='Database maintenance',
            status=AccessRequestStatus.APPROVED,
            ttl_minutes=120,
            created_at=datetime(2024, 1, 14, 14, 15, 0),
        ),
    }

    async def get_accesses_request(self, request: AccessRequestsListRequest) -> AccessRequestsListResponse:
        access_requests = list(self.mock_access_request.values())
        return AccessRequestsListResponse(access_requests=access_requests)

    async def get_access_request(self, request: AccessRequestItemRequest) -> AccessRequestItemSingleResponse:
        item = self.mock_access_request.get(request.id)
        return AccessRequestItemSingleResponse(access_request=item)

    async def create_access_request(self, request: AccessRequestCreateRequest) -> AccessRequestItemSingleResponse:
        item_id = uuid4()
        resource_type = "postgresql"
        resource_name = f"resource-{request.resource_id}"

        new_item = AccessRequestItemResponse(
            id=item_id,
            resource_id=request.resource_id,
            resource_type=resource_type,
            resource_name=resource_name,
            requester_uuid=request.requester_uuid,
            request_name=request.request_name,
            status=AccessRequestStatus.PENDING,
            ttl_minutes=request.ttl_minutes,
            created_at=datetime.now(),
        )

        self.mock_access_request[item_id] = new_item
        return AccessRequestItemSingleResponse(access_request=new_item)

    async def approve_access(self, request: AccessRequestStatusUpdateRequest) -> AccessRequestStatusUpdateResponse:
        item = self.mock_access_request.get(request.id)
        if item and item.status == AccessRequestStatus.PENDING:
            updated_data = item.model_dump()
            updated_data['status'] = AccessRequestStatus.APPROVED
            updated_item = AccessRequestItemResponse(**updated_data)
            self.mock_access_request[request.id] = updated_item

            return AccessRequestStatusUpdateResponse(access_request=updated_item)
        return AccessRequestStatusUpdateResponse(access_request=None)

    async def deny_access(self, request: AccessRequestStatusUpdateRequest) -> AccessRequestStatusUpdateResponse:
        item = self.mock_access_request.get(request.id)
        if item and item.status == AccessRequestStatus.PENDING:
            updated_data = item.model_dump()
            updated_data['status'] = AccessRequestStatus.DENIED
            updated_item = AccessRequestItemResponse(**updated_data)
            self.mock_access_request[request.id] = updated_item

            return AccessRequestStatusUpdateResponse(access_request=updated_item)
        return AccessRequestStatusUpdateResponse(access_request=None)


access_request_view = AccessRequestView()

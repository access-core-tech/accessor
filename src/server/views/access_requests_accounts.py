from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from enum import StrEnum


class AccessLevel(StrEnum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


# LIST
class ResourcesAccessAccountsListRequest(BaseModel):
    user_uuid: UUID
    project_name: Optional[str] = None


class ResourceAccessAccountResponse(BaseModel):
    id: UUID
    resource_id: UUID
    resource_name: str
    resource_type: str
    project_name: str
    user_uuid: UUID
    user_name: str
    access_level: str
    granted_by: UUID
    granted_at: datetime
    expires_at: Optional[datetime] = None
    ttl_minutes: Optional[int] = None


class ResourcesAccessAccountsListResponse(BaseModel):
    access_accounts: List[ResourceAccessAccountResponse]


# ITEM
class ResourceAccessAccountItemRequest(BaseModel):
    id: UUID


class ResourceAccessAccountItemResponse(BaseModel):
    access_account: Optional[ResourceAccessAccountResponse]


class ResourcesAccessAccountsView:
    mock_resources_access_accounts = {
        UUID('ea47b870-d8bc-11f0-b558-0800200c9a66'): ResourceAccessAccountResponse(
            id=UUID('ea47b870-d8bc-11f0-b558-0800200c9a66'),
            resource_id=UUID('da47b870-d8bc-11f0-b558-0800200c9a66'),
            resource_name='postgresql-main',
            resource_type='postgresql',
            project_name='accessor',
            user_uuid=UUID('fa47b870-d8bc-11f0-b558-0800200c9a66'),
            user_name='Иван Петров',
            access_level=AccessLevel.ADMIN,
            granted_by=UUID('aa47b870-d8bc-11f0-b558-0800200c9a66'),
            granted_at=datetime(2024, 1, 10, 9, 0, 0),
            expires_at=datetime(2024, 12, 31, 23, 59, 59),
            ttl_minutes=None,
        ),
        UUID('ea47b871-d8bc-11f0-b558-0800200c9a66'): ResourceAccessAccountResponse(
            id=UUID('ea47b871-d8bc-11f0-b558-0800200c9a66'),
            resource_id=UUID('da47b870-d8bc-11f0-b558-0800200c9a66'),
            resource_name='postgresql-main',
            resource_type='postgresql',
            project_name='accessor',
            user_uuid=UUID('fa47b871-d8bc-11f0-b558-0800200c9a66'),
            user_name='Мария Сидорова',
            access_level=AccessLevel.READ,
            granted_by=UUID('aa47b870-d8bc-11f0-b558-0800200c9a66'),
            granted_at=datetime(2024, 1, 12, 14, 30, 0),
            expires_at=datetime(2024, 1, 15, 18, 0, 0),
            ttl_minutes=4320,
        ),
    }

    async def get_resources_access_accounts(
        self, request: ResourcesAccessAccountsListRequest
    ) -> ResourcesAccessAccountsListResponse:
        all_accesses = list(self.mock_resources_access_accounts.values())

        if request.project_name:
            filtered_accesses = [access for access in all_accesses if access.project_name == request.project_name]
            return ResourcesAccessAccountsListResponse(access_accounts=filtered_accesses)

        return ResourcesAccessAccountsListResponse(access_accounts=all_accesses)

    async def get_resource_access_account(
        self, request: ResourceAccessAccountItemRequest
    ) -> ResourceAccessAccountItemResponse:
        item = self.mock_resources_access_accounts.get(request.id)
        return ResourceAccessAccountItemResponse(access_account=item)


resource_access_accounts_view = ResourcesAccessAccountsView()

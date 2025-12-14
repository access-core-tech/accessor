from pydantic import BaseModel
from uuid import UUID, uuid4
from datetime import datetime
from typing import List, Optional
from enum import StrEnum


class RevokeRequestStatus(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"


# LIST
class RevokeRequestsListRequest(BaseModel):
    user_uuid: UUID
    project_name: Optional[str] = None


class RevokeRequestResponse(BaseModel):
    id: UUID
    access_account_id: UUID
    resource_id: UUID
    resource_name: str
    resource_type: str
    project_name: str
    user_uuid: UUID
    user_name: str
    revoked_by: UUID
    revoked_by_name: str
    reason: str
    status: str
    access_level: str
    revoked_at: datetime
    comment: Optional[str] = None


class RevokeRequestsListResponse(BaseModel):
    revoke_requests: List[RevokeRequestResponse]


# ITEM
class RevokeRequestItemRequest(BaseModel):
    id: UUID


class RevokeRequestItemResponse(BaseModel):
    revoke_request: Optional[RevokeRequestResponse]


# REVOKE
class RevokeAccessRequest(BaseModel):
    access_account_id: UUID
    reason: str
    revoked_by: UUID
    comment: Optional[str] = None


class RevokeAccessResponse(BaseModel):
    revoke_request: RevokeRequestResponse


class RevokeRequestsView:
    mock_revoke_requests = {
        UUID('fb47b870-d8bc-11f0-b558-0800200c9a66'): RevokeRequestResponse(
            id=UUID('fb47b870-d8bc-11f0-b558-0800200c9a66'),
            access_account_id=UUID('ea47b871-d8bc-11f0-b558-0800200c9a66'),
            resource_id=UUID('da47b870-d8bc-11f0-b558-0800200c9a66'),
            resource_name='postgresql-main',
            resource_type='postgresql',
            project_name='accessor',
            user_uuid=UUID('fa47b871-d8bc-11f0-b558-0800200c9a66'),
            user_name='Мария Сидорова',
            revoked_by=UUID('aa47b870-d8bc-11f0-b558-0800200c9a66'),
            revoked_by_name='Администратор Системы',
            reason='Временный доступ истёк',
            status=RevokeRequestStatus.COMPLETED,
            access_level='read',
            revoked_at=datetime(2024, 1, 15, 10, 0, 0),
            comment='Доступ успешно отозван',
        ),
        UUID('fb47b871-d8bc-11f0-b558-0800200c9a66'): RevokeRequestResponse(
            id=UUID('fb47b871-d8bc-11f0-b558-0800200c9a66'),
            access_account_id=UUID('ea47b872-d8bc-11f0-b558-0800200c9a66'),
            resource_id=UUID('da47b871-d8bc-11f0-b558-0800200c9a66'),
            resource_name='mariadb-main',
            resource_type='mariadb',
            project_name='accessor',
            user_uuid=UUID('fa47b872-d8bc-11f0-b558-0800200c9a66'),
            user_name='Алексей Иванов',
            revoked_by=UUID('fa47b870-d8bc-11f0-b558-0800200c9a66'),
            revoked_by_name='Иван Петров',
            reason='Сотрудник переведён в другой отдел',
            status=RevokeRequestStatus.COMPLETED,
            access_level='write',
            revoked_at=datetime(2024, 1, 14, 14, 30, 0),
            comment='Доступ отозван по запросу руководителя',
        ),
    }

    async def get_revokes(self, request: RevokeRequestsListRequest) -> RevokeRequestsListResponse:
        all_requests = list(self.mock_revoke_requests.values())

        if request.project_name:
            filtered_requests = [req for req in all_requests if req.project_name == request.project_name]
            return RevokeRequestsListResponse(revoke_requests=filtered_requests)

        return RevokeRequestsListResponse(revoke_requests=all_requests)

    async def get_revoke(self, request: RevokeRequestItemRequest) -> RevokeRequestItemResponse:
        item = self.mock_revoke_requests.get(request.id)
        return RevokeRequestItemResponse(revoke_request=item)

    async def revoke_access(self, request: RevokeAccessRequest) -> RevokeAccessResponse:
        item_id = uuid4()

        access_account = self._get_mock_access_account(request.access_account_id)

        if not access_account:
            raise ValueError(f"Access account with id {request.access_account_id} not found")

        revoked_by_name = self._get_mock_user_name(request.revoked_by)

        try:
            status = RevokeRequestStatus.COMPLETED
            comment = request.comment or "Доступ успешно отозван"

        except Exception as e:
            status = RevokeRequestStatus.FAILED
            comment = f"Ошибка при отзыве: {str(e)}"

        new_revoke = RevokeRequestResponse(
            id=item_id,
            access_account_id=request.access_account_id,
            resource_id=access_account['resource_id'],
            resource_name=access_account['resource_name'],
            resource_type=access_account['resource_type'],
            project_name=access_account['project_name'],
            user_uuid=access_account['user_uuid'],
            user_name=access_account['user_name'],
            revoked_by=request.revoked_by,
            revoked_by_name=revoked_by_name,
            reason=request.reason,
            status=status,
            access_level=access_account['access_level'],
            revoked_at=datetime.now(),
            comment=comment,
        )

        self.mock_revoke_requests[item_id] = new_revoke
        return RevokeAccessResponse(revoke_request=new_revoke)

    def _get_mock_access_account(self, access_account_id: UUID) -> dict | None:
        mock_access_accounts = {
            UUID('ea47b870-d8bc-11f0-b558-0800200c9a66'): {
                'resource_id': UUID('da47b870-d8bc-11f0-b558-0800200c9a66'),
                'resource_name': 'postgresql-main',
                'resource_type': 'postgresql',
                'project_name': 'accessor',
                'user_uuid': UUID('fa47b870-d8bc-11f0-b558-0800200c9a66'),
                'user_name': 'Иван Петров',
                'access_level': 'admin',
            },
            UUID('ea47b871-d8bc-11f0-b558-0800200c9a66'): {
                'resource_id': UUID('da47b870-d8bc-11f0-b558-0800200c9a66'),
                'resource_name': 'postgresql-main',
                'resource_type': 'postgresql',
                'project_name': 'accessor',
                'user_uuid': UUID('fa47b871-d8bc-11f0-b558-0800200c9a66'),
                'user_name': 'Мария Сидорова',
                'access_level': 'read',
            },
        }
        return mock_access_accounts.get(access_account_id)

    def _get_mock_user_name(self, user_uuid: UUID) -> str:
        mock_users = {
            UUID('fa47b870-d8bc-11f0-b558-0800200c9a66'): 'Иван Петров',
            UUID('fa47b871-d8bc-11f0-b558-0800200c9a66'): 'Мария Сидорова',
            UUID('aa47b870-d8bc-11f0-b558-0800200c9a66'): 'Администратор Системы',
        }
        return mock_users.get(user_uuid, 'Неизвестный пользователь')


revoke_requests_view = RevokeRequestsView()

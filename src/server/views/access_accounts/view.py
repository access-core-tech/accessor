from uuid import UUID

from server.database import get_db
from server.repositories.access_account import AccessAccountRepo
from server.repositories.resources import ResourceRepo

from server.views.access_accounts.models import (
    ResourcesAccessAccountsListRequest,
    ResourcesAccessAccountsListResponse,
    ResourceAccessAccountItemRequest,
    ResourceAccessAccountItemResponse,
    AccessAccountResponse,
)


class ResourcesAccessAccountsView:
    def __init__(self):
        pass

    async def get_resources_access_accounts(
        self, request: ResourcesAccessAccountsListRequest
    ) -> ResourcesAccessAccountsListResponse:
        async with get_db() as session:
            resource_repo = ResourceRepo(session)
            access_account_repo = AccessAccountRepo(session)

            if request.project_id:
                access_accounts = await access_account_repo.list_active_by_project(request.project_id)
            else:
                access_accounts = await self._get_all_active_access_accounts(access_account_repo)

            responses = []
            for account in access_accounts:
                resource = await resource_repo.get_by_id(account.resource_id)
                if not resource:
                    continue

                response = AccessAccountResponse(
                    id=account.id,
                    resource_id=account.resource_id,
                    resource_name=resource.name,
                    resource_type=resource.resource_type,
                    project_id=resource.project_id,
                    user_uuid=account.user_uuid,
                    access_level=account.access_level,
                    granted_by=account.granted_by,
                    granted_at=account.granted_at,
                    expires_at=account.expires_at,
                    is_active=account.is_active,
                )
                responses.append(response)

            return ResourcesAccessAccountsListResponse(access_accounts=responses)

    async def get_resource_access_account(
        self, request: ResourceAccessAccountItemRequest
    ) -> ResourceAccessAccountItemResponse:
        async with get_db() as session:
            resource_repo = ResourceRepo(session)
            access_account_repo = AccessAccountRepo(session)

            account = await access_account_repo.get_by_id(request.id)
            if not account:
                return ResourceAccessAccountItemResponse(access_account=None)

            resource = await resource_repo.get_by_id(account.resource_id)
            if not resource:
                return ResourceAccessAccountItemResponse(access_account=None)

            response = AccessAccountResponse(
                id=account.id,
                resource_id=account.resource_id,
                resource_name=resource.name,
                resource_type=resource.resource_type,
                project_id=resource.project_id,
                user_uuid=account.user_uuid,
                access_level=account.access_level,
                granted_by=account.granted_by,
                granted_at=account.granted_at,
                expires_at=account.expires_at,
                is_active=account.is_active,
            )

            return ResourceAccessAccountItemResponse(access_account=response)

    async def _get_all_active_access_accounts(self, access_account_repo: AccessAccountRepo):
        access_accounts = []
        all_accounts = await access_account_repo.list_by_user(UUID(int=0))
        access_accounts = [acc for acc in all_accounts if acc.is_active]
        return access_accounts


resource_access_accounts_view = ResourcesAccessAccountsView()

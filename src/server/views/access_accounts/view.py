import base64
import json
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
    AccessAccountCredentialsRequest,
    AccessAccountCredentialsResponse,
)
from services.secret_service import SecretStoreClient


class ResourcesAccessAccountsView:
    def __init__(self):
        pass

    def _get_user_secret_path(
        self, resource_type: str, resource_name: str, project_id: UUID, user_uuid: UUID
    ) -> list[str]:
        """Путь к user секрету в SecretStore"""
        return [
            str(project_id),
            resource_type,
            resource_name,
            str(user_uuid),
            'config',
        ]

    async def get_account_credentials(
        self, request: AccessAccountCredentialsRequest
    ) -> AccessAccountCredentialsResponse:
        async with get_db() as session:
            resource_repo = ResourceRepo(session)
            access_account_repo = AccessAccountRepo(session)

            access_account = await access_account_repo.get_by_id(request.id)
            if not access_account:
                return AccessAccountCredentialsResponse(credentials=None)

            if not access_account.is_active:
                return AccessAccountCredentialsResponse(credentials=None)

            resource = await resource_repo.get_by_id(access_account.resource_id)
            if not resource:
                return AccessAccountCredentialsResponse(credentials=None)

            secret_client = SecretStoreClient()

            async with secret_client as client:
                secret_path = self._get_user_secret_path(
                    resource_type=resource.resource_type,
                    resource_name=resource.name,
                    project_id=resource.project_id,
                    user_uuid=access_account.user_uuid,
                )

                secret = await secret_client.get_secret(path=secret_path)
                if not secret or not secret.json_value:
                    return AccessAccountCredentialsResponse(credentials=None)

                json_str = json.dumps(secret.json_value, ensure_ascii=False)
                base64_bytes = base64.b64encode(json_str.encode('utf-8'))
                base64_str = base64_bytes.decode('utf-8')

                return AccessAccountCredentialsResponse(credentials=base64_str)

    async def get_resources_access_accounts(
        self, request: ResourcesAccessAccountsListRequest
    ) -> ResourcesAccessAccountsListResponse:
        async with get_db() as session:
            resource_repo = ResourceRepo(session)
            access_account_repo = AccessAccountRepo(session)

            if request.project_id:
                access_accounts = await access_account_repo.list_active_by_project(request.project_id)
            else:
                access_accounts = await self._get_all_active_access_accounts(access_account_repo, request.user_uuid)

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

    async def _get_all_active_access_accounts(self, access_account_repo: AccessAccountRepo, user_uuid: UUID):
        access_accounts = []
        all_accounts = await access_account_repo.list_by_user(user_uuid)
        access_accounts = [acc for acc in all_accounts if acc.is_active]
        return access_accounts


resource_access_accounts_view = ResourcesAccessAccountsView()

from uuid import UUID
from datetime import datetime, UTC

from server.database import get_db
from server.repositories.resources import ResourceRepo
from services.secret_service.client import SecretStoreClient
from server.views.resources.models import (
    ResourceItemWithId,
    ResourcesListRequest,
    ResourcesListResponse,
    ResourceItemRequest,
    ResourceItemResponse,
    ResourceItemCreateRequest,
    ResourceItemUpdateRequest,
    ResourceDeleteRequest,
)


class ResourceView:
    def __init__(self):
        pass

    def _get_admin_secret_path(self, resource_type: str, name: str, project_id: UUID) -> list[str]:
        return [str(project_id), resource_type, name, "_admin"]

    async def get_resource(self, request: ResourceItemRequest) -> ResourceItemResponse:
        async with get_db() as session:
            repo = ResourceRepo(session)
            resource = await repo.get_by_id(request.id)

            if not resource:
                return ResourceItemResponse(resource=None)

            resource_item = ResourceItemWithId(
                id=resource.id,
                project_id=resource.project_id,
                resource_type=resource.resource_type,
                name=resource.name,
            )

            return ResourceItemResponse(resource=resource_item)

    async def get_resources(self, request: ResourcesListRequest) -> ResourcesListResponse:
        async with get_db() as session:
            repo = ResourceRepo(session)
            resources = await repo.list_by_project(request.project_id)

            resource_items = [
                ResourceItemWithId(id=r.id, project_id=r.project_id, resource_type=r.resource_type, name=r.name)
                for r in resources
            ]

            return ResourcesListResponse(resources=resource_items)

    async def create_resource(self, request: ResourceItemCreateRequest) -> ResourceItemResponse:
        from services.secret_service import SecretStoreClient

        async with get_db() as session:
            secret_client = None
            try:
                repo = ResourceRepo(session)

                existing = await repo.get_by_project_and_name(request.project_id, request.name)
                if existing:
                    raise ValueError(f"Resource with name '{request.name}' already exists in project")

                admin_credentials_dict = None
                if request.admin_credentials:
                    admin_credentials_dict = request.get_admin_credentials_dict()

                if admin_credentials_dict:
                    secret_client = SecretStoreClient()
                    await secret_client.connect()

                    secret_path = self._get_admin_secret_path(request.resource_type, request.name, request.project_id)

                    await secret_client.put_secret(
                        path=secret_path,
                        value=admin_credentials_dict,
                        metadata={"created_at": datetime.now(UTC).isoformat(), "resource_type": request.resource_type},
                    )

                resource = await repo.create(
                    project_id=request.project_id,
                    resource_type=request.resource_type,
                    name=request.name,
                    description=request.description,
                )

                resource_item = ResourceItemWithId(
                    id=resource.id,
                    project_id=resource.project_id,
                    resource_type=resource.resource_type,
                    name=resource.name,
                )

                return ResourceItemResponse(resource=resource_item)

            finally:
                if secret_client:
                    await secret_client.disconnect()

    async def update_resource(self, request: ResourceItemUpdateRequest) -> ResourceItemResponse:
        from services.secret_service import SecretStoreClient

        async with get_db() as session:
            secret_client = None
            try:
                repo = ResourceRepo(session)
                resource = await repo.get_by_id(request.id)
                if not resource:
                    raise ValueError(f"Resource with id {request.id} not found")

                if request.name and request.name != resource.name:
                    existing = await repo.get_by_project_and_name(resource.project_id, request.name)
                    if existing:
                        raise ValueError(f"Resource with name '{request.name}' already exists in project")

                admin_credentials_dict = None
                if request.admin_credentials is not None:
                    admin_credentials_dict = request.get_admin_credentials_dict()

                if admin_credentials_dict is not None:
                    secret_client = SecretStoreClient()
                    await secret_client.connect()

                    secret_name = request.name if request.name else resource.name
                    secret_path = self._get_admin_secret_path(resource.resource_type, secret_name, resource.project_id)

                    await secret_client.put_secret(
                        path=secret_path,
                        value=admin_credentials_dict,
                        metadata={"updated_at": datetime.now(UTC).isoformat(), "resource_type": resource.resource_type},
                    )

                update_data = {}
                if request.name is not None:
                    update_data["name"] = request.name
                if request.description is not None:
                    update_data["description"] = request.description

                if update_data:
                    await repo.update(request.id, **update_data)

                updated = await repo.get_by_id(request.id)
                resource_item = ResourceItemWithId(
                    id=updated.id, project_id=updated.project_id, resource_type=updated.resource_type, name=updated.name
                )

                return ResourceItemResponse(resource=resource_item)

            finally:
                if secret_client:
                    await secret_client.disconnect()

    async def delete_resource(self, request: ResourceDeleteRequest) -> None:

        async with get_db() as session:
            secret_client = None
            try:
                resource_repo = ResourceRepo(session)

                resource = await resource_repo.get_by_id(request.id)
                if not resource:
                    raise ValueError(f"Resource with id {request.id} not found")

                secret_client = SecretStoreClient()
                await secret_client.connect()

                admin_secret_path = self._get_admin_secret_path(
                    resource.resource_type, resource.name, resource.project_id
                )
                await secret_client.delete_secret(path=admin_secret_path)

                deleted = await resource_repo.delete(request.id)
                if not deleted:
                    raise ValueError(f"Resource with id {request.id} not found")

            finally:
                if secret_client:
                    await secret_client.disconnect()


resource_view = ResourceView()

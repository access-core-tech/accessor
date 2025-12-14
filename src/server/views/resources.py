from pydantic import BaseModel
from uuid import UUID, uuid4
from typing import Optional, List
from fast_grpc import Empty


class ResourceItem(BaseModel):
    project_name: str
    resource_type: str
    name: str


# LIST
class ResourcesListRequest(BaseModel):
    user_uuid: UUID
    project_name: str


class ResourceItemWithId(ResourceItem):
    id: UUID


class ResourcesListResponse(BaseModel):
    resources: List[ResourceItemWithId]


# ITEM
class ResourceItemRequest(BaseModel):
    id: UUID


class ResourceItemResponse(BaseModel):
    resource: Optional[ResourceItemWithId]


# DELETE
class ResourceDeleteRequest(BaseModel):
    id: UUID


class ResourcesView:
    mock_resource = {
        UUID('da47b870-d8bc-11f0-b558-0800200c9a66'): ResourceItemWithId(
            id=UUID('da47b870-d8bc-11f0-b558-0800200c9a66'),
            project_name='accessor',
            resource_type='postgresql',
            name='postgresql-main',
        ),
        UUID('da47b871-d8bc-11f0-b558-0800200c9a66'): ResourceItemWithId(
            id=UUID('da47b871-d8bc-11f0-b558-0800200c9a66'),
            project_name='accessor',
            resource_type='mariadb',
            name='mariadb-main',
        ),
    }

    async def get_resources(self, request: ResourcesListRequest) -> ResourcesListResponse:
        resources_list = list(self.mock_resource.values())
        return ResourcesListResponse(resources=resources_list)

    async def get_resource(self, request: ResourceItemRequest) -> ResourceItemResponse:
        item = self.mock_resource.get(request.id)
        return ResourceItemResponse(resource=item)

    async def create_resource(self, request: ResourceItem) -> ResourceItemResponse:
        item_id = uuid4()
        new_item = ResourceItemWithId(
            id=item_id,
            project_name=request.project_name,
            resource_type=request.resource_type,
            name=request.name,
        )
        self.mock_resource[item_id] = new_item
        return ResourceItemResponse(resource=new_item)

    async def delete_resource(self, request: ResourceDeleteRequest) -> Empty:
        if request.id in self.mock_resource:
            self.mock_resource.pop(request.id)

        return Empty()


resource_view = ResourcesView()

from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from server.tables import Resource


class ResourceRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, project_id: UUID, resource_type: str, name: str, description: str | None = None) -> Resource:
        resource = Resource(project_id=project_id, resource_type=resource_type, name=name, description=description)
        self.session.add(resource)
        await self.session.flush()
        return resource

    async def get_by_id(self, resource_id: UUID) -> Resource | None:
        result = await self.session.execute(select(Resource).where(Resource.id == resource_id))
        return result.scalar_one_or_none()

    async def get_by_project_and_name(self, project_id: UUID, name: str) -> Resource | None:
        result = await self.session.execute(
            select(Resource).where(Resource.project_id == project_id, Resource.name == name)
        )
        return result.scalar_one_or_none()

    async def list_by_project(self, project_id: UUID) -> list[Resource]:
        result = await self.session.execute(
            select(Resource).where(Resource.project_id == project_id).order_by(Resource.created_at.desc())
        )
        return list(result.scalars().all())

    async def update(self, resource_id: UUID, **kwargs) -> None:
        await self.session.execute(update(Resource).where(Resource.id == resource_id).values(**kwargs))

    async def delete(self, resource_id: UUID) -> bool:
        result = await self.session.execute(delete(Resource).where(Resource.id == resource_id))
        return result.rowcount > 0

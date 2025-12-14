from sqlalchemy import select, update, desc
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime, UTC

from server.tables import AccessRequest, Resource


class AccessRequestRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, resource_id: UUID, requester_uuid: UUID, request_name: str, ttl_minutes: int | None = None
    ) -> AccessRequest:
        access_request = AccessRequest(
            resource_id=resource_id,
            requester_uuid=requester_uuid,
            request_name=request_name,
            ttl_minutes=ttl_minutes,
            status='pending',
            created_at=datetime.now(UTC),
        )
        self.session.add(access_request)
        await self.session.flush()
        return access_request

    async def get_by_id(self, request_id: UUID) -> AccessRequest | None:
        result = await self.session.execute(select(AccessRequest).where(AccessRequest.id == request_id))
        return result.scalar_one_or_none()

    async def get_by_resource_and_user(
        self, resource_id: UUID, user_uuid: UUID, status: str = 'pending'
    ) -> AccessRequest | None:
        result = await self.session.execute(
            select(AccessRequest).where(
                AccessRequest.resource_id == resource_id,
                AccessRequest.requester_uuid == user_uuid,
                AccessRequest.status == status,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_project(self, project_id: UUID) -> list[AccessRequest]:
        result = await self.session.execute(
            select(AccessRequest)
            .join(Resource, AccessRequest.resource_id == Resource.id)
            .where(Resource.project_id == project_id)
            .order_by(desc(AccessRequest.created_at))
        )
        return list(result.scalars().all())

    async def list_by_requester(self, requester_uuid: UUID) -> list[AccessRequest]:
        result = await self.session.execute(
            select(AccessRequest)
            .where(AccessRequest.requester_uuid == requester_uuid)
            .order_by(desc(AccessRequest.created_at))
        )
        return list(result.scalars().all())

    async def list_pending_by_resource(self, resource_id: UUID) -> list[AccessRequest]:
        result = await self.session.execute(
            select(AccessRequest)
            .where(AccessRequest.resource_id == resource_id, AccessRequest.status == 'pending')
            .order_by(AccessRequest.created_at)
        )
        return list(result.scalars().all())

    async def approve(self, request_id: UUID, reviewer_uuid: UUID, comment: str | None = None) -> AccessRequest:
        await self.session.execute(
            update(AccessRequest)
            .where(AccessRequest.id == request_id)
            .values(
                status='approved', reviewer_uuid=reviewer_uuid, review_comment=comment, reviewed_at=datetime.now(UTC)
            )
        )
        return await self.get_by_id(request_id)

    async def deny(self, request_id: UUID, reviewer_uuid: UUID, comment: str | None = None) -> AccessRequest:
        await self.session.execute(
            update(AccessRequest)
            .where(AccessRequest.id == request_id)
            .values(status='denied', reviewer_uuid=reviewer_uuid, review_comment=comment, reviewed_at=datetime.now(UTC))
        )
        return await self.get_by_id(request_id)

    async def update_ttl(self, request_id: UUID, ttl_minutes: int | None) -> AccessRequest:
        await self.session.execute(
            update(AccessRequest).where(AccessRequest.id == request_id).values(ttl_minutes=ttl_minutes)
        )
        return await self.get_by_id(request_id)

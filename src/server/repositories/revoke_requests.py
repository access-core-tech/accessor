from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime, UTC

from server.tables import RevokeRequest, AccessAccount, Resource


class RevokeRequestRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        access_account_id: UUID,
        requester_uuid: UUID,
        reason: str,
    ) -> RevokeRequest:
        """Создать запрос на отзыв"""
        revoke_request = RevokeRequest(
            access_account_id=access_account_id,
            requester_uuid=requester_uuid,
            reason=reason,
            status='pending',
            created_at=datetime.now(UTC),
        )
        self.session.add(revoke_request)
        await self.session.flush()
        return revoke_request

    async def get_by_id(self, request_id: UUID) -> RevokeRequest | None:
        """Получить запрос на отзыв по ID"""
        result = await self.session.execute(select(RevokeRequest).where(RevokeRequest.id == request_id))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[RevokeRequest]:
        """Получить все запросы на отзыв"""
        from sqlalchemy import desc

        result = await self.session.execute(select(RevokeRequest).order_by(desc(RevokeRequest.created_at)))
        return list(result.scalars().all())

    async def list_by_project(self, project_id: UUID) -> list[RevokeRequest]:
        """Получить запросы на отзыв по проекту"""
        from sqlalchemy import desc

        result = await self.session.execute(
            select(RevokeRequest)
            .join(AccessAccount, RevokeRequest.access_account_id == AccessAccount.id)
            .join(Resource, AccessAccount.resource_id == Resource.id)
            .where(Resource.project_id == project_id)
            .order_by(desc(RevokeRequest.created_at))
        )
        return list(result.scalars().all())

    async def complete(self, request_id: UUID, error_message: str | None = None) -> RevokeRequest:
        """Завершить запрос на отзыв"""
        from sqlalchemy import update

        status = 'completed' if not error_message else 'failed'

        await self.session.execute(
            update(RevokeRequest)
            .where(RevokeRequest.id == request_id)
            .values(status=status, completed_at=datetime.now(UTC), error_message=error_message)
        )

        return await self.get_by_id(request_id)

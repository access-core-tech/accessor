from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from server.tables import Resource, AccessAccount, AccessRequest, RevokeRequest, EventOutbox


class ResourceRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, project_id: UUID, resource_type: str, name: str, description: Optional[str] = None
    ) -> Resource:
        resource = Resource(project_id=project_id, resource_type=resource_type, name=name, description=description)
        self.session.add(resource)
        await self.session.flush()
        return resource

    async def get_by_id(self, resource_id: UUID) -> Optional[Resource]:
        result = await self.session.execute(select(Resource).where(Resource.id == resource_id))
        return result.scalar_one_or_none()

    async def get_by_project_and_name(self, project_id: UUID, name: str) -> Optional[Resource]:
        result = await self.session.execute(
            select(Resource).where(Resource.project_id == project_id, Resource.name == name)
        )
        return result.scalar_one_or_none()

    async def list_by_project(self, project_id: UUID) -> List[Resource]:
        result = await self.session.execute(
            select(Resource).where(Resource.project_id == project_id).order_by(Resource.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete(self, resource_id: UUID) -> bool:
        result = await self.session.execute(delete(Resource).where(Resource.id == resource_id))
        return result.rowcount > 0


class AccessRequestRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, resource_id: UUID, requester_uuid: UUID, request_name: str, ttl_minutes: Optional[int] = None
    ) -> AccessRequest:
        request = AccessRequest(
            resource_id=resource_id, requester_uuid=requester_uuid, request_name=request_name, ttl_minutes=ttl_minutes
        )
        self.session.add(request)
        await self.session.flush()
        return request

    async def get_by_id(self, request_id: UUID) -> Optional[AccessRequest]:
        result = await self.session.execute(select(AccessRequest).where(AccessRequest.id == request_id))
        return result.scalar_one_or_none()

    async def list_by_project(self, project_id: UUID) -> List[AccessRequest]:
        result = await self.session.execute(
            select(AccessRequest)
            .join(Resource)
            .where(Resource.project_id == project_id)
            .order_by(AccessRequest.created_at.desc())
        )
        return list(result.scalars().all())

    async def approve(
        self, request_id: UUID, reviewer_uuid: UUID, comment: Optional[str] = None
    ) -> Optional[AccessRequest]:
        await self.session.execute(
            update(AccessRequest)
            .where(AccessRequest.id == request_id)
            .values(
                status='approved', reviewer_uuid=reviewer_uuid, review_comment=comment, reviewed_at=datetime.utcnow()
            )
        )
        return await self.get_by_id(request_id)

    async def deny(
        self, request_id: UUID, reviewer_uuid: UUID, comment: Optional[str] = None
    ) -> Optional[AccessRequest]:
        await self.session.execute(
            update(AccessRequest)
            .where(AccessRequest.id == request_id)
            .values(status='denied', reviewer_uuid=reviewer_uuid, review_comment=comment, reviewed_at=datetime.utcnow())
        )
        return await self.get_by_id(request_id)


class AccessAccountRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        resource_id: UUID,
        user_uuid: UUID,
        access_level: str,
        granted_by: UUID,
        access_request_id: Optional[UUID] = None,
        expires_at: Optional[datetime] = None,
    ) -> AccessAccount:
        account = AccessAccount(
            resource_id=resource_id,
            user_uuid=user_uuid,
            access_level=access_level,
            granted_by=granted_by,
            access_request_id=access_request_id,
            expires_at=expires_at,
        )
        self.session.add(account)
        await self.session.flush()
        return account

    async def get_by_id(self, account_id: UUID) -> Optional[AccessAccount]:
        result = await self.session.execute(select(AccessAccount).where(AccessAccount.id == account_id))
        return result.scalar_one_or_none()

    async def get_by_resource_and_user(self, resource_id: UUID, user_uuid: UUID) -> Optional[AccessAccount]:
        result = await self.session.execute(
            select(AccessAccount).where(
                AccessAccount.resource_id == resource_id,
                AccessAccount.user_uuid == user_uuid,
                AccessAccount.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_resource(self, resource_id: UUID) -> List[AccessAccount]:
        result = await self.session.execute(
            select(AccessAccount)
            .where(AccessAccount.resource_id == resource_id, AccessAccount.is_active == True)
            .order_by(AccessAccount.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_project(self, project_id: UUID) -> List[AccessAccount]:
        result = await self.session.execute(
            select(AccessAccount)
            .join(Resource)
            .where(Resource.project_id == project_id, AccessAccount.is_active == True)
            .order_by(AccessAccount.created_at.desc())
        )
        return list(result.scalars().all())

    async def deactivate(self, account_id: UUID) -> bool:
        result = await self.session.execute(
            update(AccessAccount).where(AccessAccount.id == account_id).values(is_active=False)
        )
        return result.rowcount > 0


class RevokeRequestRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, access_account_id: UUID, requester_uuid: UUID, reason: str) -> RevokeRequest:
        request = RevokeRequest(access_account_id=access_account_id, requester_uuid=requester_uuid, reason=reason)
        self.session.add(request)
        await self.session.flush()
        return request

    async def get_by_id(self, request_id: UUID) -> Optional[RevokeRequest]:
        result = await self.session.execute(select(RevokeRequest).where(RevokeRequest.id == request_id))
        return result.scalar_one_or_none()

    async def list_all(self) -> List[RevokeRequest]:
        result = await self.session.execute(select(RevokeRequest).order_by(RevokeRequest.created_at.desc()))
        return list(result.scalars().all())

    async def complete(self, request_id: UUID, error_message: Optional[str] = None) -> Optional[RevokeRequest]:
        status = 'completed' if not error_message else 'failed'

        await self.session.execute(
            update(RevokeRequest)
            .where(RevokeRequest.id == request_id)
            .values(status=status, completed_at=datetime.utcnow(), error_message=error_message)
        )
        return await self.get_by_id(request_id)


class EventOutboxRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, event_type: str, payload: dict) -> EventOutbox:
        event = EventOutbox(event_type=event_type, payload=payload)
        self.session.add(event)
        await self.session.flush()
        return event

    async def get_pending(self, limit: int = 100) -> List[EventOutbox]:
        result = await self.session.execute(
            select(EventOutbox).where(EventOutbox.status == 'pending').order_by(EventOutbox.created_at).limit(limit)
        )
        return list(result.scalars().all())

    async def mark_sent(self, event_id: UUID) -> bool:
        result = await self.session.execute(
            update(EventOutbox).where(EventOutbox.id == event_id).values(status='sent', sent_at=datetime.utcnow())
        )
        return result.rowcount > 0

    async def mark_failed(self, event_id: UUID, error_message: str) -> bool:
        result = await self.session.execute(
            update(EventOutbox)
            .where(EventOutbox.id == event_id)
            .values(status='failed', error_message=error_message, retry_count=EventOutbox.retry_count + 1)
        )
        return result.rowcount > 0

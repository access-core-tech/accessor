from sqlalchemy import select, update, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime, UTC

from server.tables import AccessAccount, Resource


class AccessAccountRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        resource_id: UUID,
        user_uuid: UUID,
        access_level: str,
        granted_by: UUID,
        access_request_id: UUID | None = None,
        expires_at: datetime | None = None,
    ) -> AccessAccount:
        """Создать новую запись о выданном доступе"""
        access_account = AccessAccount(
            resource_id=resource_id,
            user_uuid=user_uuid,
            access_level=access_level,
            granted_by=granted_by,
            access_request_id=access_request_id,
            expires_at=expires_at,
            granted_at=datetime.now(UTC),
            is_active=True,
        )
        self.session.add(access_account)
        await self.session.flush()
        return access_account

    async def get_by_id(self, account_id: UUID) -> AccessAccount | None:
        """Получить доступ по ID"""
        result = await self.session.execute(select(AccessAccount).where(AccessAccount.id == account_id))
        return result.scalar_one_or_none()

    async def get_by_resource_and_user(self, resource_id: UUID, user_uuid: UUID) -> AccessAccount | None:
        """Получить доступ пользователя к ресурсу"""
        result = await self.session.execute(
            select(AccessAccount).where(AccessAccount.resource_id == resource_id, AccessAccount.user_uuid == user_uuid)
        )
        return result.scalar_one_or_none()

    async def get_active_by_resource_and_user(self, resource_id: UUID, user_uuid: UUID) -> AccessAccount | None:
        """Получить активный доступ пользователя к ресурсу"""
        result = await self.session.execute(
            select(AccessAccount).where(
                AccessAccount.resource_id == resource_id,
                AccessAccount.user_uuid == user_uuid,
                AccessAccount.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_resource(self, resource_id: UUID) -> list[AccessAccount]:
        result = await self.session.execute(
            select(AccessAccount)
            .where(AccessAccount.resource_id == resource_id)
            .order_by(desc(AccessAccount.granted_at))
        )
        return list(result.scalars().all())

    async def list_active_by_resource(self, resource_id: UUID) -> list[AccessAccount]:
        result = await self.session.execute(
            select(AccessAccount)
            .where(AccessAccount.resource_id == resource_id, AccessAccount.is_active == True)
            .order_by(desc(AccessAccount.granted_at))
        )
        return list(result.scalars().all())

    async def list_by_project(self, project_id: UUID) -> list[AccessAccount]:
        result = await self.session.execute(
            select(AccessAccount)
            .join(Resource, AccessAccount.resource_id == Resource.id)
            .where(Resource.project_id == project_id)
            .order_by(desc(AccessAccount.granted_at))
        )
        return list(result.scalars().all())

    async def list_active_by_project(self, project_id: UUID) -> list[AccessAccount]:
        result = await self.session.execute(
            select(AccessAccount)
            .join(Resource, AccessAccount.resource_id == Resource.id)
            .where(Resource.project_id == project_id, AccessAccount.is_active == True)
            .order_by(desc(AccessAccount.granted_at))
        )
        return list(result.scalars().all())

    async def list_by_user(self, user_uuid: UUID) -> list[AccessAccount]:
        result = await self.session.execute(
            select(AccessAccount).where(AccessAccount.user_uuid == user_uuid).order_by(desc(AccessAccount.granted_at))
        )
        return list(result.scalars().all())

    async def list_active_by_user(self, user_uuid: UUID) -> list[AccessAccount]:
        result = await self.session.execute(
            select(AccessAccount)
            .where(AccessAccount.user_uuid == user_uuid, AccessAccount.is_active == True)
            .order_by(desc(AccessAccount.granted_at))
        )
        return list(result.scalars().all())

    async def deactivate(self, account_id: UUID) -> bool:
        result = await self.session.execute(
            update(AccessAccount)
            .where(AccessAccount.id == account_id)
            .values(is_active=False, updated_at=datetime.now(UTC))
        )
        return result.rowcount > 0

    async def update_expires_at(self, account_id: UUID, expires_at: datetime | None) -> AccessAccount:
        await self.session.execute(
            update(AccessAccount)
            .where(AccessAccount.id == account_id)
            .values(expires_at=expires_at, updated_at=datetime.now(UTC))
        )
        return await self.get_by_id(account_id)

    async def check_expired(self) -> list[AccessAccount]:
        result = await self.session.execute(
            select(AccessAccount).where(
                AccessAccount.is_active == True,
                AccessAccount.expires_at.is_not(None),
                AccessAccount.expires_at <= datetime.now(UTC),
            )
        )
        return list(result.scalars().all())

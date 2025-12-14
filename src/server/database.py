from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from server.config import settings

engine = create_async_engine(settings.DATABASE_URL)


@asynccontextmanager
async def get_db():
    async with AsyncSession(engine) as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e

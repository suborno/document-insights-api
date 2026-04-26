from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import redis.asyncio as aioredis

from config import Settings

settings = Settings()

engine = create_async_engine(settings.database_url, pool_pre_ping=True)

# need expire_on_commit=False so we can read attributes after commit
# without triggering lazy loads inside the async context
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

_redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


def get_redis() -> aioredis.Redis:
    return _redis_client

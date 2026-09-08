import os

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ["DATABASE_URL"]

# seperate driver for Celery because Celery tasks are run synchronously
SYNC_DATABASE_URL = os.environ.get("SYNC_DATABSE_URL", DATABASE_URL.replace("+asyncpg", "+psycopg"))

# FastAPI Async engine
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session

# Celery Sync engine
sync_engine = create_engine(SYNC_DATABASE_URL, echo=False)
sync_session = sessionmaker(bind=sync_engine)
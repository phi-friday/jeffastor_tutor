from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import AsyncAdaptedQueuePool

from ..core.config import DATABASE_URL

engine = create_async_engine(
    DATABASE_URL, pool_size=10, poolclass=AsyncAdaptedQueuePool, pool_pre_ping=True
)

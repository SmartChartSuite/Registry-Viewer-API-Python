import os
from ..logging_config import logger, mask_url
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

def get_database_url() -> str:
    """Return the database URL.

    If the ``DATABASE_URL`` environment variable is set, it is used directly.
    Otherwise the URL is constructed from the individual PostgreSQL variables.
    """
    # Prefer explicit full URL if provided (useful for local SQLite or test DBs)
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    # Fall back to building a PostgreSQL URL from component vars
    user = os.getenv("DATABASE_USER")
    password = os.getenv("DATABASE_PASSWORD")
    host = os.getenv("DATABASE_HOST")
    name = os.getenv("DATABASE_NAME")
    if not all([user, password, host, name]):
        raise RuntimeError(
            "Database connection variables are missing. "
            "Set DATABASE_USER, DATABASE_PASSWORD, DATABASE_HOST, DATABASE_NAME, or DATABASE_URL."
        )
    return f"postgresql+asyncpg://{user}:{password}@{host}/{name}"

# Build the async engine using the composed URL
DATABASE_URL = get_database_url()

# Async engine
try:
    engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    logger.info("Async DB engine created for URL %s", mask_url(DATABASE_URL))
except Exception as exc:
    logger.exception("Failed to create async DB engine for URL %s", mask_url(DATABASE_URL))
    raise

# Async session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Base class for ORM models
Base = declarative_base()

# Dependency for FastAPI routes
async def get_async_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

def get_database_url() -> str:
    """Construct the async PostgreSQL URL from individual env vars.

    Expected vars:
        DATABASE_USER
        DATABASE_PASSWORD
        DATABASE_HOST
        DATABASE_NAME
    """
    user = os.getenv("DATABASE_USER")
    password = os.getenv("DATABASE_PASSWORD")
    host = os.getenv("DATABASE_HOST")
    name = os.getenv("DATABASE_NAME")
    if not all([user, password, host, name]):
        raise RuntimeError(
            "Database connection variables are missing. "
            "Set DATABASE_USER, DATABASE_PASSWORD, DATABASE_HOST, DATABASE_NAME."
        )
    return f"postgresql+asyncpg://{user}:{password}@{host}/{name}"

# Build the async engine using the composed URL
DATABASE_URL = get_database_url()

# Async engine
engine = create_async_engine(DATABASE_URL, echo=False, future=True)

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

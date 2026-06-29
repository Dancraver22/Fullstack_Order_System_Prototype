import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./orders.db")

# Safety Override: Supabase provides connection strings starting with 'postgres://'.
# Async SQLAlchemy requires 'postgresql+asyncpg://' to use the async driver.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

# Handle transaction mode string optimization if pooling parameters are appended
if "?sslmode=" not in DATABASE_URL and "sqlite" not in DATABASE_URL:
    # Ensures clean SSL handshake with Supabase servers
    if "?" in DATABASE_URL:
        DATABASE_URL += "&sslmode=require"
    else:
        DATABASE_URL += "?sslmode=require"

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# Sessionmaker for async sessions
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

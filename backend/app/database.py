import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Pull the live variable from your Railway Settings panel
raw_url = os.getenv("DATABASE_URL")

# 2. Fallback only if Railway's dashboard environment variable is totally blank
if not raw_url:
    # Uses port 6543 for optimized container routing
    raw_url = "postgresql://postgres:Blb60601q2w3@db.nxmxhonkzxwzfjdxjmga.supabase.co:6543/postgres?sslmode=disable"

# 3. Explicitly transform the connection protocol to use the async driver layout
if raw_url.startswith("postgresql://"):
    DATABASE_URL = raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    DATABASE_URL = raw_url

# 4. Spin up the async engine connection pool securely
engine = create_async_engine(
    DATABASE_URL, 
    echo=True,
    future=True
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
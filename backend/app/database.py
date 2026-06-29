import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Grab the variable from your Railway environment dashboard
raw_url = os.getenv("DATABASE_URL")

# 2. Complete fallback if the environment variable comes up empty
if not raw_url:
    raw_url = "postgresql://postgres:[Blb60601q2w3]@db.nxmxhonkzxwzfjdxjmga.supabase.co:5432/postgres"

# 3. Carefully swap the scheme to asyncpg while keeping the port and parameters intact
if raw_url.startswith("postgresql://"):
    DATABASE_URL = raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    DATABASE_URL = raw_url

# 4. Fire up the async connection pool engine
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
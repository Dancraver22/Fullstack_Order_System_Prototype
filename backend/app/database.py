import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Fetch your clean Railway environment variable 
raw_url = os.getenv("DATABASE_URL")

# 2. Safety Check: If it begins with postgresql://, explicitly rewrite it to use asyncpg
if raw_url and raw_url.startswith("postgresql://"):
    DATABASE_URL = raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    DATABASE_URL = raw_url

# Fallback string tracking only if environment variables are completely missing
if not DATABASE_URL:
    DATABASE_URL = "postgresql://postgres:[Blb60601q2w3]@db.nxmxhonkzxwzfjdxjmga.supabase.co:5432/postgres"

# 3. Create the asynchronous database engine safely
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
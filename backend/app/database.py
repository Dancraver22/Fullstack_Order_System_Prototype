import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Grab your database URL from Railway variables
raw_url = os.getenv("DATABASE_URL")

# 2. Hardcoded fallback (Make sure to replace this with your actual Neon string if needed)
if not raw_url:
    raw_url = "postgresql://neondb_owner:npg_Gt0Xk6iSsOYB@ep-mute-night-aopfbq6e-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# 3. Programmatically strip any trailing query parameters like ?sslmode=require
# This prevents asyncpg from throwing keyword argument errors
if "?" in raw_url:
    raw_url = raw_url.split("?")[0]

# 4. Swap out the scheme to use the asyncpg driver protocol
if raw_url.startswith("postgresql://"):
    DATABASE_URL = raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    DATABASE_URL = raw_url

# 5. Fire up the async engine passing the SSL flag explicitly to the driver arguments
engine = create_async_engine(
    DATABASE_URL, 
    echo=True,
    future=True,
    connect_args={"ssl": True}  # Neon requires SSL, this is the format asyncpg loves
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
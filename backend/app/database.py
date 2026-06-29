import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Grab your database URL from Railway variables
raw_url = os.getenv("DATABASE_URL")

# 2. FIXED: Completely clean fallback with NO passwords exposed
if not raw_url:
    raw_url = "postgresql://postgres:local_password@localhost:5432/neondb"

# 3. Strip query parameters
if "?" in raw_url:
    raw_url = raw_url.split("?")[0]

# 4. Swap out the scheme to use the asyncpg driver protocol
if raw_url.startswith("postgresql://"):
    DATABASE_URL = raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    DATABASE_URL = raw_url

# 5. Fire up the async engine
engine = create_async_engine(
    DATABASE_URL, 
    echo=True,
    future=True,
    connect_args={"ssl": True}
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
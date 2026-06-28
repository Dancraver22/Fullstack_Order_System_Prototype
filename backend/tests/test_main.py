import hmac
import hashlib
import pytest
import httpx
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Import database module first, then patch it
import app.database
app.database.DATABASE_URL = "sqlite+aiosqlite:///./test_orders.db"
app.database.engine = create_async_engine(app.database.DATABASE_URL, echo=False)
app.database.AsyncSessionLocal = sessionmaker(
    bind=app.database.engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Use distinct import name to avoid namespace conflict with the 'app' package
from app.main import app as fastapi_app
from app.database import Base
from app.models import Order

# Use the patched engine and session local in the tests
engine = app.database.engine
AsyncSessionLocal = app.database.AsyncSessionLocal

@pytest.fixture(autouse=True)
async def setup_db():
    # Setup: Create tables before each test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Teardown: Drop tables and close engine connections
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    # Remove file-based SQLite database
    if os.path.exists("test_orders.db"):
        try:
            os.remove("test_orders.db")
        except Exception:
            pass

@pytest.mark.asyncio
async def test_read_root():
    transport = httpx.ASGITransport(app=fastapi_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

@pytest.mark.asyncio
async def test_create_order_and_list():
    transport = httpx.ASGITransport(app=fastapi_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        # Check initial empty list
        response = await ac.get("/api/orders")
        assert response.status_code == 200
        assert len(response.json()) == 0

        # Create new order
        payload = {"product_name": "Test Laptop", "quantity": 2}
        response = await ac.post("/api/orders", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["product_name"] == "Test Laptop"
        assert data["quantity"] == 2
        assert data["status"] == "pending"
        order_id = data["id"]

        # Check list after creation
        response = await ac.get("/api/orders")
        assert response.status_code == 200
        orders = response.json()
        assert len(orders) == 1
        assert orders[0]["id"] == order_id

@pytest.mark.asyncio
async def test_webhook_payment_success():
    async with AsyncSessionLocal() as session:
        # Inject an order to the test DB
        order = Order(product_name="Gadget", quantity=1, status="pending")
        session.add(order)
        await session.commit()
        await session.refresh(order)
        order_id = order.id

    webhook_secret = "super_secret_webhook_key"
    payload = f'{{"order_id": {order_id}, "status": "completed"}}'.encode("utf-8")
    
    # Compute signature
    signature = hmac.new(
        key=webhook_secret.encode("utf-8"),
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()

    transport = httpx.ASGITransport(app=fastapi_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/webhooks/payments",
            content=payload,
            headers={"X-Signature": signature, "Content-Type": "application/json"}
        )
    assert response.status_code == 200
    assert response.json()["status"] == "success"

@pytest.mark.asyncio
async def test_webhook_payment_invalid_signature():
    payload = b'{"order_id": 1, "status": "completed"}'
    
    transport = httpx.ASGITransport(app=fastapi_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/webhooks/payments",
            content=payload,
            headers={"X-Signature": "invalid_sig_here", "Content-Type": "application/json"}
        )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid signature"

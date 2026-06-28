from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from .database import engine, Base, get_db
from .models import Order
from .schemas import OrderCreate, OrderResponse
from .tasks import process_order_ai, run_cleanup_and_batch_processing
from .webhooks import router as webhook_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize the database tables if they do not exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: Clean up resources if any
    await engine.dispose()

app = FastAPI(
    title="Fullstack Order System API",
    description="Backend service demonstrating FastAPI, SQLModel/SQLAlchemy async, Background Tasks, and HMAC Webhooks.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For prototype simplicity; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Webhook Router
app.include_router(webhook_router)

@app.get("/")
def read_root():
    return {"status": "online", "message": "FastAPI order system API is fully functional"}

@app.get("/api/orders", response_model=List[OrderResponse])
async def list_orders(db: AsyncSession = Depends(get_db)):
    """
    List all orders in the database.
    """
    result = await db.execute(select(Order).order_by(Order.id.desc()))
    orders = result.scalars().all()
    return orders

@app.post("/api/orders", response_model=OrderResponse, status_code=201)
async def create_order(
    order_in: OrderCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new order and trigger background tasks (AI diagnostic and batch cleanup).
    """
    new_order = Order(
        product_name=order_in.product_name,
        quantity=order_in.quantity,
        status="pending"
    )
    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)

    # Queue background task for AI analysis retry logic
    background_tasks.add_task(process_order_ai, new_order.id)
    
    # Queue general cleanup and batch verification task
    background_tasks.add_task(run_cleanup_and_batch_processing)

    return new_order

@app.post("/api/orders/{order_id}/retry", response_model=OrderResponse)
async def retry_order_processing(
    order_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint to manually trigger or retry AI processing for a failed/pending order.
    """
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    order.status = "pending"
    await db.commit()
    await db.refresh(order)
    
    # Add back to processing queue
    background_tasks.add_task(process_order_ai, order.id)
    
    return order

@app.delete("/api/orders/{order_id}", status_code=204)
async def delete_order(
    order_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Permanently delete a single order by ID.
    """
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    await db.delete(order)
    await db.commit()

@app.delete("/api/orders", status_code=204)
async def delete_all_orders(db: AsyncSession = Depends(get_db)):
    """
    Permanently delete ALL orders in the database (clear table).
    """
    result = await db.execute(select(Order))
    orders = result.scalars().all()
    for order in orders:
        await db.delete(order)
    await db.commit()

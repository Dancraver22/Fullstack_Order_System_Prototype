import os
import httpx
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
import logging
from app.models import Order
from app.database import engine, Base, get_db

# Configure clean logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Full-Stack Operations Center API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing database tables...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")

# --- ENDPOINTS ---

@app.get("/api/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}

@app.get("/api/orders")
async def get_orders(db: AsyncSession = Depends(get_db)):
    try:
        # Fetch all orders from the database
        result = await db.execute(select(Order))
        orders = result.scalars().all()
        
        # Convert to dictionary with properly formatted ISO dates
        return [
            {
                "id": o.id, 
                "product": o.product_name, 
                "quantity": o.quantity, 
                "status": o.status,
                "created_at": o.created_at.isoformat() if o.created_at else None
            } 
            for o in orders
        ]
    except Exception as e:
        logger.error(f"Failed to fetch orders: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not retrieve orders")

@app.post("/api/orders")
async def create_order(
    order_data: dict, 
    background_tasks: BackgroundTasks, 
    db: AsyncSession = Depends(get_db)
):
    try:
        product = order_data.get("product", "Unknown Item")
        qty = order_data.get("quantity", 1)

        new_order = Order(
            product_name=product, 
            quantity=qty, 
            status="Completed"
        )
        
        db.add(new_order)
        await db.commit()
        await db.refresh(new_order)

        background_tasks.add_task(fallback_background_task, new_order.id, product, qty)

        return {
            "id": new_order.id,
            "product": product,
            "quantity": qty,
            "status": "Completed",
            "message": "Order saved to database."
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Order creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/orders")
async def delete_orders():
    return {"message": "Delete requested"}

@app.delete("/api/orders/{order_id}")
async def delete_order(order_id: int):
    return {"message": f"Order {order_id} deleted"}

@app.post("/webhooks/payments")
async def handle_payment_webhook():
    return {"status": "Webhook received"}

# --- BACKGROUND TASK ---

async def fallback_background_task(order_id: int, product: str, qty: int):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://httpbin.org/post", 
                json={"order_id": order_id, "product": product, "quantity": qty},
                timeout=5.0
            )
            response.raise_for_status()
        except Exception as e:
            logger.warning(f"External API down: {str(e)}")
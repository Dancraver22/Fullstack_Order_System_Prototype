import os
import httpx
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

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

# Startup Lifespan
@app.on_event("startup")
async def startup_event():
    logger.info("Initializing database tables...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")

# Health check
@app.get("/api/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}

# --- NEW: GET route to populate your OrderTable ---
@app.get("/api/orders")
async def get_orders(db: AsyncSession = Depends(get_db)):
    try:
        # Fetching all orders, sorted by newest first
        result = await db.execute(text("SELECT * FROM orders ORDER BY id DESC"))
        # Converting rows to dicts for frontend consumption
        orders = [dict(row) for row in result.mappings()]
        return orders
    except Exception as e:
        logger.error(f"Failed to fetch orders: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not retrieve orders")

# Background task for diagnostics
async def fallback_background_task(order_id: int, product: str, qty: int):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://httpbin.org/post", 
                json={"order_id": order_id, "product": product, "quantity": qty},
                timeout=5.0
            )
            response.raise_for_status()
            logger.info("Diagnostic data successfully forwarded.")
        except Exception as e:
            logger.warning(f"External API down: {str(e)}")

# --- FIXED: POST route with correct column mapping ---
@app.post("/api/orders")
async def create_order(
    order_data: dict, 
    background_tasks: BackgroundTasks, 
    db: AsyncSession = Depends(get_db)
):
    try:
        # Use 'product_name' to match your database schema
        product_name = order_data.get("product_name", "Unknown Item")
        qty = order_data.get("quantity", 1)

        # SQL execution using 'product_name' to avoid the 500 error
        await db.execute(
            text("INSERT INTO orders (product_name, quantity, status) VALUES (:p, :q, 'pending')"),
            {"p": product_name, "q": qty}
        )
        await db.commit()
        
        # Trigger background diagnostics
        background_tasks.add_task(fallback_background_task, 0, product_name, qty)

        return {"message": "Order created successfully"}
    except Exception as e:
        await db.rollback()
        logger.error(f"Order creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
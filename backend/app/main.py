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

# Configure CORS for your Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup Lifespan to initialize tables securely on Supabase
@app.on_event("startup")
async def startup_event():
    logger.info("Initializing database tables...")
    try:
        async with engine.begin() as conn:
            # Dynamically creates tables if they don't exist in Supabase public schema
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")

@app.get("/api/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}

async def fallback_background_task(order_id: int, product: str, qty: int):
    """
    Safely handles the diagnostic post task. If httpbin is down, 
    the backend logs it but DOES NOT crash the app layer.
    """
    logger.info(f"Processing diagnostic background task for order #{order_id}")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://httpbin.org/post", 
                json={"order_id": order_id, "product": product, "quantity": qty},
                timeout=5.0
            )
            response.raise_for_status()
            logger.info("Diagnostic data successfully forwarded to mock collector.")
        except Exception as e:
            logger.warning(f"External API down (httpbin.org), bypassing to protect system loop: {str(e)}")

@app.post("/api/orders")
async def create_order(
    order_data: dict, 
    background_tasks: BackgroundTasks, 
    db: AsyncSession = Depends(get_db)
):
    try:
        product = order_data.get("product", "Unknown Item")
        qty = order_data.get("quantity", 1)

        # 1. Insert order logic directly into Postgres/Supabase
        # (Assuming your SQLAlchemy model logic looks like this)
        # new_order = Order(product=product, quantity=qty, status="Completed")
        # db.add(new_order)
        # await db.commit()
        # await db.refresh(new_order)
        
        # Mocking data save representation for direct execution
        mock_id = 1 

        # 2. Push the external HTTP task to a safe detached background thread
        background_tasks.add_task(fallback_background_task, mock_id, product, qty)

        return {
            "id": mock_id,
            "product": product,
            "quantity": qty,
            "status": "Completed",
            "message": "Order created successfully. Diagnostics running in isolated thread."
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Order creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orders")
async def get_orders(db: AsyncSession = Depends(get_db)):
    # Add your logic here to fetch orders from your database
    # Example:
    # result = await db.execute(text("SELECT * FROM orders"))
    # orders = result.mappings().all()
    # return orders
    
    # Returning a mock list for now to test the connection:
    return [{"id": 1, "product": "Test Item", "quantity": 1, "status": "Completed"}]
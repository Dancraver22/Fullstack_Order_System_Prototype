import os
import httpx
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

from app.database import engine, Base, get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Full-Stack Operations Center API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# 1. ADDED: GET route to fix 405 error
@app.get("/api/orders")
async def get_orders(db: AsyncSession = Depends(get_db)):
    try:
        # Fetching all orders
        result = await db.execute(text("SELECT * FROM orders ORDER BY created_at DESC"))
        return [dict(row) for row in result.mappings()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. FIXED: POST route to match DB schema (product_name)
@app.post("/api/orders")
async def create_order(
    order_data: dict, 
    background_tasks: BackgroundTasks, 
    db: AsyncSession = Depends(get_db)
):
    try:
        # Use 'product_name' to match DB schema
        product_name = order_data.get("product_name", "Unknown Item")
        qty = order_data.get("quantity", 1)

        await db.execute(
            text("INSERT INTO orders (product_name, quantity, status) VALUES (:p, :q, 'pending')"),
            {"p": product_name, "q": qty}
        )
        await db.commit()
        
        return {"message": "Order created"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# 3. ADDED: DELETE route to fix "Failed to clear"
@app.delete("/api/orders")
async def delete_all_orders(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("DELETE FROM orders"))
        await db.commit()
        return {"message": "All orders cleared"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
import asyncio
import logging
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .models import Order
from .database import AsyncSessionLocal

logger = logging.getLogger("app.tasks")
logging.basicConfig(level=logging.INFO)

async def process_order_ai(order_id: int):
    """
    Background worker simulating a 3-attempt retry logic for external AI diagnostic calls.
    Integrates with httpbin.org mock endpoint.
    """
    max_retries = 3
    retry_delay = 1.0  # seconds
    
    # 1. Update order status to "processing"
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        if not order:
            logger.error(f"Order {order_id} not found.")
            return
        order.status = "processing"
        await session.commit()
        product_name = order.product_name
        quantity = order.quantity

    # 2. Network client to simulate mock AI diagnostic call with 3 attempts
    async with httpx.AsyncClient() as client:
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Attempt {attempt}/{max_retries} processing order {order_id} via mock AI API...")
                
                # Hitting httpbin.org/post to simulate third-party AI integration
                response = await client.post(
                    "https://httpbin.org/post",
                    json={
                        "order_id": order_id,
                        "product": product_name,
                        "quantity": quantity,
                        "requested_service": "AI Diagnostic Summary"
                    },
                    timeout=5.0
                )
                response.raise_for_status()
                response_json = response.json()
                
                # Extract some sent data to prove it hit the mock service successfully
                sent_data = response_json.get("json", {})
                prod = sent_data.get("product", "Unknown Product")
                qty = sent_data.get("quantity", 0)
                
                ai_summary = (
                    f"AI Diagnostic summary generated. Order status verified. "
                    f"Validated {qty} unit(s) of '{prod}'. Security check: PASSED. "
                    f"Performance health: EXCELLENT."
                )
                
                # 3. Update status to completed on success
                async with AsyncSessionLocal() as session:
                    result = await session.execute(select(Order).where(Order.id == order_id))
                    db_order = result.scalar_one_or_none()
                    if db_order:
                        db_order.status = "completed"
                        db_order.ai_summary = ai_summary
                        await session.commit()
                logger.info(f"Successfully processed order {order_id} on attempt {attempt}.")
                return
                
            except Exception as e:
                logger.warning(f"Attempt {attempt} failed for order {order_id}: {str(e)}")
                if attempt == max_retries:
                    # Final attempt failed
                    async with AsyncSessionLocal() as session:
                        result = await session.execute(select(Order).where(Order.id == order_id))
                        db_order = result.scalar_one_or_none()
                        if db_order:
                            db_order.status = "failed"
                            db_order.ai_summary = f"AI summary processing failed after {max_retries} retries. Error: {str(e)}"
                            await session.commit()
                    logger.error(f"Failed to process order {order_id} after {max_retries} attempts.")
                else:
                    await asyncio.sleep(retry_delay)

async def run_cleanup_and_batch_processing():
    """
    Simulated background task handling batched processing and cleanup of failed/stale orders.
    Can be run in BackgroundTasks.
    """
    logger.info("Starting batched cleanup and processing task...")
    await asyncio.sleep(0.5) # Simulate batch latency
    
    async with AsyncSessionLocal() as session:
        # Find any order that remains in 'processing' or 'pending' state
        result = await session.execute(
            select(Order).where(Order.status.in_(["pending", "processing"]))
        )
        stale_orders = result.scalars().all()
        
        if stale_orders:
            logger.info(f"Batch worker: Found {len(stale_orders)} active orders in queue.")
            # Perform simulated batched validation or cleaning
            # For demonstration, we just log them
            for o in stale_orders:
                logger.info(f"Batch worker status check: Order {o.id} is currently '{o.status}'")
        else:
            logger.info("Batch worker: No active orders requiring immediate queue cleanup.")
    
    logger.info("Batched cleanup task completed successfully.")

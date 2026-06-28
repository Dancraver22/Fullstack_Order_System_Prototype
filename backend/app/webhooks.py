import os
import hmac
import hashlib
import logging
from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.future import select
from .database import AsyncSessionLocal
from .models import Order

logger = logging.getLogger("app.webhooks")
router = APIRouter()

# Read secret from environment, default to a secure fallback for local dev/testing
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "super_secret_webhook_key")

async def verify_webhook_signature(request: Request, x_signature: str = Header(..., alias="X-Signature")):
    """
    Dependency to verify the HMAC signature of incoming webhooks.
    Computes HMAC-SHA256 of the raw body using the WEBHOOK_SECRET.
    """
    body = await request.body()
    
    # Compute signature
    computed_signature = hmac.new(
        key=WEBHOOK_SECRET.encode("utf-8"),
        msg=body,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    # Secure comparison to prevent timing attacks
    if not hmac.compare_digest(computed_signature, x_signature):
        logger.warning("Webhook signature verification failed.")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    return True

@router.post("/webhooks/payments")
async def handle_payment_webhook(
    request: Request,
    is_valid: bool = Depends(verify_webhook_signature)
):
    """
    Secure payment webhook endpoint. Updates the status of an Order to 'paid' (or logs success).
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
    order_id = payload.get("order_id")
    payment_status = payload.get("status")
    
    if not order_id:
        raise HTTPException(status_code=422, detail="Missing order_id in webhook payload")
        
    logger.info(f"Webhook received. Order ID: {order_id}, Payment Status: {payment_status}")
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        if not order:
            # We log it but return 404 to let the payment provider know the order doesn't exist
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        
        # Simulating updating order with payment confirmation
        if payment_status == "completed":
            order.status = "completed"
            order.ai_summary = (order.ai_summary or "") + "\n[Payment Webhook: Confirmed Paid]"
            await session.commit()
            logger.info(f"Order {order_id} status updated to completed via payment webhook.")
        
    return {"status": "success", "message": f"Webhook processed successfully for order {order_id}"}

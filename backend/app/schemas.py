from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

class OrderCreate(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=100)
    quantity: int = Field(..., gt=0)

class OrderResponse(BaseModel):
    id: int
    product_name: str
    quantity: int
    status: str
    ai_summary: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

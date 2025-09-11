# app/schemas/order.py
from app.db.models import OrderStatus
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int

class OrderCreate(BaseModel):
    items: List[OrderItemCreate]

class OrderItemOut(BaseModel):
    id: int
    product_id: Optional[int]
    quantity: int
    price_at_purchase: float

    model_config = ConfigDict(from_attributes=True)

class OrderOut(BaseModel):
    id: int
    user_id: int
    status: OrderStatus
    total: float
    items: List[OrderItemOut]

    model_config = ConfigDict(from_attributes=True)

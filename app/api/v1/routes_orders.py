# app/api/v1/routes_orders.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.pg import get_db
from app.core.auth import get_current_active_user, get_current_superuser
from app.repos.order_repo import create_order, get_order, list_all_orders, list_orders_for_user, cancel_order
from app.schemas.order import OrderCreate, OrderOut

router = APIRouter()

# Create order - authenticated users
@router.post("/", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order_endpoint(data: OrderCreate, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_active_user)):
    try:
        # convert items to dicts expected by repo
        items = [{"product_id": it.product_id, "quantity": it.quantity} for it in data.items]
        order = await create_order(db, user_id=current_user.id, items=items)
        # load items to return via ORM mode
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# List user's orders
@router.get("/", response_model=List[OrderOut])
async def list_orders(limit: int = Query(50, le=200), offset: int = 0, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_active_user)):
    orders = await list_orders_for_user(db, user_id=current_user.id, limit=limit, offset=offset)
    return orders

# Get single order (owner or admin)
@router.get("/{order_id}", response_model=OrderOut)
async def get_order_endpoint(order_id: int, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_active_user)):
    order = await get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    return order

# Cancel order - owner or admin
@router.post("/{order_id}/cancel", response_model=OrderOut)
async def cancel_order_endpoint(order_id: int, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_active_user)):
    order = await get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    try:
        updated = await cancel_order(db, order)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Admin listing all orders
@router.get("/admin/all", response_model=List[OrderOut])
async def admin_list_all(limit: int = Query(100, le=500), offset: int = 0, db: AsyncSession = Depends(get_db), admin = Depends(get_current_superuser)):
    return await list_all_orders(db, limit=limit, offset=offset)

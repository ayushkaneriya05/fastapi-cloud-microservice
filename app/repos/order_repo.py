# app/repos/order_repo.py
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Order, OrderItem, Product
from sqlalchemy.exc import NoResultFound

async def create_order(session: AsyncSession , user_id: int, items: List[dict]):
    """
    items: list of dicts {product_id: int, quantity: int}
    This function:
      - checks stock
      - decreases stock
      - creates order with order items and price at purchase
      - returns order with items
    """
    order = Order(user_id=user_id, total=0.0)
    session.add(order)
    await session.flush()  # assign id

    total = 0.0
    created_items = []
    for it in items:
        product_id = it["product_id"]
        quantity = it["quantity"]
        product: Product = ( await session.execute(
        select(Product).where(Product.id == product_id).with_for_update())).scalar_one_or_none()
        if not product or not product.is_active:
            raise ValueError(f"Product {product_id} not available")
        if product.stock < quantity:
            raise ValueError(f"Insufficient stock for product {product_id}")
        price_at_purchase = float(product.price)
        product.stock = product.stock - quantity
        order_item = OrderItem(order_id=order.id, product_id=product_id, quantity=quantity, price_at_purchase=price_at_purchase)
        session.add(order_item)
        total += price_at_purchase * quantity
        created_items.append(order_item)

    order.total = total
    session.add(order)
    await session.commit()
    q = select(Order).options(selectinload(Order.items)).where(Order.id == order.id)
    res = await session.execute(q)
    return res.scalars().first()

async def get_order(session: AsyncSession, order_id: int) -> Optional[Order]:
    q = (
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id)
    )
    res = await session.execute(q)
    return res.scalars().first()

async def list_orders_for_user(session: AsyncSession, user_id: int, limit: int = 50, offset: int = 0):
    q = (
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.user_id == user_id)
        .limit(limit)
        .offset(offset)
    )
    res = await session.execute(q)
    return res.scalars().all()

async def cancel_order(session: AsyncSession, order: Order):
    # basic cancellation policy: only pending/paid can be cancelled
    if order.status in (order.status.pending, order.status.paid):
        order.status = order.status.cancelled
        # restore stock
        for item in order.items:
            product = await session.get(Product, item.product_id)
            if product:
                product.stock += item.quantity
        session.add(order)
        await session.commit()
        q = select(Order).options(selectinload(Order.items)).where(Order.id == order.id)
        res = await session.execute(q)
        
    else:
        raise ValueError("Cannot cancel this order")
    return res.scalars().first()

async def list_all_orders(session: AsyncSession, limit: int = 100, offset: int = 0):
    q = select(Order).options(selectinload(Order.items)).limit(limit).offset(offset)
    res = await session.execute(q)
    return res.scalars().all()


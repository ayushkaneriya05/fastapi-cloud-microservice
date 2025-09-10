# app/repos/product_repo.py
from typing import Optional
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Product

async def create_product(session: AsyncSession, owner_id: int, name: str, price: float, stock: int = 0, description: str | None = None, image_key: str | None = None) -> Product:
    product = Product(owner_id=owner_id, name=name, price=price, stock=stock, description=description, image_key=image_key)
    session.add(product)
    await session.flush()
    await session.commit()
    await session.refresh(product)
    return product

async def get_product(session: AsyncSession, product_id: int) -> Optional[Product]:
    return await session.get(Product, product_id)

async def list_products(session: AsyncSession, limit: int = 50, offset: int = 0, only_active: bool = True):
    q = select(Product)
    if only_active:
        q = q.where(Product.is_active == True)
    q = q.limit(limit).offset(offset)
    res = await session.execute(q)
    return res.scalars().all()

async def update_product(session: AsyncSession, product: Product, **fields) -> Product:
    for k, v in fields.items():
        if v is not None and hasattr(product, k):
            setattr(product, k, v)
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product

async def delete_product(session: AsyncSession, product: Product):
    await session.delete(product)
    await session.commit()
    return

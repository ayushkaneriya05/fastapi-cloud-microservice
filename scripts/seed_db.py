# scripts/seed_db.py
import asyncio
import os
import sys
sys.path.insert(0, os.getcwd())

from sqlalchemy import text
from app.db.models import Base, User, Product
from app.core.security import hash_password
from app.db.pg import engine, AsyncSessionLocal  # engine and session maker from app/db/pg.py
from sqlalchemy.ext.asyncio import AsyncSession

async def create_schema_and_seed():
    # Drop and recreate schema (development safe)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)   # DROP everything
        await conn.run_sync(Base.metadata.create_all) # CREATE everything

    # Seed data
    async with AsyncSessionLocal() as session:
        # create admin user
        admin = User(email="admin@example.com", hashed_password=hash_password("changeme"), is_superuser=True)
        session.add(admin)
        await session.flush()
        # create a product owned by admin (owner_id will be set from admin.id via flush)
        prod = Product(owner_id=admin.id, name="Starter Laptop", description="Seeded product", price=999.99)
        session.add(prod)
        await session.commit()
        print("Seeded admin and product.")

if __name__ == "__main__":
    asyncio.run(create_schema_and_seed())

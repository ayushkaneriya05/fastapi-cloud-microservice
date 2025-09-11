# tests/repos/test_product_repo.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.repos import product_repo
from app.db.models import User, Product

# All tests in this file are correctly marked with @pytest.mark.asyncio
# as they directly call asynchronous repository functions.

@pytest.mark.asyncio
async def test_create_product(db_session: AsyncSession, test_user: User):
    """
    Tests that a product can be created successfully with an owner.
    """
    product_data = {
        "name": "Wireless Mouse",
        "price": 49.99,
        "stock": 150,
        "description": "A high-precision wireless mouse."
    }
    product = await product_repo.create_product(
        session=db_session,
        owner_id=test_user.id,
        **product_data
    )
    
    assert product.name == product_data["name"]
    assert product.owner_id == test_user.id
    assert product.stock == product_data["stock"]

@pytest.mark.asyncio
async def test_update_product(db_session: AsyncSession, test_user: User):
    """
    Tests updating a product's details, such as price and stock.
    """
    # First, create a product to update
    product = await product_repo.create_product(
        session=db_session, owner_id=test_user.id, name="Test Keyboard", price=99.99, stock=100
    )

    # Now, update it
    updated_product = await product_repo.update_product(
        session=db_session, product=product, price=89.99, stock=50
    )
    
    assert updated_product.price == 89.99
    assert updated_product.stock == 50
    assert updated_product.name == "Test Keyboard"  # This should not change

@pytest.mark.asyncio
async def test_get_product(db_session: AsyncSession, test_user: User):
    """
    Tests retrieving a specific product by its ID.
    """
    product = await product_repo.create_product(
        session=db_session, owner_id=test_user.id, name="Test Product", price=10
    )
    retrieved_product = await product_repo.get_product(db_session, product_id=product.id)
    
    assert retrieved_product is not None
    assert retrieved_product.id == product.id
    assert retrieved_product.name == "Test Product"

@pytest.mark.asyncio
async def test_list_products(db_session: AsyncSession, test_user: User):
    """
    Tests listing all products from the database.
    """
    # Create a couple of products to ensure the list is not empty
    await product_repo.create_product(
        session=db_session, owner_id=test_user.id, name="Product A", price=10
    )
    await product_repo.create_product(
        session=db_session, owner_id=test_user.id, name="Product B", price=20
    )
    
    products = await product_repo.list_products(db_session)
    
    # Due to test isolation, we can be sure about the exact count
    assert len(products) == 2

@pytest.mark.asyncio
async def test_delete_product(db_session: AsyncSession, test_user: User):
    """
    Tests that a product can be successfully deleted.
    """
    product_to_delete = await product_repo.create_product(
        session=db_session, owner_id=test_user.id, name="Deletable", price=5
    )
    
    # Delete the product
    await product_repo.delete_product(db_session, product=product_to_delete)
    
    # Verify the product is no longer in the database
    deleted_product = await product_repo.get_product(db_session, product_id=product_to_delete.id)
    assert deleted_product is None
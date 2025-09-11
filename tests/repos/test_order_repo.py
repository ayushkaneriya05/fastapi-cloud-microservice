# tests/repos/test_order_repo.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.repos import order_repo, product_repo
from app.db.models import User, Product
import pytest_asyncio

# A fixture to create a sample product, making it available for order tests.
@pytest_asyncio.fixture
async def sample_product(db_session: AsyncSession, test_user: User) -> Product:
    """Fixture to create a sample product for order tests."""
    product = await product_repo.create_product(
        session=db_session,
        owner_id=test_user.id,
        name="Sample T-Shirt",
        price=19.99,
        stock=20
    )
    return product

@pytest.mark.asyncio
async def test_create_order_success(db_session: AsyncSession, test_user: User, sample_product: Product):
    """
    Tests successful order creation and verifies that the product stock is correctly decreased.
    """
    items = [{"product_id": sample_product.id, "quantity": 2}]
    order = await order_repo.create_order(session=db_session, user_id=test_user.id, items=items)

    # Verify order details
    assert order.user_id == test_user.id
    assert order.total == pytest.approx(19.99 * 2)
    assert len(order.items) == 1
    assert order.items[0].quantity == 2
    
    # Verify stock was updated correctly
    await db_session.refresh(sample_product)
    assert sample_product.stock == 18  # Initial stock (20) - quantity (2)

@pytest.mark.asyncio
async def test_create_order_insufficient_stock(db_session: AsyncSession, test_user: User, sample_product: Product):
    """
    Tests that an order creation fails with a ValueError if there is not enough stock.
    """
    items = [{"product_id": sample_product.id, "quantity": 100}] # Order more than available stock
    with pytest.raises(ValueError, match="Insufficient stock"):
        await order_repo.create_order(session=db_session, user_id=test_user.id, items=items)

@pytest.mark.asyncio
async def test_cancel_order(db_session: AsyncSession, test_user: User, sample_product: Product):
    """
    Tests that cancelling an order correctly restores the product stock.
    """
    items = [{"product_id": sample_product.id, "quantity": 5}]
    order = await order_repo.create_order(session=db_session, user_id=test_user.id, items=items)
    
    # Stock should be 15 after the order
    await db_session.refresh(sample_product)
    assert sample_product.stock == 15

    # Cancel the order
    await order_repo.cancel_order(session=db_session, order=order)

    # Verify stock was restored to its original value
    await db_session.refresh(sample_product)
    assert sample_product.stock == 20

@pytest.mark.asyncio
async def test_get_order(db_session: AsyncSession, test_user: User, sample_product: Product):
    """
    Tests retrieving a single order by its ID.
    """
    items = [{"product_id": sample_product.id, "quantity": 1}]
    order = await order_repo.create_order(session=db_session, user_id=test_user.id, items=items)
    
    retrieved_order = await order_repo.get_order(db_session, order_id=order.id)
    
    assert retrieved_order is not None
    assert retrieved_order.id == order.id
    assert retrieved_order.user_id == test_user.id

@pytest.mark.asyncio
async def test_list_orders_for_user(db_session: AsyncSession, test_user: User, sample_product: Product):
    """
    Tests listing all orders for a specific user.
    """
    items = [{"product_id": sample_product.id, "quantity": 1}]
    await order_repo.create_order(session=db_session, user_id=test_user.id, items=items)
    
    user_orders = await order_repo.list_orders_for_user(db_session, user_id=test_user.id)
    
    assert len(user_orders) == 1
    assert user_orders[0].user_id == test_user.id

@pytest.mark.asyncio
async def test_list_all_orders(db_session: AsyncSession, test_user: User, superuser: User, sample_product: Product):
    """
    Tests the admin function to list all orders from all users.
    """
    items = [{"product_id": sample_product.id, "quantity": 1}]
    # Create orders for two different users
    await order_repo.create_order(session=db_session, user_id=test_user.id, items=items)
    await order_repo.create_order(session=db_session, user_id=superuser.id, items=items)

    all_orders = await order_repo.list_all_orders(db_session)
    
    # Because of test isolation, we know exactly how many orders should be in the DB
    assert len(all_orders) == 2
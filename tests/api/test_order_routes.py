# tests/api/test_order_routes.py
import pytest
from fastapi.testclient import TestClient
from fastapi import status
from app.db.models import User, Product
from unittest.mock import MagicMock


def product_for_order(client: TestClient, superuser_auth_headers: dict) -> dict:
    """Fixture to create a product available for ordering via the API."""
    response = client.post(
        "/api/v1/products/",
        headers=superuser_auth_headers,
        json={"name": "Orderable Item", "price": 25.00, "stock": 10},
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()

def test_create_order(client: TestClient, auth_headers: dict, product_for_order: dict):
    """
    Tests successful order creation via the API.
    """
    order_data = {
        "items": [
            {"product_id": product_for_order["id"], "quantity": 2}
        ]
    }
    response = client.post("/api/v1/orders/", headers=auth_headers, json=order_data)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["total"] == 50.00
    assert data["items"][0]["product_id"] == product_for_order["id"]

def test_create_order_insufficient_stock_api(client: TestClient, auth_headers: dict, product_for_order: dict):
    """
    Tests that the API returns a 400 error for insufficient stock.
    """
    order_data = {
        "items": [
            {"product_id": product_for_order["id"], "quantity": 20} # More than available stock
        ]
    }
    response = client.post("/api/v1/orders/", headers=auth_headers, json=order_data)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Insufficient stock" in response.json()["detail"]

def test_get_own_orders(client: TestClient, auth_headers: dict, product_for_order: dict):
    """
    Tests that a user can retrieve their own list of orders.
    """
    # First, create an order
    client.post("/api/v1/orders/", headers=auth_headers, json={
        "items": [{"product_id": product_for_order["id"], "quantity": 1}]
    })
    
    # Then, list the orders
    response = client.get("/api/v1/orders/", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["items"][0]["product_id"] == product_for_order["id"]

def test_get_order_not_found(client: TestClient, auth_headers: dict):
    """
    Tests that requesting a non-existent order returns a 404 error.
    """
    response = client.get("/api/v1/orders/999999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_get_order_not_owner(
    client: TestClient, auth_headers: dict, superuser_auth_headers: dict, product_for_order: dict
):
    """
    Tests that a user cannot access an order belonging to another user.
    """
    # Create an order owned by the superuser
    order_data = {"items": [{"product_id": product_for_order["id"], "quantity": 1}]}
    create_response = client.post("/api/v1/orders/", headers=superuser_auth_headers, json=order_data)
    order_id = create_response.json()["id"]
    
    # Attempt to access it as the standard test_user
    response = client.get(f"/api/v1/orders/{order_id}", headers=auth_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_cancel_order_api(client: TestClient, auth_headers: dict, product_for_order: dict):
    """
    Tests that a user can cancel their own order via the API.
    """
    # Create an order
    order_data = {"items": [{"product_id": product_for_order["id"], "quantity": 1}]}
    create_response = client.post("/api/v1/orders/", headers=auth_headers, json=order_data)
    order_id = create_response.json()["id"]

    # Cancel the order
    response = client.post(f"/api/v1/orders/{order_id}/cancel", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "cancelled"

def test_admin_list_all_orders(
    client: TestClient, superuser_auth_headers: dict, auth_headers: dict, product_for_order: dict
):
    """
    Tests that an admin can list all orders from all users.
    """
    # Create an order for the regular test user
    client.post(
        "/api/v1/orders/",
        headers=auth_headers,
        json={"items": [{"product_id": product_for_order["id"], "quantity": 1}]}
    )

    # List all orders as admin
    response = client.get("/api/v1/orders/admin/all", headers=superuser_auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

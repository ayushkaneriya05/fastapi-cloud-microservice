# tests/api/test_product_routes.py
from fastapi.testclient import TestClient
from fastapi import status
from app.db.models import User
from io import BytesIO
from unittest.mock import MagicMock

def test_create_product_as_superuser(client: TestClient, superuser_auth_headers: dict):
    """
    Tests that a superuser can create a new product.
    """
    response = client.post(
        "/api/v1/products/",
        headers=superuser_auth_headers,
        json={"name": "New Laptop", "price": 1299.99, "stock": 50},
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "New Laptop"
    assert "id" in data

def test_list_products_public(client: TestClient, superuser_auth_headers: dict):
    """
    Tests that anyone can list products.
    """
    # First, create a product to ensure the list isn't empty
    client.post(
        "/api/v1/products/",
        headers=superuser_auth_headers,
        json={"name": "Public Product", "price": 9.99, "stock": 10},
    )
    
    response = client.get("/api/v1/products/")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0


def test_update_product_as_owner(client: TestClient, superuser_auth_headers: dict):
    """
    Tests that a product owner can update their product.
    """
    # Step 1: Create a product to update
    create_response = client.post(
        "/api/v1/products/",
        headers=superuser_auth_headers,
        json={"name": "Old Name", "price": 10, "stock": 100},
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    product_id = create_response.json()["id"]

    # Step 2: Update the product
    response = client.put(
        f"/api/v1/products/{product_id}",
        headers=superuser_auth_headers,
        json={"name": "New Name", "price": 15.50},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "New Name"
    assert data["price"] == 15.50

def test_update_product_not_owner(client: TestClient, superuser_auth_headers: dict, auth_headers: dict):
    """
    Tests that a user cannot update a product they do not own.
    """
    # Step 1: Superuser creates a product
    create_response = client.post(
        "/api/v1/products/",
        headers=superuser_auth_headers,
        json={"name": "Someone else's product", "price": 10, "stock": 10},
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    product_id = create_response.json()["id"]

    # Step 2: Standard user tries to update it
    response = client.put(
        f"/api/v1/products/{product_id}",
        headers=auth_headers, # Using standard user's headers
        json={"name": "Attempted New Name"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_delete_product_as_owner(client: TestClient, superuser_auth_headers: dict):
    """
    Tests that a product owner can delete their product.
    """
    # Step 1: Create a product to delete
    create_response = client.post(
        "/api/v1/products/",
        headers=superuser_auth_headers,
        json={"name": "To Be Deleted", "price": 10, "stock": 10},
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    product_id = create_response.json()["id"]

    # Step 2: Delete the product
    response = client.delete(f"/api/v1/products/{product_id}", headers=superuser_auth_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT

def test_upload_product_image(client: TestClient, superuser_auth_headers: dict, mock_s3_client: MagicMock):
    """
    Tests uploading an image for a product.
    """
    # Step 1: Create a product
    create_response = client.post(
        "/api/v1/products/",
        headers=superuser_auth_headers,
        json={"name": "Product with Image", "price": 10, "stock": 10},
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    product_id = create_response.json()["id"]
    
    # Step 2: Upload an image for the product
    file_content = b"fake image data"
    files = {"file": ("image.jpg", BytesIO(file_content), "image/jpeg")}

    response = client.post(
        f"/api/v1/products/{product_id}/image",
        headers=superuser_auth_headers,
        files=files,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "image_key" in data
    assert data["image_key"] is not None
    mock_s3_client.upload_fileobj.assert_called_once()

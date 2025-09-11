# tests/api/test_user_routes.py
from fastapi.testclient import TestClient
from fastapi import status
from app.db.models import User

# NOTE: All tests using the `client` fixture must be synchronous (no `async def`)
# because `TestClient` is a synchronous test utility.

def test_get_me(client: TestClient, auth_headers: dict):
    """
    Tests the /users/me endpoint for an authenticated user.
    """
    # No `await` for client calls
    response = client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "test@example.com"

def test_list_users_as_superuser(client: TestClient, superuser_auth_headers: dict, test_user: User):
    """
    Tests that a superuser can list all users.
    The `test_user` fixture is included to ensure at least one user exists.
    """
    response = client.get("/api/v1/users/", headers=superuser_auth_headers)
    assert response.status_code == status.HTTP_200_OK
    # The list should contain at least the test_user and the superuser
    assert len(response.json()) >= 2

def test_list_users_as_normal_user(client: TestClient, auth_headers: dict):
    """
    Tests that a normal user is forbidden from listing users.
    """
    response = client.get("/api/v1/users/", headers=auth_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_create_user_as_admin(client: TestClient, superuser_auth_headers: dict):
    """
    Tests that an admin/superuser can create a new user.
    """
    response = client.post(
        "/api/v1/users/",
        headers=superuser_auth_headers,
        json={"email": "createdbyadmin@example.com", "password": "password123"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "createdbyadmin@example.com"

def test_update_me(client: TestClient, auth_headers: dict):
    """
    Tests that a user can update their own information.
    """
    response = client.put(
        "/api/v1/users/me",
        headers=auth_headers,
        json={"email": "updated.me@example.com"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "updated.me@example.com"

def test_delete_user_as_admin(client: TestClient, superuser_auth_headers: dict, test_user: User):
    """
    Tests that an admin can delete another user.
    """
    response = client.delete(f"/api/v1/users/{test_user.id}", headers=superuser_auth_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT

import pytest
import re
from fastapi.testclient import TestClient
from fastapi import status
from app.core.security import create_refresh_token, create_access_token
from app.db.models import User
from unittest.mock import MagicMock

# NOTE: All tests using the `client` fixture must be synchronous (`def`).

def test_register_user(client: TestClient):
    """
    Tests successful user registration.
    """
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "registertest@example.com", "password": "password123"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "registertest@example.com"
    assert "id" in data

def test_login(client: TestClient, test_user: User):
    """
    Tests successful login. FastAPI's OAuth2 form expects 'x-www-form-urlencoded' data.
    """
    response = client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "password123"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

def test_login_invalid_credentials(client: TestClient, test_user: User):
    """
    Tests login failure with an incorrect password.
    """
    response = client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "wrongpassword"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_logout(client: TestClient, auth_headers: dict):
    """
    Tests that a user can log out.
    """
    response = client.post("/api/v1/auth/logout", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["msg"] == "Logged out"

def test_password_reset_request(client: TestClient, test_user: User, mock_send_email: MagicMock):
    """
    Tests the password reset request which should trigger an email.
    """
    response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": test_user.email}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["msg"] == "OTP sent to email"
    mock_send_email.assert_called_once()

def test_password_reset_verify(client: TestClient, test_user: User, mock_send_email: MagicMock):
    """
    Tests the full password reset flow with a valid OTP.
    """
    email = test_user.email
    
    # Step 1: Request a password reset to generate an OTP
    client.post("/api/v1/auth/password-reset/request", json={"email": email})
    
    # Step 2: Extract the OTP from the mocked email call
    email_body = mock_send_email.call_args.kwargs['body']
    otp_match = re.search(r'\b\d{6}\b', email_body)
    assert otp_match, "Could not find OTP in mocked email body"
    otp = otp_match.group(0)

    # Step 3: Verify the OTP and set a new password
    response = client.post(
        "/api/v1/auth/password-reset/verify",
        json={"email": email, "otp": otp, "new_password": "newpassword123"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["msg"] == "Password reset successful"

def test_refresh_token(client: TestClient, test_user: User):
    """
    Tests that a valid refresh token can be used to get a new access token.
    """
    refresh_token = create_refresh_token(subject=str(test_user.id))
    
    response = client.post(
        "/api/v1/auth/refresh",
        headers={"Authorization": f"Bearer {refresh_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data

def test_superuser_route(client: TestClient, superuser_auth_headers: dict):
    """
    Tests the superuser-only protected route for listing all users.
    """
    response = client.get("/api/v1/users/", headers=superuser_auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)

def test_access_with_inactive_user_token(client: TestClient, inactive_user: User):
    """
    Tests that a protected endpoint cannot be accessed by an inactive user.
    """
    token = create_access_token(subject=str(inactive_user.id))
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/v1/users/me", headers=headers)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Inactive user"


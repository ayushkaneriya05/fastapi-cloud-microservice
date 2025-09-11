# tests/api/test_auth_routes.py
import re
from fastapi.testclient import TestClient
from fastapi import status
from app.core.security import create_refresh_token, create_access_token
from app.db.models import User
from unittest.mock import MagicMock

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

def test_access_with_inactive_user_token(client: TestClient, inactive_user: User):
    """
    Tests that a protected endpoint cannot be accessed by an inactive user.
    """
    token = create_access_token(subject=str(inactive_user.id))
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/v1/users/me", headers=headers)
    
    # Application correctly denies access, but with 400, not 401
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Inactive user"

def test_access_with_invalid_token(client: TestClient):
    """
    Tests that a protected endpoint rejects a malformed or invalid token.
    """
    invalid_token = "this.is.not.a.valid.jwt"
    headers = {"Authorization": f"Bearer {invalid_token}"}
    
    response = client.get("/api/v1/users/me", headers=headers)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_login(client: TestClient, test_user: User):
    """
    Tests successful login using JSON payload.
    """
    response = client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "password123"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client: TestClient, test_user: User):
    """
    Tests login failure with an incorrect password using JSON payload.
    """
    response = client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "wrongpassword"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_password_reset_request(client: TestClient, test_user: User):
    """
    Tests the password reset request which should trigger an email.
    NOTE: current route expects raw string body, not JSON object.
    """
    response = client.post(
        "/api/v1/auth/password-reset/request",
        json=test_user.email,  # raw string body
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["msg"] == "OTP sent to email"


def test_password_reset_verify(client: TestClient, test_user: User, monkeypatch):
    """
    Tests the full password reset flow with a valid OTP.
    """
    email = test_user.email
    sent = {}

    # patch send_email to capture OTP
    def fake_send_email(to, subject, body):
        sent["body"] = body

    from app.core import email as email_module
    monkeypatch.setattr(email_module, "send_email", fake_send_email)

    # Step 1: Request a password reset to generate an OTP
    client.post("/api/v1/auth/password-reset/request", json=email)

    # Step 2: Extract the OTP from the captured email
    import re
    otp_match = re.search(r"\b\d{6}\b", sent["body"])
    assert otp_match, "Could not find OTP in mocked email body"
    otp = otp_match.group(0)

    # Step 3: Verify the OTP and set a new password
    response = client.post(
        "/api/v1/auth/password-reset/verify",
        json={"email": email, "otp": otp, "new_password": "newpassword123"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["msg"] == "Password reset successful"

    # Step 4: Verify login with the new password
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "newpassword123"},
    )
    assert login_response.status_code == status.HTTP_200_OK


def test_refresh_token(client: TestClient, test_user: User):
    """
    Tests that a valid refresh token can be used to get a new access token.
    NOTE: current route expects raw string body, not JSON object.
    """
    refresh_token = create_refresh_token(subject=str(test_user.id))

    response = client.post(
        "/api/v1/auth/refresh",
        json=refresh_token,  # raw string body
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert "refresh_token" in data


def test_superuser_route(client: TestClient, superuser_auth_headers: dict):
    """
    Tests the superuser-only protected route.
    """
    response = client.get("/api/v1/auth/superuser", headers=superuser_auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert "email" in response.json()

# tests/api/test_main.py
import pytest
from fastapi.testclient import TestClient
from fastapi import status
from app.core.config import settings

def test_root_endpoint(client: TestClient):
    """
    Tests the main root endpoint of the application.
    """
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": f"Welcome to {settings.PROJECT_NAME}"}

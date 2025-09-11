# tests/api/test_health_routes.py
from fastapi.testclient import TestClient
from fastapi import status

def test_live_endpoint(client: TestClient):
    """
    Tests the /live health check endpoint.
    """
    response = client.get("/api/v1/health/live")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}

def test_ready_endpoint(client: TestClient):
    """
    Tests the /ready health check endpoint.
    """
    response = client.get("/api/v1/health/ready")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ready"}

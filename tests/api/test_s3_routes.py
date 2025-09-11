# tests/api/test_s3_routes.py
from fastapi.testclient import TestClient
from fastapi import status
from io import BytesIO
from unittest.mock import MagicMock

# NOTE: All tests using the `client` fixture must be synchronous (no `async def`)
# because `TestClient` is a synchronous test utility.

def test_upload_file(client: TestClient, auth_headers: dict, mock_s3_client: MagicMock):
    """
    Tests successful file upload to the mock S3 client.
    """
    file_content = b"This is a test file for upload."
    files = {"file": ("test_upload.txt", BytesIO(file_content), "text/plain")}
    
    # The client call is synchronous (no await)
    response = client.post("/api/v1/s3/upload", headers=auth_headers, files=files)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "file_key" in data
    assert "download_url" in data
    
    # Verify that the mock S3 client's put_object method was called
    mock_s3_client.upload_fileobj.assert_called_once()

def test_get_presigned_url(client: TestClient, auth_headers: dict, mock_s3_client: MagicMock):
    """
    Tests retrieving a presigned URL for a given file key.
    """
    file_key = "some/test/file.txt"
    response = client.get(f"/api/v1/s3/file/{file_key}", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["file_key"] == file_key
    assert data["download_url"] == "https://s3.test/mock-url"
    
    # Verify that the S3 client's generate_presigned_url method was called
    mock_s3_client.generate_presigned_url.assert_called_once_with(
        "get_object",
        Params={"Bucket": "ecom-bucket-1", "Key": file_key},
        ExpiresIn=3600
    )

def test_delete_file(client: TestClient, auth_headers: dict, mock_s3_client: MagicMock):
    """
    Tests successful file deletion from the mock S3 client.
    """
    file_key = "some/test/file_to_delete.txt"
    response = client.delete(f"/api/v1/s3/file/{file_key}", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "File deleted successfully"
    
    # Verify that the S3 client's delete_object method was called
    mock_s3_client.delete_object.assert_called_once_with(Bucket="ecom-bucket-1", Key=file_key)

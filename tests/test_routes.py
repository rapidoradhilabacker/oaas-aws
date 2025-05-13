"""
Test cases for the FastAPI AWS S3 File Upload Service API routes.
"""

import io
import pytest
from fastapi import UploadFile
from app.schemas import OaasFolderRequest, OaasFileRequest, S3BucketContentType

def test_root_endpoint(test_client):
    """Test the root endpoint returns welcome message."""
    response = test_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the FastAPI AWS S3 Service"}

def test_upload_file(test_client, mock_s3_service, monkeypatch):
    """Test the file upload endpoint."""
    # Create a mock file
    file_content = b"test file content"
    file = io.BytesIO(file_content)
    
    response = test_client.post(
        "/s3/upload",
        files={"file": ("test.txt", file, "text/plain")},
        data={"file_name": "test.txt", "directory": "test"}
    )
    
    assert response.status_code == 200
    assert "s3_url" in response.json()
    assert response.json()["s3_url"] == "https://test-bucket.s3.amazonaws.com/test/file.txt"

def test_upload_file_with_content_type(test_client, mock_s3_service):
    """Test file upload with content type specification."""
    file_content = b"test image content"
    file = io.BytesIO(file_content)
    
    response = test_client.post(
        "/s3/upload/content-type",
        files={"file": ("test.jpg", file, "image/jpeg")},
        data={
            "file_name": "test.jpg",
            "content_type": S3BucketContentType.IMAGE.value,
            "directory": "test"
        }
    )
    
    assert response.status_code == 200
    assert "s3_url" in response.json()
    assert response.json()["s3_url"] == "https://test-bucket.s3.amazonaws.com/test/file.jpg"

def test_upload_oaas_folder(test_client, mock_s3_service):
    """Test OAAS folder upload endpoint."""
    request_data = {
        "tenant_id": "test-tenant",
        "user_id": "test-user",
        "product_id": "test-product",
        "folder_url": "https://example.com/test.zip"
    }
    
    response = test_client.post("/s3/upload/oaas/folder", json=request_data)
    
    assert response.status_code == 200
    assert "s3_urls" in response.json()

def test_upload_oaas_files(test_client, mock_s3_service):
    """Test OAAS files upload endpoint."""
    request_data = {
        "tenant_id": "test-tenant",
        "user_id": "test-user",
        "product_id": "test-product",
        "file_urls": ["https://example.com/file1.jpg", "https://example.com/file2.jpg"]
    }
    
    response = test_client.post("/s3/upload/oaas/files", json=request_data)
    
    assert response.status_code == 200
    assert "s3_urls" in response.json()

def test_upload_presigned_url(test_client, mock_s3_service):
    """Test presigned URL generation endpoint."""
    response = test_client.post(
        "/s3/upload/presigned",
        data={
            "source": "https://example.com/test.txt",
            "file_name": "test.txt"
        }
    )
    
    assert response.status_code == 200
    assert "presigned_url" in response.json()
    assert "signature" in response.json()["presigned_url"]

def test_upload_file_error(test_client, mock_s3_service):
    """Test error handling in file upload endpoint."""
    mock_s3_service.save_file.side_effect = Exception("Upload failed")
    
    file_content = b"test file content"
    file = io.BytesIO(file_content)
    
    response = test_client.post(
        "/s3/upload",
        files={"file": ("test.txt", file, "text/plain")},
        data={"file_name": "test.txt", "directory": "test"}
    )
    
    assert response.status_code == 500
    assert "detail" in response.json()
    assert "Upload failed" in response.json()["detail"] 
"""
Pytest configuration and fixtures for the FastAPI AWS S3 File Upload Service tests.
"""

import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.service import S3FileService

@pytest.fixture
def test_client():
    """
    Create a test client for the FastAPI application.
    """
    return TestClient(app)

@pytest.fixture
def mock_s3_service(mocker):
    """
    Create a mock S3FileService for testing.
    """
    mock_service = mocker.Mock(spec=S3FileService)
    # Add common mock responses here
    mock_service.save_file.return_value = "https://test-bucket.s3.amazonaws.com/test/file.txt"
    mock_service.save_file_with_content_type.return_value = "https://test-bucket.s3.amazonaws.com/test/file.jpg"
    mock_service.save_file_with_validity.return_value = "https://test-bucket.s3.amazonaws.com/test/file.txt?signature=xyz"
    return mock_service

@pytest.fixture
def test_env_vars():
    """
    Set up test environment variables.
    """
    os.environ["FILE_UPLOAD_BUCKET"] = "test-bucket"
    os.environ["FILE_UPLOAD_KEY_ID"] = "test-key-id"
    os.environ["FILE_UPLOAD_ACCESS_KEY"] = "test-access-key"
    yield
    # Clean up
    del os.environ["FILE_UPLOAD_BUCKET"]
    del os.environ["FILE_UPLOAD_KEY_ID"]
    del os.environ["FILE_UPLOAD_ACCESS_KEY"] 
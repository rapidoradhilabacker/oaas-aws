"""
Test cases for the S3FileService class.
"""

import pytest
from unittest.mock import Mock, patch
from app.service import S3FileService
from fastapi import UploadFile
from app.schemas import OaasFolderRequest, OaasFileRequest, S3BucketContentType

@pytest.fixture
def s3_service():
    """Create an S3FileService instance for testing."""
    return S3FileService(
        bucket_name="test-bucket",
        aws_access_key_id="test-key-id",
        aws_secret_access_key="test-access-key"
    )

@pytest.mark.asyncio
async def test_save_file(s3_service):
    """Test saving a file to S3."""
    # Mock file and S3 client
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = "test.txt"
    mock_file.file.read.return_value = b"test content"
    
    with patch("aioboto3.Session") as mock_session:
        mock_client = Mock()
        mock_session.return_value.client.return_value.__aenter__.return_value = mock_client
        
        result = await s3_service.save_file(
            file=mock_file,
            file_name="test.txt",
            directory="test"
        )
        
        # Verify S3 upload was called
        mock_client.upload_fileobj.assert_called_once()
        assert "test-bucket.s3.amazonaws.com" in result

@pytest.mark.asyncio
async def test_save_file_with_content_type(s3_service):
    """Test saving a file with specific content type."""
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = "test.jpg"
    mock_file.file.read.return_value = b"test image content"
    
    with patch("aioboto3.Session") as mock_session:
        mock_client = Mock()
        mock_session.return_value.client.return_value.__aenter__.return_value = mock_client
        
        result = await s3_service.save_file_with_content_type(
            file=mock_file,
            file_name="test.jpg",
            content_type=S3BucketContentType.IMAGE
        )
        
        # Verify content type was set
        mock_client.upload_fileobj.assert_called_once()
        call_kwargs = mock_client.upload_fileobj.call_args[1]
        assert "ContentType" in call_kwargs.get("ExtraArgs", {})
        assert "image/" in call_kwargs["ExtraArgs"]["ContentType"]

@pytest.mark.asyncio
async def test_save_oaas_folder(s3_service):
    """Test saving an OAAS folder structure."""
    request = OaasFolderRequest(
        tenant_id="test-tenant",
        user_id="test-user",
        product_id="test-product",
        folder_url="https://example.com/test.zip"
    )
    
    with patch("aioboto3.Session") as mock_session:
        mock_client = Mock()
        mock_session.return_value.client.return_value.__aenter__.return_value = mock_client
        
        result = await s3_service.save_oaas_folder(request)
        
        assert isinstance(result, list)
        mock_client.upload_fileobj.assert_called()

@pytest.mark.asyncio
async def test_save_oaas_files(s3_service):
    """Test saving multiple OAAS files."""
    request = OaasFileRequest(
        tenant_id="test-tenant",
        user_id="test-user",
        product_id="test-product",
        file_urls=["https://example.com/file1.jpg", "https://example.com/file2.jpg"]
    )
    
    with patch("aioboto3.Session") as mock_session:
        mock_client = Mock()
        mock_session.return_value.client.return_value.__aenter__.return_value = mock_client
        
        result = await s3_service.save_oaas_files(request)
        
        assert isinstance(result, list)
        assert mock_client.upload_fileobj.call_count == len(request.file_urls)

@pytest.mark.asyncio
async def test_save_file_with_validity(s3_service):
    """Test generating a presigned URL for a file."""
    with patch("aioboto3.Session") as mock_session:
        mock_client = Mock()
        mock_session.return_value.client.return_value.__aenter__.return_value = mock_client
        mock_client.generate_presigned_url.return_value = "https://test-bucket.s3.amazonaws.com/test.txt?signature=xyz"
        
        result = await s3_service.save_file_with_validity(
            source="https://example.com/test.txt",
            file_name="test.txt"
        )
        
        assert "signature" in result
        mock_client.generate_presigned_url.assert_called_once()

@pytest.mark.asyncio
async def test_error_handling(s3_service):
    """Test error handling in S3FileService."""
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = "test.txt"
    mock_file.file.read.return_value = b"test content"
    
    with patch("aioboto3.Session") as mock_session:
        mock_client = Mock()
        mock_session.return_value.client.return_value.__aenter__.return_value = mock_client
        mock_client.upload_fileobj.side_effect = Exception("S3 upload failed")
        
        with pytest.raises(Exception) as exc_info:
            await s3_service.save_file(
                file=mock_file,
                file_name="test.txt",
                directory="test"
            )
        
        assert "S3 upload failed" in str(exc_info.value) 
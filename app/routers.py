# app/routers/s3_routes.py

import os
import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from app.service import S3FileService
from app.schemas import (
    OaasFolderRequest,
    OaasFileRequest,
    S3BucketContentType,
    S3UploadResponse,
    S3UploadFileBytesRequest
)
from app.auth import get_current_user, Trace

router = APIRouter()

# Read configuration from environment variables
S3_BUCKET_NAME = os.getenv("FILE_UPLOAD_BUCKET", "")
AWS_ACCESS_KEY_ID = os.getenv("FILE_UPLOAD_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("FILE_UPLOAD_ACCESS_KEY", "")

# Initialize the S3FileService instance.
s3_service = S3FileService(S3_BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

@router.post("/upload/oaas/folder", response_model=S3UploadResponse)
async def upload_oaas_folder(
    request: OaasFolderRequest,
    trace: Trace = Depends(get_current_user)
):
    """
    Upload a ZIP file to S3 and extract its contents maintaining folder structure.
    The ZIP file should contain product folders with images inside.

    Returns:
        S3UploadResponse: A list of S3 URLs for the uploaded files
    """
    file_urls = {}
    try:
        file_urls = await s3_service.save_oaas_folder(request)
        return {"s3_urls": file_urls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))  

@router.post("/upload/oaas/files", response_model=S3UploadResponse)
async def upload_oaas_files(
    request: OaasFileRequest,
    trace: Trace = Depends(get_current_user)
):
    """
    Upload individual files to S3 under the directory provided in request.

    Returns:
        S3UploadResponse: A list of S3 URLs for the uploaded files
    """
    file_urls = {}
    try:
        file_urls = await s3_service.save_oaas_files(request)
        return {"s3_urls": file_urls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload/oaas/files/v2", response_model=S3UploadResponse)
async def upload_oaas_files_v2(
    request: S3UploadFileBytesRequest,
    trace: Trace = Depends(get_current_user)
):
    """
    Upload binary image data for multiple products to S3.
    
    This endpoint accepts binary image data directly instead of URLs,
    allowing for more efficient file uploads without requiring pre-storage.
    
    Returns:
        S3UploadResponse: A dictionary mapping product codes to lists of S3 URLs
    """
    file_urls = {}
    try:
        file_urls = await s3_service.upload_product_bytes(request)
        return {"s3_urls": file_urls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
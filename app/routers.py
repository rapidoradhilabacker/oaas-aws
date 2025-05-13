# app/routers/s3_routes.py

import os
import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.service import S3FileService
from app.schemas import (
    OaasFolderRequest,
    OaasFileRequest,
    S3BucketContentType,
    S3UploadResponse
)
router = APIRouter()

# Read configuration from environment variables
S3_BUCKET_NAME = os.getenv("FILE_UPLOAD_BUCKET", "")
AWS_ACCESS_KEY_ID = os.getenv("FILE_UPLOAD_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("FILE_UPLOAD_ACCESS_KEY", "")

# Initialize the S3FileService instance.
s3_service = S3FileService(S3_BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

@router.post("/upload/oaas/folder", response_model=S3UploadResponse)
async def upload_oaas_folder(
    request: OaasFolderRequest
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
    request: OaasFileRequest
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
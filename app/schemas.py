from enum import Enum
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel

class InboundDocumentType(str, Enum):
    PDF = "application/pdf"
    IMAGE = "image/jpeg"
    ZIP = "application/zip"
    JSON = "application/json"
    PNG = "image/png"
    BINARY = "binary/octet-stream"

class Image(BaseModel):
    image_type: InboundDocumentType
    url: str

class ZipFolderInfo(BaseModel):
    url: str

class Product(BaseModel):
    tmp_code: str
    images: list[Image]

class User(BaseModel):
    mobile_no: str  
    company_name: Optional[str] = ""

class OaasFolderRequest(BaseModel):
    """
    Request model for uploading ZIP files containing product folders
    """
    user: User
    zip_folder: ZipFolderInfo
    tenant: str = 'placeorder'

class OaasFileRequest(BaseModel):
    """
    Request model for uploading individual product files
    """
    user: User
    product: Product
    tenant: str = 'placeorder'

class ImageBytes(BaseModel):
    """
    Model for image data with binary content
    """
    image_name: str
    image_type: InboundDocumentType
    image_bytes: str

class ProductBytes(BaseModel):
    """
    Model for product with binary image data
    """
    product_code: str
    images: list[ImageBytes]

class S3UploadFileBytesRequest(BaseModel):
    """
    Request model for uploading binary product files
    """
    user: User
    products: list[ProductBytes]
    tenant: str = 'placeorder'

class S3BucketContentType(str, Enum):
    PDF = "application/pdf"
    IMAGE = "image/jpeg"

class S3UploadResponse(BaseModel):
    """
    Response model for S3 upload endpoints
    """
    s3_urls: dict[str, list[str]]
    
    class Config:
        schema_extra = {
            "example": {
                "s3_urls": {
                    "product_code": [
                        "https://bucket-name.s3.region.amazonaws.com/path/to/file1.jpg",
                        "https://bucket-name.s3.region.amazonaws.com/path/to/file2.jpg"
                    ]
                }
            }
        }
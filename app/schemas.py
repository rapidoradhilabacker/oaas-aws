from enum import Enum
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel
from datetime import date
from typing import Optional
from pydantic.networks import HttpUrl
from humps import camelize
from typing import Any, Self

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

def to_camel(string):
    return camelize(string)

class CamelModel(BaseModel):
    class Config:
        alias_generator = to_camel
        populate_by_name = True

class SuccessCode(str, Enum):
   SUCCESS = '200'

class ErrorCode(str, Enum):
   ERROR_CODE_NA = ''
   ERROR_CODE_UNKNOWN = 'EONDC0000'
   ERROR_CODE_INVALID_REQUEST_ID = 'EONDC0001'
   ERROR_CODE_INVALID_TOKEN = 'EONDC0003'
   ERROR_CODE_INVALID_REQUEST = 'EONDC0007'
   ERROR_CODE_INTEGRATION_ERROR = 'EONDC0008'
   ERROR_CODE_AUTH_ERROR = 'EONDC0077'
   ERROR_CODE_ALREADY_EXISTS = 'EONDC0011'
   ERROR_CODE_DUPLICATE_REQUEST = 'EONDC0005'
   ERROR_CODE_ENTITY_NOT_EXIST = 'EONDC0006'
   ERROR_CODE_TIMEOUT = 'EONDC0010'

class GenericResponse(CamelModel):
    error_code: ErrorCode
    customer_message: str
    code: str
    status: bool
    debug_info: dict[str, Any] | None = None
    info: dict[str, Any] | None = None

    @classmethod
    def get_error_response(cls, error_code: ErrorCode, customer_message: str, debug_info: dict[str, Any] | None = None, info: dict[str, Any] | None = None):
        return GenericResponse(
            error_code=error_code,
            customer_message=customer_message,
            debug_info=debug_info,
            info=info,
            status=False,
            code=''
        )

    @classmethod
    def get_success_response(cls, customer_message: str, debug_info: dict[str, Any] | None = None, info: dict[str, Any] | None = None) -> Self:
        return cls(
            error_code=ErrorCode.ERROR_CODE_NA,
            customer_message=customer_message,
            debug_info=debug_info,
            info=info,
            status=True,
            code=SuccessCode.SUCCESS
        )

    @property
    def is_error_response(self):
        return not self.status


class Trace(BaseModel):
    request_id: str
    device_id: str
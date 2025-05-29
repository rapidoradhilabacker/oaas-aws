from pydantic_settings import BaseSettings
from functools import lru_cache
from enum import Enum
from pydantic import validator

class Settings(BaseSettings):
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = ""
    SERVICE_ID: str = ""

    class Config:
        env_prefix = 'API_'


class FileUploadSettings(BaseSettings):
    bucket: str = ""
    access_key: str = ""
    key_id: str = ""
    
    @validator('access_key', 'key_id')
    def validate_s3_credentials(cls, value, values):
        if not value:
            raise ValueError(f"'access_key' and 'key_id' cannot be None")
        return value

    class Config:
        env_prefix = 'FILE_UPLOAD_'


@lru_cache()
def get_settings():
    return Settings()

@lru_cache()
def get_file_upload_settings():
    return FileUploadSettings()

SETTINGS = get_settings()
FILE_UPLOAD_SETTINGS = get_file_upload_settings()
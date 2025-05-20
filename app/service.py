# app/services/s3_file_service.py

from enum import Enum
import hashlib
import aioboto3
from fastapi import UploadFile
import io
import typing
import aiohttp # Required for downloading files from URLs
from urllib.parse import urlparse
import os # For os.path.basename
from zipfile import ZipFile
from zipfile import BadZipFile
import time
from typing import Optional
from app.schemas import (
    S3BucketContentType, 
    User, 
    Product, 
    OaasFolderRequest,
    OaasFileRequest,
    InboundDocumentType,
    S3UploadFileBytesRequest
)
import base64

class S3FileService:
    def __init__(self, bucket_name: str, aws_access_key_id: str, aws_secret_access_key: str):
        self.bucket_name = bucket_name
        self.session = aioboto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )

    def _generate_key(self, directory: str, file_name: str) -> str:
        """
        Build the S3 key/path using the provided directory and filename.
        The resulting key will have the format: {directory}/{file_name}
        """
        # Ensure that the directory does not start or end with extra slashes
        directory = directory.strip("/ ")
        return f"{directory}/{file_name}"

    def _hash_string(self, input_string: str) -> str:
        """
        Generates a SHA256 hash for the given string.
        """
        return hashlib.sha256(input_string.encode('utf-8')).hexdigest()

    def get_oaas_directory(self, tenant: str, user: User, product_code: str) -> str:
        """
        Generate a directory path for storing OAAS files in S3.
        The directory path is constructed using the tenant, hashed mobile number,
        and product ID.
        """

        hashed_mobile_no = self._hash_string(user.mobile_no)
        return f"{tenant}/{hashed_mobile_no}/{product_code}"

    async def save_oaas_files(self, request: OaasFileRequest) -> dict[str, list[str]]:
        """
        Downloads images specified by URLs in the OaasFileRequest and saves them to S3.
        Sets the Content-Type for each file in S3 based on its InboundDocumentType.
        If the content_type is a ZIP file, extracts and processes all images within.
        Returns a dictionary mapping the product code to a list of S3 URLs.
        """
        user = request.user
        product_data = request.product
        tenant = request.tenant

        base_directory = self.get_oaas_directory(tenant, user, product_data.tmp_code)
        folder_urls: dict[str, list[str]] = {product_data.tmp_code: []}

        async with aiohttp.ClientSession() as http_session:
            for image_item in product_data.images:
                image_url_str = image_item.url
                content_type_value = image_item.image_type.value

                try:
                    async with http_session.get(image_url_str) as response:
                        response.raise_for_status()
                        content_bytes = await response.read()

                    parsed_url = urlparse(image_url_str)
                    file_name_from_url = os.path.basename(parsed_url.path)

                    # Check if content is a ZIP file
                    # is_zip = content_type_value == 'application/zip' or content_type_value == 'application/x-zip-compressed' or file_name_from_url.lower().endswith('.zip')
                    is_zip = image_item.image_type == InboundDocumentType.ZIP
                    if is_zip:
                        # Process ZIP file
                        try:
                            zip_buffer = io.BytesIO(content_bytes)
                            with ZipFile(zip_buffer) as zip_ref:
                                # Process each file in the ZIP
                                for file_path in zip_ref.namelist():
                                    if file_path.endswith('/'):  # Skip directories
                                        continue
                                        
                                    try:
                                        # Extract file content
                                        file_content = zip_ref.read(file_path)
                                        original_filename = os.path.basename(file_path)
                                        
                                        if not original_filename:
                                            continue
                                            
                                        # Determine content type based on file extension
                                        file_ext = os.path.splitext(original_filename)[1].lower()
                                        img_content_type = {
                                            '.pdf': InboundDocumentType.PDF.value, 
                                            '.jpg': InboundDocumentType.IMAGE.value,
                                            '.jpeg': InboundDocumentType.IMAGE.value,
                                            '.png': InboundDocumentType.PNG.value,
                                        }.get(file_ext, InboundDocumentType.BINARY.value)
                                        
                                        # Upload file to S3
                                        file_stream = io.BytesIO(file_content)
                                        s3_url = await self.save_file(
                                            file_content_stream=file_stream,
                                            file_name=original_filename,
                                            directory=base_directory,
                                            content_type_str=img_content_type
                                        )
                                        folder_urls[product_data.tmp_code].append(s3_url)
                                    except Exception as e:
                                        folder_urls[product_data.tmp_code].append(f"Error processing file {file_path} from ZIP: {str(e)}")
                        except BadZipFile:
                            folder_urls[product_data.tmp_code].append(f"Invalid ZIP file format: {image_url_str}")
                    else:
                        # Process as a regular image file
                        if not file_name_from_url:
                            url_hash_suffix = hashlib.sha1(image_url_str.encode()).hexdigest()[:8]
                            extension = content_type_value.split('/')[-1]
                            if extension == "octet-stream":
                                extension = "bin"
                            elif extension == "jpeg":
                                extension = "jpg"
                            file_name_from_url = f"image_{url_hash_suffix}.{extension}"

                        image_content_stream = io.BytesIO(content_bytes)
                        
                        s3_url = await self.save_file(
                            file_content_stream=image_content_stream,
                            file_name=file_name_from_url,
                            directory=base_directory,
                            content_type_str=content_type_value
                        )
                        folder_urls[product_data.tmp_code].append(s3_url)
                except aiohttp.ClientError as e:
                    folder_urls[product_data.tmp_code].append(f"Error downloading {image_url_str}: {str(e)}")
                except Exception as e:
                    folder_urls[product_data.tmp_code].append(f"Error processing {image_url_str}: {str(e)}")
        return folder_urls

    async def save_oaas_folder(self, request: OaasFolderRequest) -> dict[str, list[str]]:
        """
        Downloads a ZIP file from the URL in the request, extracts its contents,
        and saves the extracted files to S3 maintaining the folder structure.
        Returns a dictionary mapping folder names to lists of S3 URLs for files in that folder.
        """
        start_time = time.perf_counter()
        folder_urls: dict[str, list[str]] = {}  # Dictionary with folder name as key and list of URLs as value
        user = request.user
        tenant = request.tenant

        try:
            # Download the zip file
            async with aiohttp.ClientSession() as http_session:
                async with http_session.get(request.zip_folder.url) as response:
                    response.raise_for_status()
                    zip_content = await response.read()

            # Create a BytesIO object from the zip content
            zip_buffer = io.BytesIO(zip_content)

            # Process the zip file
            with ZipFile(zip_buffer) as zip_ref:
                # Group files by their parent folders
                folder_files: dict[str, list[str]] = {}
                for file_path in zip_ref.namelist():
                    if file_path.endswith('/'):  # Skip directories
                        continue
                    parent_folder = os.path.dirname(file_path).split('/')[-1]
                    if not parent_folder:  # Skip files in root
                        continue
                    if parent_folder not in folder_files:
                        folder_files[parent_folder] = []
                    folder_files[parent_folder].append(file_path)

                # Process each folder and its files
                for folder_name, files in folder_files.items():
                    # Initialize list for this folder's URLs
                    folder_urls[folder_name] = []
                    
                    # Create S3 directory path for this folder
                    folder_directory = self.get_oaas_directory(tenant, user, folder_name)

                    # Process each file in the folder
                    for file_path in files:
                        try:
                            # Extract file content
                            file_content = zip_ref.read(file_path)
                            original_filename = os.path.basename(file_path)
                            name, ext = os.path.splitext(original_filename)
                            
                            # Generate timestamp in format: YYYYMMDD_HHMMSS
                            timestamp = time.strftime('%Y%m%d_%H%M%S')
                            
                            # Combine timestamp and original filename
                            file_name = f"{name}_{timestamp}{ext}"

                            # Determine content type based on file extension
                            file_ext = os.path.splitext(file_name)[1].lower()
                            content_type = {
                                '.pdf': InboundDocumentType.PDF.value, 
                                '.jpg': InboundDocumentType.IMAGE.value,
                                '.jpeg': InboundDocumentType.IMAGE.value,
                                '.png': InboundDocumentType.PNG.value,
                            }.get(file_ext, InboundDocumentType.BINARY.value)

                            # Upload file to S3
                            file_stream = io.BytesIO(file_content)
                            s3_url = await self.save_file(
                                file_content_stream=file_stream,
                                file_name=file_name,
                                directory=folder_directory,
                                content_type_str=content_type
                            )
                            # Add URL to the folder's list
                            folder_urls[folder_name].append(s3_url)

                        except Exception as e:
                            # Add error message to the folder's list
                            folder_urls[folder_name].append(f"Error processing file {file_path}: {str(e)}")
                            continue

            end_time = time.perf_counter()
            print(f"Time taken to process zip file: {end_time - start_time} seconds")
            return folder_urls

        except aiohttp.ClientError as e:
            raise Exception(f"Failed to fetch zip file: {str(e)}")
        except BadZipFile:
            raise Exception("Invalid zip file format")
        except Exception as e:
            raise Exception(f"Error processing zip file: {str(e)}")

    async def save_file(self, file_content_stream: typing.BinaryIO, file_name: str, directory: str, content_type_str: typing.Optional[str] = None) -> str:
        """
        Save the file content stream to S3 under the provided directory and return the public URL.
        Optionally sets the Content-Type of the S3 object.
        """
        s3_key = self._generate_key(directory, file_name)
        extra_args = {}
        if content_type_str:
            extra_args['ContentType'] = content_type_str

        async with self.session.client('s3') as s3_client:
            bucket_location = await s3_client.get_bucket_location(Bucket=self.bucket_name)
            # Ensure stream is at the beginning if it's seekable (like BytesIO)
            if hasattr(file_content_stream, 'seek') and callable(file_content_stream.seek):
                file_content_stream.seek(0)
            await s3_client.upload_fileobj(
                file_content_stream, # Use the stream directly
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )
            region = bucket_location.get('LocationConstraint')
            if region is None: # us-east-1 returns None for LocationConstraint
                s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
            else:
                s3_url = f"https://{self.bucket_name}.s3-{region}.amazonaws.com/{s3_key}"
            return s3_url
        

    async def save_file_with_content_type(self, file: UploadFile, file_name: str, content_type: S3BucketContentType, directory: str) -> str:
        """
        Save the file to S3 with a specified content type under the provided directory
        and return the public URL.
        """
        s3_key = self._generate_key(directory, file_name)
        async with self.session.client('s3') as s3_client:
            bucket_location = await s3_client.get_bucket_location(Bucket=self.bucket_name)
            await s3_client.upload_fileobj(
                file.file,
                self.bucket_name,
                s3_key,
                ExtraArgs={'ACL': 'public-read', 'ContentType': content_type.value}
            )
            s3_url = (
                f"https://{self.bucket_name}.s3-{bucket_location['LocationConstraint']}.amazonaws.com/{s3_key}"
            )
            return s3_url

    async def save_file_with_validity(self, source: str, file_name: str, directory: str) -> str:
        """
        Upload a file from a local source to S3 under the provided directory,
        then return a presigned URL valid for 600 seconds.
        """
        s3_key = self._generate_key(directory, file_name)
        async with self.session.client('s3') as s3_client:
            bucket_location = await s3_client.get_bucket_location(Bucket=self.bucket_name)
            await s3_client.upload_file(source, self.bucket_name, s3_key)
            s3_url = await s3_client.generate_presigned_url(
                ClientMethod='get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=600
            )
            return s3_url
    
    async def upload_file_bytes(self, file_bytes: bytes, file_name: str, directory: str, content_type_str: Optional[str] = None) -> str:
        """
        Save the file bytes to S3 under the provided directory and return the public URL.
        Optionally sets the Content-Type of the S3 object.
        """
        s3_key = self._generate_key(directory, file_name)
        extra_args = {}
        if content_type_str:
            extra_args['ContentType'] = content_type_str
        
        async with self.session.client('s3') as s3_client:
            bucket_location = await s3_client.get_bucket_location(Bucket=self.bucket_name)
            file_stream = io.BytesIO(file_bytes)
            await s3_client.upload_fileobj(
                file_stream,
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )
            region = bucket_location.get('LocationConstraint')
            if region is None:  # us-east-1 returns None for LocationConstraint
                s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
            else:
                s3_url = f"https://{self.bucket_name}.s3-{region}.amazonaws.com/{s3_key}"
            return s3_url
    
    async def upload_product_bytes(self, request: S3UploadFileBytesRequest) -> dict[str, list[str]]:
        """
        Uploads binary image data for multiple products to S3.
        Returns a dictionary mapping product codes to lists of S3 URLs.
        """
        user = request.user
        tenant = request.tenant
        result_urls: dict[str, list[str]] = {}
        
        for product in request.products:
            product_code = product.product_code
            base_directory = self.get_oaas_directory(tenant, user, product_code)
            result_urls[product_code] = []
            
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            for image in product.images:
                try:
                    ext = image.image_name.split('.')[-1]
                    file_name = image.image_name.split('.')[0]
                    image_name = f"{file_name}_{timestamp}.{ext}"
                    image_bytes = base64.b64decode(image.image_bytes)
                    s3_url = await self.upload_file_bytes(
                        file_bytes=image_bytes,
                        file_name=image_name,
                        directory=base_directory,
                        content_type_str=image.image_type.value
                    )
                    result_urls[product_code].append(s3_url)
                except Exception as e:
                    print(f"Error uploading {image.image_name} for product {product_code}: {str(e)}")
                    # Continue with other images even if one fails
        
        return result_urls

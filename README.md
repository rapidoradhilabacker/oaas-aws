# FastAPI AWS S3 File Upload Service

This project is a FastAPI application designed to handle file uploads to an AWS S3 bucket. It provides several endpoints for different upload scenarios, including direct file uploads, uploads from URLs, and generating presigned URLs for uploaded objects.

## Features

*   Upload files directly to S3.
*   Upload files from URLs specified in a request.
*   Upload and extract ZIP files maintaining folder structure.
*   Specify content type for uploaded files.
*   Generate presigned URLs for S3 objects with a defined validity period.
*   Organize files in S3 using a directory structure based on tenant, user, and product information.
*   Securely handles AWS credentials.

## Prerequisites

*   Python 3.8+
*   pip (Python package installer)
*   An AWS account with an S3 bucket.
*   AWS Access Key ID and Secret Access Key with permissions to access the S3 bucket.

## Project Structure

```
.
├── app/
│   ├── main.py           # FastAPI application entry point
│   ├── routers.py        # API route definitions
│   ├── schemas.py        # Pydantic models for request/response
│   ├── service.py        # S3 service implementation
│   └── utils.py          # Utility functions
├── tests/               # Test directory
│   ├── __init__.py
│   ├── conftest.py      # pytest configurations
│   ├── test_routes.py   # API endpoint tests
│   └── test_service.py  # S3 service unit tests
├── requirements.txt     # Project dependencies
└── README.md           # Project documentation
```

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd <your-repository-name>
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(You'll need to create a `requirements.txt` file. Based on the imports, it should at least contain `fastapi`, `uvicorn`, `aioboto3`, `aiohttp`, `pydantic`)*

4.  **Configure Environment Variables:**
    Create a `.env` file in the root directory of the project or set the following environment variables in your system:

    ```env
    FILE_UPLOAD_BUCKET="your-s3-bucket-name"
    FILE_UPLOAD_KEY_ID="your-aws-access-key-id"
    FILE_UPLOAD_ACCESS_KEY="your-aws-secret-access-key"
    ```
    Replace the placeholder values with your actual AWS S3 bucket name and credentials.

## API Endpoints

### 1. Upload File (`POST /s3/upload`)
Upload a single file to S3 with a specified directory.

**Form Data:**
- `file`: File to upload
- `file_name`: Name for the file in S3
- `directory`: Target directory in S3

### 2. Upload with Content Type (`POST /s3/upload/content-type`)
Upload a file with a specific content type.

**Form Data:**
- `file`: File to upload
- `file_name`: (Optional) Name for the file in S3
- `content_type`: Content type for the file
- `directory`: Target directory in S3

### 3. Upload OAAS Folder (`POST /s3/upload/oaas/folder`)
Upload and extract a ZIP file maintaining folder structure.

**Request Body:**
- JSON object with folder structure specifications

### 4. Upload OAAS Files (`POST /s3/upload/oaas/files`)
Upload multiple files under a specified directory.

**Request Body:**
- JSON object with file specifications

### 5. Generate Presigned URL (`POST /s3/upload/presigned`)
Generate a presigned URL for temporary file access.

**Form Data:**
- `source`: Source path or URL
- `file_name`: Name for the file in S3

## Running the Application

To run the FastAPI application locally, use Uvicorn:

```bash
uvicorn app.main:app --reload

```

The API will be available at `http://localhost:8000`. Access the interactive API documentation at `http://localhost:8000/docs`.

## Testing

The project uses pytest for testing. Install test dependencies:

```bash
pip install pytest pytest-asyncio pytest-cov
```

Run tests:

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=app tests/

# Run specific test file
pytest tests/test_routes.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

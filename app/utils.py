

from zipfile import ZipFile
from app.schemas import InboundDocumentType
from fastapi import HTTPException
from io import BytesIO
from zipfile import BadZipFile

async def extract_images(
    file_bytes: bytes, content_type: str
) -> tuple[list[bytes], list[str]]:
    """
    If zip archive, extract all image files; otherwise, return single file.
    """
    if content_type.lower() == InboundDocumentType.ZIP:
        try:
            with ZipFile(BytesIO(file_bytes)) as zf:
                image_names = [f for f in zf.namelist() if f.lower().endswith((
                    ".png", ".jpg", ".jpeg", ".gif", ".bmp"
                ))]
                if not image_names:
                    raise HTTPException(
                        status_code=400,
                        detail="No image files found in ZIP archive"
                    )
                images = [zf.read(name) for name in image_names]
                return images, image_names
        except BadZipFile:
            raise HTTPException(status_code=400, detail="Invalid ZIP archive")
    # Non-zip: return raw bytes
    return [file_bytes], []
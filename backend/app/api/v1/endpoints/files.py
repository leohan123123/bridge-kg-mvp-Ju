import os
import shutil
from typing import List
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, constr
import datetime

router = APIRouter()

UPLOAD_DIR = "backend/app/files"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS = {".dxf", ".pdf", ".ifc"}

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)

class FileUploadResponse(BaseModel):
    filename: str
    content_type: str
    size: int
    saved_path: str
    uploaded_at: datetime.datetime

@router.post("/upload", response_model=List[FileUploadResponse])
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Handles uploading of multiple files.
    Validates file types and sizes.
    Saves files to the specified directory.
    """
    uploaded_files_info = []
    for file in files:
        # Validate file extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.filename}. Allowed types are {', '.join(ALLOWED_EXTENSIONS)}."
            )

        # Validate file size
        if file.size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large: {file.filename}. Maximum size is {MAX_FILE_SIZE / (1024 * 1024)}MB."
            )

        try:
            # Sanitize filename (optional, but good practice)
            # For simplicity, we'll use the original filename.
            # Consider using a library like `werkzeug.utils.secure_filename` for more robust sanitization.
            filename = file.filename
            file_path = os.path.join(UPLOAD_DIR, filename)

            # Save the file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            uploaded_at = datetime.datetime.now()
            file_info = FileUploadResponse(
                filename=filename,
                content_type=file.content_type,
                size=file.size,
                saved_path=file_path,
                uploaded_at=uploaded_at
            )
            uploaded_files_info.append(file_info)

        except Exception as e:
            # Log the error e
            raise HTTPException(
                status_code=500,
                detail=f"Could not upload file: {file.filename}. Error: {str(e)}"
            )
        finally:
            await file.close() # Ensure the file is closed

    if not uploaded_files_info:
        raise HTTPException(status_code=400, detail="No files were uploaded.")

    return uploaded_files_info

import os
import shutil
from typing import List, Dict, Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, constr
import datetime

# Assuming services are in the correct path for import
# from backend.app.services.bim_knowledge_builder import BIMKnowledgeBuilder
# For local testing, direct import might work if PYTHONPATH is set or they are in same dir:
try:
    from ...services.bim_knowledge_builder import BIMKnowledgeBuilder
except ImportError: # Fallback for different execution contexts
    # This relative import path should work when 'files.py' is run as part of the 'app' module
    from app.services.bim_knowledge_builder import BIMKnowledgeBuilder


router = APIRouter()

UPLOAD_DIR = "backend/app/files" # This path might need to be relative to the project root if run from there
# Ensure UPLOAD_DIR is correct based on where the app is started.
# If app is started from 'backend', then 'app/files' might be more appropriate.
# For now, assuming 'backend/app/files' is accessible from the running directory.
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS = {".dxf", ".pdf", ".ifc"}


class FileUploadResponse(BaseModel):
    filename: str
    content_type: str
    size: int
    saved_path: str
    uploaded_at: datetime.datetime
    processing_result: Optional[Dict] = None # To hold results from IFC parsing

# Initialize BIMKnowledgeBuilder instance
# This should ideally be managed with dependency injection for larger apps
bim_knowledge_builder = BIMKnowledgeBuilder()

def process_ifc_file(file_path: str) -> Dict:
    """
    Processes an IFC file using BIMKnowledgeBuilder.
    Returns the knowledge graph data or an error dictionary.
    """
    try:
        knowledge_data = bim_knowledge_builder.build_knowledge_from_bim(file_path)
        return knowledge_data
    except Exception as e:
        # Log the exception e
        return {"error": f"Failed to process IFC file: {str(e)}"}


@router.post("/upload", response_model=List[FileUploadResponse])
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Handles uploading of multiple files.
    Validates file types and sizes.
    Saves files and processes .ifc files.
    """
    uploaded_files_info = []
    for file in files:
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            await file.close() # Close file before raising exception
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.filename}. Allowed types are {', '.join(ALLOWED_EXTENSIONS)}."
            )

        if file.size > MAX_FILE_SIZE:
            await file.close() # Close file
            raise HTTPException(
                status_code=413,
                detail=f"File too large: {file.filename}. Maximum size is {MAX_FILE_SIZE / (1024 * 1024)}MB."
            )

        processing_output = None
        try:
            filename = file.filename # Consider sanitizing filename
            # Ensure UPLOAD_DIR is correctly resolved. If app root is project root, 'backend/app/files' is fine.
            # If app root is 'backend', then 'app/files' might be better.
            # For now, assume UPLOAD_DIR is correctly set.
            file_path = os.path.join(UPLOAD_DIR, filename)

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            uploaded_at = datetime.datetime.now()

            if file_ext == ".ifc":
                # Process the IFC file
                processing_output = process_ifc_file(file_path)

            file_info = FileUploadResponse(
                filename=filename,
                content_type=file.content_type,
                size=file.size,
                saved_path=file_path,
                uploaded_at=uploaded_at,
                processing_result=processing_output
            )
            uploaded_files_info.append(file_info)

        except Exception as e:
            # Log the error e
            # Ensure file is closed if an error occurs after opening it but before explicit close
            if not file.file.closed:
                 await file.close()
            raise HTTPException(
                status_code=500,
                detail=f"Could not upload file: {file.filename}. Error: {str(e)}"
            )
        finally:
            await file.close() # Ensure the file is closed

    if not uploaded_files_info:
        raise HTTPException(status_code=400, detail="No files were uploaded.")

    return uploaded_files_info

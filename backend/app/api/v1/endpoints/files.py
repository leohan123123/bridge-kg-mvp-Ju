import os
import shutil
from typing import List, Dict
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, constr
import datetime
import logging

# Assuming WordParserService and WordContentAnalyzer are structured to be importable
from app.services.word_parser_service import WordParserService
# WordContentAnalyzer might not be directly called here if process_word_document is simple
# and KnowledgeGraphEngine handles the deeper analysis.
# from app.services.word_content_analyzer import WordContentAnalyzer


router = APIRouter()
logger = logging.getLogger(__name__)

UPLOAD_DIR = "backend/app/files"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
# Updated ALLOWED_EXTENSIONS
ALLOWED_EXTENSIONS = {".dxf", ".pdf", ".ifc", ".doc", ".docx"}
WORD_EXTENSIONS = {".doc", ".docx"}

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)

class FileUploadResponse(BaseModel):
    filename: str
    content_type: str
    size: int
    saved_path: str
    uploaded_at: datetime.datetime
    processing_result: Dict = None # To include results from process_word_document

# Helper function to process Word documents
def process_word_document(file_path: str) -> Dict:
    """
    Processes a Word document using WordParserService.
    This is a simplified version. In a real scenario, you might also call WordContentAnalyzer
    or this logic could be deeper within a service like KnowledgeGraphEngine.
    """
    try:
        parser = WordParserService()
        # Basic extraction. More detailed analysis might be needed depending on requirements.
        text_content = parser.extract_text_content(file_path)
        tables = parser.extract_tables(file_path)
        # Headers and images could also be extracted if needed at this stage
        # headers = parser.extract_headers_and_sections(file_path)
        # images = parser.extract_images_info(file_path)

        # For now, return a summary. The KnowledgeGraphEngine will do more detailed analysis.
        return {
            "status": "success",
            "message": "Word document parsed. Basic content extracted.",
            "filename": os.path.basename(file_path),
            "text_snippet": text_content.get("text", "")[:200] + "..." if text_content.get("text") else "N/A",
            "metadata": text_content.get("metadata", {}),
            "table_count": len(tables),
            # "header_count": len(headers.get("headers", [])),
            # "image_count": len(images)
        }
    except HTTPException as http_exc: # Catch HTTPExceptions from parser
        logger.error(f"HTTPException during Word document processing for {file_path}: {http_exc.detail}")
        raise http_exc # Re-raise to be handled by FastAPI
    except Exception as e:
        logger.error(f"Error processing Word document {file_path}: {e}")
        # Return an error structure or raise HTTPException
        # Raising HTTPException is consistent with other error handling in this file
        raise HTTPException(status_code=500, detail=f"Failed to process Word document {os.path.basename(file_path)}: {str(e)}")


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
            processing_data = None

            # If it's a Word document, call process_word_document
            if file_ext in WORD_EXTENSIONS:
                logger.info(f"Processing Word document: {filename}")
                try:
                    # This call is synchronous. For long parsing tasks, consider background tasks.
                    processing_data = process_word_document(file_path)
                except HTTPException as http_exc: # Catch specific HTTP errors from processing
                    logger.error(f"HTTPException while processing Word file {filename}: {http_exc.detail}")
                    # We might want to decide if a processing failure for one file fails the whole upload batch
                    # or if it just logs error for that file and continues.
                    # For now, let it be part of the response for that file.
                    processing_data = {"status": "error", "detail": http_exc.detail, "filename": filename}
                except Exception as e:
                    logger.error(f"Generic error while processing Word file {filename}: {str(e)}")
                    processing_data = {"status": "error", "detail": f"Failed to process: {str(e)}", "filename": filename}


            file_info = FileUploadResponse(
                filename=filename,
                content_type=file.content_type,
                size=file.size,
                saved_path=file_path,
                uploaded_at=uploaded_at,
                processing_result=processing_data # Add processing result here
            )
            uploaded_files_info.append(file_info)

        except HTTPException as http_e: # Re-raise HTTPExceptions directly
            raise http_e
        except Exception as e:
            logger.error(f"Could not upload or process file: {file.filename}. Error: {str(e)}")
            # Ensure a consistent error response for upload failures.
            # The current FileUploadResponse doesn't have a top-level error field for the file itself,
            # but processing_result can hold error info for the processing step.
            # If the upload itself fails (before processing), it raises HTTPException.
            raise HTTPException(
                status_code=500,
                detail=f"Could not upload file: {file.filename}. Error: {str(e)}"
            )
        finally:
            await file.close() # Ensure the file is closed

    if not uploaded_files_info:
        raise HTTPException(status_code=400, detail="No files were uploaded.")

    return uploaded_files_info

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
from app.services.drawing_knowledge_extractor import DrawingKnowledgeExtractor
from app.services.bim_knowledge_builder import BIMKnowledgeBuilder


router = APIRouter()
logger = logging.getLogger(__name__)

UPLOAD_DIR = "backend/app/files"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
# Updated ALLOWED_EXTENSIONS
ALLOWED_EXTENSIONS = {".dxf", ".pdf", ".ifc", ".doc", ".docx"}
WORD_EXTENSIONS = {".doc", ".docx"}
DXF_EXTENSIONS = {".dxf"}
IFC_EXTENSIONS = {".ifc"}

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)

class FileUploadResponse(BaseModel):
    filename: str
    content_type: str
    size: int
    saved_path: str
    uploaded_at: datetime.datetime
    processing_result: Dict = None # To include results from processing functions

# Helper function to process Word documents
def process_word_document(file_path: str) -> Dict:
    """
    Processes a Word document using WordParserService.
    """
    try:
        parser = WordParserService()
        text_content = parser.extract_text_content(file_path)
        tables = parser.extract_tables(file_path)
        return {
            "status": "success",
            "message": "Word document parsed. Basic content extracted.",
            "filename": os.path.basename(file_path),
            "text_snippet": text_content.get("text", "")[:200] + "..." if text_content.get("text") else "N/A",
            "metadata": text_content.get("metadata", {}),
            "table_count": len(tables),
        }
    except HTTPException as http_exc:
        logger.error(f"HTTPException during Word document processing for {file_path}: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Error processing Word document {file_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process Word document {os.path.basename(file_path)}: {str(e)}")

# Helper function to process DXF documents
def process_dxf_file(file_path: str) -> Dict:
    """
    Processes a DXF drawing file using DrawingKnowledgeExtractor.
    """
    try:
        extractor = DrawingKnowledgeExtractor()
        # The extractor returns a comprehensive dictionary including errors if any.
        knowledge_data = extractor.extract_knowledge_from_drawing(file_path)

        if knowledge_data.get("error"):
            logger.error(f"Error processing DXF file {file_path}: {knowledge_data['error']}")
            # We could raise HTTPException here, but extractor already provides an error structure.
            # For consistency in FileUploadResponse, let's ensure processing_result reflects this.
            return {
                "status": "error",
                "message": f"Failed to process DXF file: {knowledge_data['error']}",
                "filename": os.path.basename(file_path),
                "detail": knowledge_data['error']
            }

        # Return a summary or the full extracted knowledge as needed
        # For now, let's return a success status and the main parts of the extracted data.
        return {
            "status": "success",
            "message": "DXF file processed and knowledge extracted.",
            "filename": os.path.basename(file_path),
            "document_info": knowledge_data.get("document_info"),
            "analysis_summary": knowledge_data.get("analysis_summary"),
            # Optionally include "knowledge_graph" or "raw_parsed_data" if the frontend needs it directly
            # "knowledge_graph_summary": {
            #     "nodes_count": len(knowledge_data.get("knowledge_graph", {}).get("nodes", [])),
            #     "edges_count": len(knowledge_data.get("knowledge_graph", {}).get("edges", []))
            # }
        }
    except HTTPException as http_exc: # Catch any HTTPExceptions raised within the extractor flow if any
        logger.error(f"HTTPException during DXF file processing for {file_path}: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error processing DXF file {file_path}: {e}")
        # Raise HTTPException for unexpected errors to ensure a proper FastAPI response
        raise HTTPException(status_code=500, detail=f"Unexpected error processing DXF file {os.path.basename(file_path)}: {str(e)}")

# Helper function to process IFC files
def process_ifc_file(file_path: str) -> Dict:
    """
    Processes an IFC BIM file using BIMKnowledgeBuilder.
    """
    try:
        builder = BIMKnowledgeBuilder()
        # This call is synchronous. For very large IFC files, consider background tasks.
        knowledge_data = builder.build_knowledge_from_bim(file_path)

        if knowledge_data.get("error"):
            logger.error(f"Error processing IFC file {file_path}: {knowledge_data['error']}")
            return {
                "status": "error",
                "message": f"Failed to process IFC file: {knowledge_data['error']}",
                "filename": os.path.basename(file_path),
                "detail": knowledge_data['error']
            }

        # Return a summary of the extracted knowledge graph
        return {
            "status": "success",
            "message": "IFC file processed and knowledge graph built.",
            "filename": os.path.basename(file_path),
            "knowledge_graph_summary": {
                "nodes_count": len(knowledge_data.get("nodes", [])),
                "relationships_count": len(knowledge_data.get("relationships", []))
            },
            # Optionally, include parts of the graph if small, or specific insights
            # "project_name": next((n['properties'].get('name') for n in knowledge_data.get("nodes", []) if n['type'] == 'Project'), None)
        }
    except HTTPException as http_exc:
        logger.error(f"HTTPException during IFC file processing for {file_path}: {http_exc.detail}")
        raise http_exc # Re-raise if it's already an HTTPException
    except Exception as e:
        logger.error(f"Unexpected error processing IFC file {file_path}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Unexpected error processing IFC file {os.path.basename(file_path)}: {str(e)}")


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

            # Process file based on extension
            if file_ext in WORD_EXTENSIONS:
                logger.info(f"Processing Word document: {filename}")
                try:
                    processing_data = process_word_document(file_path)
                except HTTPException as http_exc:
                    logger.error(f"HTTPException while processing Word file {filename}: {http_exc.detail}")
                    processing_data = {"status": "error", "detail": http_exc.detail, "filename": filename}
                except Exception as e:
                    logger.error(f"Generic error while processing Word file {filename}: {str(e)}")
                    processing_data = {"status": "error", "detail": f"Failed to process: {str(e)}", "filename": filename}

            elif file_ext in DXF_EXTENSIONS:
                logger.info(f"Processing DXF file: {filename}")
                try:
                    # This call is synchronous. For long parsing tasks, consider background tasks.
                    processing_data = process_dxf_file(file_path)
                except HTTPException as http_exc:
                    logger.error(f"HTTPException while processing DXF file {filename}: {http_exc.detail}")
                    processing_data = {"status": "error", "detail": http_exc.detail, "filename": filename}
                except Exception as e:
                    logger.error(f"Generic error while processing DXF file {filename}: {str(e)}")
                    processing_data = {"status": "error", "detail": f"Failed to process: {str(e)}", "filename": filename}

            elif file_ext in IFC_EXTENSIONS:
                logger.info(f"Processing IFC file: {filename}")
                try:
                    processing_data = process_ifc_file(file_path)
                except HTTPException as http_exc:
                    logger.error(f"HTTPException while processing IFC file {filename}: {http_exc.detail}")
                    processing_data = {"status": "error", "detail": http_exc.detail, "filename": filename}
                except Exception as e:
                    logger.error(f"Generic error while processing IFC file {filename}: {str(e)}")
                    processing_data = {"status": "error", "detail": f"Failed to process: {str(e)}", "filename": filename}


            # Placeholder for other file types (PDF)
            # elif file_ext == ".pdf":
            #     logger.info(f"PDF file {filename} received. Processing not yet implemented.")
            #     processing_data = {"status": "pending", "message": "PDF processing not implemented."}


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

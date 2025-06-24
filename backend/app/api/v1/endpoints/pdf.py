from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
import os

from app.services.pdf_service import extract_text_from_pdf
from app.core.config import settings

router = APIRouter()

class PDFExtractRequest(BaseModel):
    file_path: str

class PDFExtractResponse(BaseModel):
    text: str
    length: int

@router.post("/extract", response_model=PDFExtractResponse)
async def extract_pdf_text(request_body: PDFExtractRequest = Body(...)):
    """
    Extracts text from an uploaded PDF file.
    """
    # Construct the full file path relative to the UPLOAD_DIR
    full_file_path = os.path.join(settings.UPLOAD_DIR, request_body.file_path)

    if not os.path.exists(full_file_path):
        raise HTTPException(status_code=404, detail="File not found.")
    if not request_body.file_path.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are supported.")

    extracted_text = extract_text_from_pdf(full_file_path)

    if extracted_text.startswith("Error:"):
        # Handle errors from pdf_service
        if "File not found" in extracted_text:
             raise HTTPException(status_code=404, detail=extracted_text)
        elif "File is not a PDF" in extracted_text:
             raise HTTPException(status_code=400, detail=extracted_text)
        else:
             raise HTTPException(status_code=500, detail=extracted_text)

    return PDFExtractResponse(text=extracted_text, length=len(extracted_text))

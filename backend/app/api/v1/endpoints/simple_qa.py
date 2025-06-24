from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any

from backend.app.services.simple_rag_service import SimpleRAGService
# Ensure ai_service exceptions can be caught if necessary, though SimpleRAGService should handle them
from backend.app.services.ai_service import AIServiceError

router = APIRouter()

class QAQuery(BaseModel):
    question: str

# Initialize the service.
# For a stateless service like this, initializing once can be efficient.
# If the service had state or required complex setup, dependency injection (FastAPI's Depends) would be better.
rag_service = SimpleRAGService()

@router.post("/ask", response_model=Dict[str, Any])
async def ask_question(query: QAQuery = Body(...)):
    """
    Receives a question, uses the SimpleRAGService to get an answer
    based on knowledge graph context and AI generation.
    """
    if not query.question or not query.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        # The answer_question method is async
        answer_response = await rag_service.answer_question(question=query.question)

        # The answer_response from SimpleRAGService is expected to be a dict,
        # potentially with an 'error' key if something went wrong in the service.
        if answer_response.get("error"):
            # If the service handled an error and returned a structured error response
            error_content = answer_response.get("message", {}).get("content", "An unknown error occurred in the RAG service.")
            raise HTTPException(status_code=500, detail=error_content)

        return answer_response

    except AIServiceError as e:
        # This catches errors specifically from the AI service if not handled by SimpleRAGService
        print(f"AI Service Error in endpoint: {e}")
        raise HTTPException(status_code=e.status_code or 503, detail=str(e))
    except Exception as e:
        # Catch-all for other unexpected errors
        print(f"Unexpected error in /ask endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# Example of how to add more related endpoints if needed in the future
# @router.get("/history")
# async def get_qa_history():
#     # Placeholder for future functionality
#     return {"message": "QA history endpoint not yet implemented."}

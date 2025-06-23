from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from backend.app.services.ai_service import get_ollama_chat_response, OllamaError
from backend.app.core.config import settings # For default model if specified

router = APIRouter()

# --- Pydantic Models ---
class AIChatRequest(BaseModel):
    message: str = Field(..., description="The user's message to the AI.")
    context: Optional[str] = Field(None, description="Optional context to provide to the AI.")
    model: Optional[str] = Field(None, description="Optional Ollama model to use (e.g., 'qwen2.5:7b'). Uses system default if not provided.")
    knowledge_enhanced: Optional[bool] = Field(False, description="Whether to enhance the response with knowledge graph data.")
    # stream: bool = Field(False, description="Whether to stream the response.") # Streaming not implemented yet

class AIChatResponse(BaseModel):
    role: str = Field(description="The role of the responder (e.g., 'assistant').")
    content: str = Field(description="The AI's response content.")
    model_used: str = Field(description="The Ollama model that generated the response.")
    data_source: Optional[str] = Field(None, description="Indicates the source of data if knowledge graph was used (e.g., 'Knowledge Graph').")
    # additional_info: Optional[Dict[str, Any]] = Field(None, description="Additional information from the Ollama response if any.")


@router.post("/chat", response_model=AIChatResponse)
async def handle_ai_chat(
    request: AIChatRequest = Body(...)
):
    """
    Receives a user message and optional context, communicates with the
    Ollama service, and returns the AI's response.
    Optionally enhances the response with data from the knowledge graph.
    """
    try:
        selected_model = request.model or getattr(settings, 'OLLAMA_DEFAULT_MODEL', "qwen2:0.5b")
        data_source_used = None

        # Call the AI service, passing the knowledge_enhanced flag
        ollama_response = await get_ollama_chat_response(
            message=request.message,
            context=request.context,
            model=selected_model,
            knowledge_enhanced=request.knowledge_enhanced
        )

        if not ollama_response or "message" not in ollama_response:
            raise HTTPException(status_code=500, detail="Invalid response structure from AI service.")

        ai_message = ollama_response.get("message", {})
        response_content = ai_message.get("content", "")
        response_role = ai_message.get("role", "assistant")
        model_used = ollama_response.get("model", selected_model)

        # Determine data_source based on the flag from ai_service
        if ollama_response.get("kg_context_used", False):
            data_source_used = "Knowledge Graph"
            # Optionally, add more detail to the content if KG was used.
            # For example: response_content += "\n\n(Information supplemented by the Knowledge Graph)"
            # This is a design choice. For now, just setting the data_source field.

        return AIChatResponse(
            role=response_role,
            content=response_content,
            model_used=model_used,
            data_source=data_source_used
        )

    except OllamaError as e:
        # Log the error e.message or str(e)
        print(f"Ollama service error: {e}") # Replace with actual logging
        detail = f"Error communicating with AI service: {str(e)}"
        if e.status_code:
            if e.status_code == 404: # Model not found
                 detail = f"AI model '{request.model or selected_model}' not found on Ollama server. Ensure it's pulled. Error: {str(e)}"
            elif e.status_code == 503: # Service unavailable
                 detail = f"AI service (Ollama) is unavailable. Ensure it's running. Error: {str(e)}"
        raise HTTPException(status_code=e.status_code or 503, detail=detail)
    except HTTPException:
        # Re-raise HTTPException if it was raised intentionally
        raise
    except Exception as e:
        # Log the error
        print(f"Unexpected error in AI chat endpoint: {e}") # Replace with actual logging
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# Example of how to add this router to your main app:
# from backend.app.api.v1.endpoints import ai as ai_router
# app.include_router(ai_router.router, prefix="/api/v1/ai", tags=["AI Service"])

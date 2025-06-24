from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from ....services.ai_service import get_ai_chat_response, get_ollama_chat_response, AIServiceError
from ....core.config import settings

router = APIRouter()

# --- Pydantic Models ---
class AIChatRequest(BaseModel):
    message: str = Field(..., description="The user's message to the AI.")
    context: Optional[str] = Field(None, description="Optional context to provide to the AI.")
    model: Optional[str] = Field(None, description="Optional AI model to use (e.g., 'deepseek-chat'). Uses system default if not provided.")
    # stream: bool = Field(False, description="Whether to stream the response.") # Streaming not implemented yet

class AIChatResponse(BaseModel):
    role: str = Field(description="The role of the responder (e.g., 'assistant').")
    content: str = Field(description="The AI's response content.")
    model_used: str = Field(description="The AI model that generated the response.")
    # additional_info: Optional[Dict[str, Any]] = Field(None, description="Additional information from the AI response if any.")


@router.post("/chat", response_model=AIChatResponse)
async def handle_ai_chat(
    request: AIChatRequest = Body(...)
):
    """
    Receives a user message and optional context, communicates with the
    AI service (DeepSeek or Ollama), and returns the AI's response.
    """
    try:
        # Try DeepSeek first, fallback to Ollama
        selected_model = request.model or getattr(settings, 'DEEPSEEK_DEFAULT_MODEL', 
                                                 getattr(settings, 'OLLAMA_DEFAULT_MODEL', "deepseek-chat"))

        try:
            # Primary: Use DeepSeek API
            ai_response = await get_ai_chat_response(
                message=request.message,
                context=request.context,
                model=selected_model
            )
        except AIServiceError as deepseek_error:
            # Fallback: Use Ollama if DeepSeek fails
            print(f"DeepSeek service failed, trying Ollama: {deepseek_error}")
            ai_response = await get_ollama_chat_response(
                message=request.message,
                context=request.context,
                model=getattr(settings, 'OLLAMA_DEFAULT_MODEL', "qwen2:0.5b")
            )

        # Extract the relevant part of the response
        # Response structure is unified between DeepSeek and Ollama:
        # {
        #   "model": "deepseek-chat" or "qwen2:0.5b",
        #   "created": "...",
        #   "message": { "role": "assistant", "content": "..." },
        #   "usage": { ... }
        # }

        if not ai_response or "message" not in ai_response:
            raise HTTPException(status_code=500, detail="Invalid response structure from AI service.")

        ai_message = ai_response.get("message", {})
        response_content = ai_message.get("content", "")
        response_role = ai_message.get("role", "assistant")
        model_used = ai_response.get("model", selected_model)

        return AIChatResponse(
            role=response_role,
            content=response_content,
            model_used=model_used
            # additional_info={k: v for k, v in ai_response.items() if k not in ["message", "model"]}
        )

    except AIServiceError as e:
        # Log the error e.message or str(e)
        print(f"AI service error: {e}") # Replace with actual logging
        detail = f"Error communicating with AI service: {str(e)}"
        if e.status_code:
            if e.status_code == 404: # Model not found
                 detail = f"AI model '{request.model or selected_model}' not found. Ensure it's available. Error: {str(e)}"
            elif e.status_code == 503: # Service unavailable
                 detail = f"AI service is unavailable. Check configuration and connectivity. Error: {str(e)}"
            elif e.status_code == 401: # Unauthorized (API key issue)
                 detail = f"AI service authentication failed. Check API key configuration. Error: {str(e)}"
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
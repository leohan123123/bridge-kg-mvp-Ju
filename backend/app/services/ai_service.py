import httpx
import json
from typing import Optional, Dict, Any

from ..core.config import settings

# DeepSeek API configuration
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "deepseek-chat"

class AIServiceError(Exception):
    """Custom exception for AI service errors."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code

async def get_ai_chat_response(
    message: str,
    context: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Sends a message to the DeepSeek API and returns the chat response.

    Args:
        message: The user's message.
        context: Optional context to provide to the LLM.
        model: The model to use (defaults to deepseek-chat).
        api_key: DeepSeek API key from settings.

    Returns:
        A dictionary containing the API response.

    Raises:
        AIServiceError: If the API request fails or returns an error.
    """
    api_key = api_key or getattr(settings, 'DEEPSEEK_API_KEY', None)
    if not api_key:
        raise AIServiceError("DeepSeek API key not configured")
    
    selected_model = model or getattr(settings, 'DEEPSEEK_DEFAULT_MODEL', DEFAULT_MODEL)

    system_prompt = "You are a helpful AI assistant specialized in bridge engineering and knowledge management. Provide clear, accurate, and professional responses."
    if context:
        user_message_content = f"Context: {context}\n\nUser Question: {message}"
    else:
        user_message_content = message

    payload = {
        "model": selected_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message_content}
        ],
        "stream": False,
        "temperature": 0.7,
        "max_tokens": 2048
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(DEEPSEEK_API_URL, json=payload, headers=headers)
            response.raise_for_status()

            response_data = response.json()

            # Ensure the response structure is as expected
            if "choices" not in response_data or not response_data["choices"]:
                raise AIServiceError(f"Unexpected response structure from DeepSeek: {response_data}")

            # Extract the message content from DeepSeek response format
            choice = response_data["choices"][0]
            if "message" not in choice or "content" not in choice["message"]:
                raise AIServiceError(f"Invalid message structure in DeepSeek response: {choice}")

            # Convert to a format compatible with existing frontend
            return {
                "message": {
                    "role": choice["message"]["role"],
                    "content": choice["message"]["content"]
                },
                "model": response_data.get("model", selected_model),
                "created": response_data.get("created"),
                "usage": response_data.get("usage", {})
            }

        except httpx.HTTPStatusError as e:
            error_message = f"DeepSeek API request failed with status {e.response.status_code}: {e.response.text}"
            print(f"Error: {error_message}")
            raise AIServiceError(error_message, status_code=e.response.status_code) from e
        except httpx.RequestError as e:
            error_message = f"Error connecting to DeepSeek API: {e}"
            print(f"Error: {error_message}")
            raise AIServiceError(error_message) from e
        except json.JSONDecodeError as e:
            error_message = f"Failed to decode JSON response from DeepSeek: {e}"
            print(f"Error: {error_message}")
            raise AIServiceError(error_message) from e

# Keep backward compatibility with existing code
async def get_ollama_chat_response(
    message: str,
    context: Optional[str] = None,
    model: Optional[str] = None,
    ollama_api_url: Optional[str] = None
) -> Dict[str, Any]:
    """Backward compatibility wrapper that calls DeepSeek API."""
    return await get_ai_chat_response(message, context, model)

if __name__ == '__main__':
    import asyncio

    async def main():
        print(f"Testing DeepSeek API connection")
        print(f"Using model: {getattr(settings, 'DEEPSEEK_DEFAULT_MODEL', DEFAULT_MODEL)}")

        try:
            # Test without context
            print("\n--- Test 1: Without context ---")
            response_no_context = await get_ai_chat_response(message="Hello, who are you?")
            print("DeepSeek Response (no context):")
            print(f"  Role: {response_no_context.get('message', {}).get('role')}")
            print(f"  Content: {response_no_context.get('message', {}).get('content')}")

            # Test with context
            print("\n--- Test 2: With context ---")
            sample_context = "The bridge is a suspension bridge built in 1967. It has shown signs of corrosion on the main cables."
            response_with_context = await get_ai_chat_response(
                message="What are the main concerns for this structure?",
                context=sample_context
            )
            print("DeepSeek Response (with context):")
            print(f"  Role: {response_with_context.get('message', {}).get('role')}")
            print(f"  Content: {response_with_context.get('message', {}).get('content')}")

        except AIServiceError as e:
            print(f"An error occurred: {e}")
            if e.status_code:
                print(f"Status Code: {e.status_code}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    asyncio.run(main())
import httpx # Changed from requests to httpx for async
import json
from typing import Optional, Dict, Any

from ..core.config import settings # Assuming settings will hold OLLAMA_API_URL

# Default Ollama API URL if not specified in settings
DEFAULT_OLLAMA_API_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "qwen2:0.5b" # Using a smaller model for initial testing

class OllamaError(Exception):
    """Custom exception for Ollama API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code

async def get_ollama_chat_response(
    message: str,
    context: Optional[str] = None,
    model: Optional[str] = None,
    ollama_api_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Sends a message to the Ollama API and returns the chat response.

    Args:
        message: The user's message.
        context: Optional context to provide to the LLM.
        model: The Ollama model to use (e.g., "qwen2.5:7b", "llama3.1:8b").
               Defaults to DEFAULT_MODEL.
        ollama_api_url: The URL of the Ollama API. Defaults to OLLAMA_API_URL from settings
                        or DEFAULT_OLLAMA_API_URL.

    Returns:
        A dictionary containing the Ollama API response.

    Raises:
        OllamaError: If the API request fails or returns an error.
    """
    api_url = ollama_api_url or getattr(settings, 'OLLAMA_API_URL', DEFAULT_OLLAMA_API_URL)
    selected_model = model or getattr(settings, 'OLLAMA_DEFAULT_MODEL', DEFAULT_MODEL)

    system_prompt = "You are a helpful assistant."
    if context:
        # Basic context integration. This can be refined.
        user_message_content = f"Context: {context}\n\nUser Question: {message}"
    else:
        user_message_content = message

    payload = {
        "model": selected_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message_content}
        ],
        "stream": False  # For now, we'll use non-streaming responses
    }

    async with httpx.AsyncClient(timeout=60.0) as client: # Increased timeout
        try:
            response = await client.post(api_url, json=payload)
            response.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx responses

            # The response from Ollama is a stream of JSON objects, even for stream=False.
            # We need to parse them line by line if it's not a single JSON object.
            # However, with stream=False, it should be a single JSON object.
            response_data = response.json()

            # Ensure the response structure is as expected
            if "message" not in response_data or "content" not in response_data["message"]:
                raise OllamaError(f"Unexpected response structure from Ollama: {response_data}")

            return response_data

        except httpx.HTTPStatusError as e:
            error_message = f"Ollama API request failed with status {e.response.status_code}: {e.response.text}"
            print(f"Error: {error_message}") # For logging
            raise OllamaError(error_message, status_code=e.response.status_code) from e
        except httpx.RequestError as e:
            error_message = f"Error connecting to Ollama API at {api_url}: {e}"
            print(f"Error: {error_message}") # For logging
            raise OllamaError(error_message) from e
        except json.JSONDecodeError as e:
            error_message = f"Failed to decode JSON response from Ollama: {e}. Response text: {response.text if 'response' in locals() else 'N/A'}"
            print(f"Error: {error_message}") # For logging
            raise OllamaError(error_message) from e

if __name__ == '__main__':
    import asyncio

    async def main():
        print(f"Testing Ollama connection to: {getattr(settings, 'OLLAMA_API_URL', DEFAULT_OLLAMA_API_URL)}")
        print(f"Using model: {getattr(settings, 'OLLAMA_DEFAULT_MODEL', DEFAULT_MODEL)}")

        # Make sure Ollama server is running and the model is pulled:
        # ollama pull qwen2:0.5b

        try:
            # Test without context
            print("\n--- Test 1: Without context ---")
            response_no_context = await get_ollama_chat_response(message="Hello, who are you?")
            print("Ollama Response (no context):")
            # print(json.dumps(response_no_context, indent=2))
            print(f"  Role: {response_no_context.get('message', {}).get('role')}")
            print(f"  Content: {response_no_context.get('message', {}).get('content')}")


            # Test with context
            print("\n--- Test 2: With context ---")
            sample_context = "The bridge is a suspension bridge built in 1967. It has shown signs of corrosion on the main cables."
            response_with_context = await get_ollama_chat_response(
                message="What are the main concerns for this structure?",
                context=sample_context
            )
            print("Ollama Response (with context):")
            # print(json.dumps(response_with_context, indent=2))
            print(f"  Role: {response_with_context.get('message', {}).get('role')}")
            print(f"  Content: {response_with_context.get('message', {}).get('content')}")

        except OllamaError as e:
            print(f"An error occurred: {e}")
            if e.status_code:
                print(f"Status Code: {e.status_code}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    asyncio.run(main())

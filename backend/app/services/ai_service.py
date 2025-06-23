import httpx # Changed from requests to httpx for async
import json
from typing import Optional, Dict, Any, List
import re # For keyword extraction
import logging # For logging

from backend.app.core.config import settings
from backend.app.db.neo4j_driver import get_db_session # Corrected import path
from neo4j import Session as Neo4jSession # For type hinting with synchronous session
from neo4j.exceptions import Neo4jError
import asyncio # For asyncio.to_thread


# Default Ollama API URL if not specified in settings
DEFAULT_OLLAMA_API_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "qwen2:0.5b" # Using a smaller model for initial testing

logger = logging.getLogger(__name__)

# Simple keyword patterns - this can be expanded significantly
KEYWORD_PATTERNS = {
    "bridge": re.compile(r"(?:bridge|span)\s+([\w\s-]+?)(?:\s+details|\s+information|\s+specs|is|was|\?|$)", re.IGNORECASE),
    "material": re.compile(r"(?:material|properties of)\s+([\w\s-]+?)(?:\s+details|\s+information|\s+specs|is|was|\?|$)", re.IGNORECASE),
    "component": re.compile(r"(?:component|part)\s+([\w\s-]+?)(?:\s+details|\s+information|\s+specs|is|was|\?|$)", re.IGNORECASE),
}

# Changed to synchronous function
def query_knowledge_graph(user_message: str) -> Optional[str]:
    """
    Queries the Neo4j knowledge graph based on keywords in the user message. (Synchronous)
    """
    extracted_entity_name = None
    entity_type = None # "Bridge", "Material", "Component"

    # Basic keyword extraction
    for type_name, pattern in KEYWORD_PATTERNS.items():
        match = pattern.search(user_message)
        if match:
            extracted_entity_name = match.group(1).strip()
            entity_type = type_name.capitalize() # Bridge, Material, Component
            logger.info(f"Extracted entity: '{extracted_entity_name}' of type '{entity_type}' from message: '{user_message}'")
            break

    if not extracted_entity_name or not entity_type:
        logger.info(f"No specific entities extracted from message: '{user_message}'")
        return None

    query = None
    params = {"name": extracted_entity_name}

    if entity_type == "Bridge":
        query = """
        MATCH (e:Bridge)
        WHERE toLower(e.name) CONTAINS toLower($name)
        RETURN properties(e) as data, labels(e)[0] as type
        LIMIT 5
        """
    elif entity_type == "Material":
        query = """
        MATCH (e:Material)
        WHERE toLower(e.name) CONTAINS toLower($name)
        RETURN properties(e) as data, labels(e)[0] as type
        LIMIT 5
        """
    elif entity_type == "Component":
        # This query might need adjustment based on how components are linked or named
        query = """
        MATCH (e:Component)
        WHERE toLower(e.name) CONTAINS toLower($name)
        RETURN properties(e) as data, labels(e)[0] as type
        LIMIT 5
        """

    if not query:
        return None

    formatted_context_parts = []
    db_session_generator = get_db_session()
    session: Optional[Neo4jSession] = None
    try:
        session = next(db_session_generator) # Get the synchronous session
        results = session.run(query, params) # Execute query synchronously
        records = results.data()  # Get data synchronously (list of dicts)

        if records:
            formatted_context_parts.append(f"Found information for {entity_type} '{extracted_entity_name}':")
            for record in records:
                data = record.get("data", {})
                record_type = record.get("type", entity_type)
                context_line = f"- Type: {record_type}, Data: {json.dumps(data)}"
                formatted_context_parts.append(context_line)
            logger.info(f"Found {len(records)} records for '{extracted_entity_name}' of type '{entity_type}'.")
            return "\n".join(formatted_context_parts)
        else:
            logger.info(f"No records found for '{extracted_entity_name}' of type '{entity_type}'.")
            return None

    except Neo4jError as e:
        logger.error(f"Neo4j query failed for '{extracted_entity_name}': {e}")
        # It's important to still ensure the session generator is cleaned up
    except StopIteration:
        logger.error("Failed to get Neo4j session from generator.")
    except Exception as e:
        logger.error(f"Unexpected error during knowledge graph query for '{extracted_entity_name}': {e}")
    finally:
        if session: # Check if session was successfully obtained
            try:
                # Ensure the generator is fully consumed to trigger the finally block in get_db_session
                # which closes the session.
                next(db_session_generator, None)
            except StopIteration:
                pass # Expected
            except Exception as e:
                logger.error(f"Error while ensuring Neo4j session closure in query_knowledge_graph: {e}")

    return None # Fallback if any error occurs or no records found and not returned earlier.

class OllamaError(Exception):
    """Custom exception for Ollama API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code

async def get_ollama_chat_response(
    message: str,
    context: Optional[str] = None,
    model: Optional[str] = None,
    ollama_api_url: Optional[str] = None,
    knowledge_enhanced: bool = False # New parameter
) -> Dict[str, Any]:
    """
    Sends a message to the Ollama API and returns the chat response.
    Optionally enhances the message with context from a knowledge graph.

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
    kg_context_used_flag = False
    final_context_for_llm = context # Start with user-provided context

    system_prompt = "You are a helpful assistant. If provided with context from a knowledge graph, prioritize using that information to answer the user's question."

    if knowledge_enhanced:
        logger.info(f"Knowledge enhancement requested for message: '{message}'")
        # Call synchronous query_knowledge_graph in a separate thread
        kg_context = await asyncio.to_thread(query_knowledge_graph, message)

        if kg_context:
            logger.info(f"Knowledge graph context found:\n{kg_context}")
            kg_context_used_flag = True
            if final_context_for_llm: # If user already provided some context
                final_context_for_llm = f"User Context: {final_context_for_llm}\n\nKnowledge Graph Context: {kg_context}"
            else:
                final_context_for_llm = f"Knowledge Graph Context: {kg_context}"
        else:
            logger.info("No relevant knowledge graph context found.")

    if final_context_for_llm:
        user_message_content = f"Context: {final_context_for_llm}\n\nUser Question: {message}"
    else:
        user_message_content = message

    logger.debug(f"Final user message content for LLM:\n{user_message_content}")

    payload = {
        "model": selected_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message_content}
        ],
        "stream": False
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(api_url, json=payload)
            response.raise_for_status()
            response_data = response.json()

            if "message" not in response_data or "content" not in response_data["message"]:
                raise OllamaError(f"Unexpected response structure from Ollama: {response_data}")

            # Add custom fields to the response for internal use / API response enrichment
            response_data["kg_context_used"] = kg_context_used_flag
            if kg_context_used_flag : # Store the context that was actually sent to the LLM
                response_data["final_context_for_llm"] = final_context_for_llm
            else:
                response_data["final_context_for_llm"] = context # Original context if no KG

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
    # Ensure Neo4j is running and populated with some data, e.g.:
    # CREATE (:Bridge {name: "Brooklyn Bridge", type: "Suspension", year: 1883, length_meters: 1825})
    # CREATE (:Bridge {name: "Golden Gate Bridge", type: "Suspension", year: 1937, length_meters: 2737})
    # CREATE (:Material {name: "Steel", strength: "High"})
    # CREATE (:Component {name: "Main Cable", material: "Steel"})

        try:
        # Test 0: Test Neo4j connection and query_knowledge_graph directly (now synchronous)
        # To test query_knowledge_graph directly in an async main, we'd also wrap its call in to_thread
        # or call it from a synchronous helper if we wanted to print its direct output easily.
        # For simplicity in this main test, we'll rely on its invocation via get_ollama_chat_response.
        print("\n--- Test 0: Knowledge Graph Query (via get_ollama_chat_response) ---")
        # This test will internally call query_knowledge_graph using asyncio.to_thread
        kg_test_response = await get_ollama_chat_response(
            message="Tell me about the Brooklyn Bridge",
            knowledge_enhanced=True,
            model="dummy-model-for-kg-test" # Use a dummy to isolate KG part if LLM is slow/unavailable
        )
        if kg_test_response.get("kg_context_used"):
            print("KG Context for 'Brooklyn Bridge' (as seen by LLM):")
            print(kg_test_response.get("final_context_for_llm"))
        elif "Ollama API request failed" in kg_test_response.get('message', {}).get('content', ''):
             print(f"KG test failed due to Ollama error, but check logs for KG query success: {kg_test_response.get('message', {}).get('content','')}")
        else:
            print("No KG context found or used for 'Brooklyn Bridge'. Ensure DB is populated and keyword extraction works.")
            print(f"LLM Response: {kg_test_response.get('message', {}).get('content')}")


        # Test 1: Without context, knowledge_enhanced=False (default)
        print("\n--- Test 1: Without context (knowledge_enhanced=False) ---")
            response_no_context = await get_ollama_chat_response(message="Hello, who are you?")
            print("Ollama Response (no context):")
            print(f"  Content: {response_no_context.get('message', {}).get('content')}")
        print(f"  KG Used: {response_no_context.get('kg_context_used', False)}")


        # Test 2: With provided context, knowledge_enhanced=False
        print("\n--- Test 2: With provided context (knowledge_enhanced=False) ---")
            sample_context = "The bridge is a suspension bridge built in 1967. It has shown signs of corrosion on the main cables."
            response_with_context = await get_ollama_chat_response(
                message="What are the main concerns for this structure?",
                context=sample_context
            )
            print("Ollama Response (with context):")
            print(f"  Content: {response_with_context.get('message', {}).get('content')}")
        print(f"  KG Used: {response_with_context.get('kg_context_used', False)}")

        # Test 3: knowledge_enhanced=True, query that should find KG data
        print("\n--- Test 3: With knowledge_enhanced=True (query for 'Brooklyn Bridge') ---")
        response_kg_enhanced = await get_ollama_chat_response(
            message="Tell me about the Brooklyn Bridge, its type and construction year.",
            knowledge_enhanced=True
        )
        print("Ollama Response (KG enhanced for 'Brooklyn Bridge'):")
        print(f"  Content: {response_kg_enhanced.get('message', {}).get('content')}")
        print(f"  KG Used: {response_kg_enhanced.get('kg_context_used', False)}")
        if response_kg_enhanced.get('kg_context_used', False):
             print(f"  KG Context provided to LLM: {response_kg_enhanced.get('final_context_for_llm', '')[:200]}...") # Print snippet


        # Test 4: knowledge_enhanced=True, query that should find material data
        print("\n--- Test 4: With knowledge_enhanced=True (query for 'Steel material') ---")
        response_kg_material = await get_ollama_chat_response(
            message="What do you know about Steel material properties?",
            knowledge_enhanced=True
        )
        print("Ollama Response (KG enhanced for 'Steel material'):")
        print(f"  Content: {response_kg_material.get('message', {}).get('content')}")
        print(f"  KG Used: {response_kg_material.get('kg_context_used', False)}")


        # Test 5: knowledge_enhanced=True, but no relevant KG data expected
        print("\n--- Test 5: With knowledge_enhanced=True (query for 'the moon') ---")
        response_kg_no_match = await get_ollama_chat_response(
            message="Tell me about the moon.",
            knowledge_enhanced=True
        )
        print("Ollama Response (KG enhanced for 'the moon' - no match expected):")
        print(f"  Content: {response_kg_no_match.get('message', {}).get('content')}")
        print(f"  KG Used: {response_kg_no_match.get('kg_context_used', False)}")


        # Test 6: knowledge_enhanced=True, with additional user context
        print("\n--- Test 6: With knowledge_enhanced=True AND user context ---")
        user_provided_context = "This bridge is located in a high-seismic zone."
        response_kg_user_context = await get_ollama_chat_response(
            message="Considering its age, what are the risks for the Brooklyn Bridge?",
            context=user_provided_context,
            knowledge_enhanced=True
        )
        print("Ollama Response (KG enhanced for 'Brooklyn Bridge' + user context):")
        print(f"  Content: {response_kg_user_context.get('message', {}).get('content')}")
        print(f"  KG Used: {response_kg_user_context.get('kg_context_used', False)}")
        if response_kg_user_context.get('kg_context_used', False):
             print(f"  KG Context provided to LLM (should include user and KG): {response_kg_user_context.get('final_context_for_llm', '')[:300]}...")


        except OllamaError as e:
        print(f"An Ollama error occurred: {e}")
            if e.status_code:
                print(f"Status Code: {e.status_code}")
    except Neo4jError as e:
        print(f"A Neo4j error occurred: {e}")
    except ConnectionError as e: # From get_neo4j_driver if it fails
        print(f"A DB connection error occurred: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    asyncio.run(main())

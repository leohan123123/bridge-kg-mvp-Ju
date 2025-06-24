from typing import Dict, List
# Import necessary functions from neo4j_rag_service
# We'll use the existing stubbed functions for now
from backend.app.services.neo4j_rag_service import search_by_keywords
from backend.app.services.ai_service import get_ai_chat_response
from backend.app.core.config import settings

class SimpleRAGService:
    def __init__(self):
        # In a real scenario, you might initialize connections to Neo4j
        # or load other necessary resources here.
        # For this simplified version, we rely on functions that manage their own state
        # or use global/stubbed connections as defined in neo4j_rag_service.
        pass

    async def get_bridge_context(self, question: str) -> str:
        """
        Retrieves context from the knowledge graph based on keywords in the question.
        """
        # Simple keyword extraction: split by space and use unique words.
        # In a real system, this would involve more sophisticated NLP (e.g., NER, keyword extraction libraries).
        keywords = list(set(question.lower().split()))

        # Filter out very common English stop words - basic list
        common_stopwords = {"the", "a", "is", "of", "and", "to", "in", "it", "what", "who", "where", "when", "how", "for", "on", "with", "an"}
        filtered_keywords = [kw for kw in keywords if kw not in common_stopwords and len(kw) > 2]

        if not filtered_keywords:
            return "No specific keywords identified in the question to search the knowledge graph."

        # Use the stubbed search_by_keywords function
        # We are not specifying entity_types for a broader search initially.
        try:
            print(f"Searching graph with keywords: {filtered_keywords}")
            retrieved_entities = search_by_keywords(keywords=filtered_keywords)
        except Exception as e:
            print(f"Error during graph search: {e}")
            return "Error occurred while searching the knowledge graph."

        if not retrieved_entities:
            return "No relevant information found in the knowledge graph for the keywords."

        # Build a simple context string from the retrieved entities
        context_parts = []
        for entity in retrieved_entities:
            entity_name = entity.get("properties", {}).get("name", entity.get("id", "Unknown Entity"))
            entity_type = entity.get("type", "Unknown Type")
            context_parts.append(f"{entity_name} (Type: {entity_type})")

        if not context_parts:
             return "No detailed information found for the keywords in the knowledge graph."

        context_str = "Found entities related to your question: " + ", ".join(context_parts) + "."
        return context_str

    async def answer_question(self, question: str) -> Dict:
        """
        Answers a question using RAG approach:
        1. Retrieve context from the knowledge graph.
        2. Call an AI model with the question and context.
        """
        print(f"Received question for RAG: {question}")

        # 1. Get context from Neo4j
        context_str = await self.get_bridge_context(question)
        print(f"Retrieved context: {context_str}")

        # 2. Call DeepSeek API (via ai_service) with question and context
        try:
            # The get_ai_chat_response function is already async
            ai_response = await get_ai_chat_response(
                message=question,
                context=context_str,
                # Model and API key are handled by ai_service using settings
            )
            # The response from get_ai_chat_response is expected to be a dictionary
            # e.g., {"message": {"role": "assistant", "content": "The answer..."}, ...}
            # We can return this directly or reformat if needed. For now, return as is.
            print(f"AI response: {ai_response}")
            return ai_response

        except Exception as e:
            # Log the error and return a user-friendly error message
            # In a real app, you might have more sophisticated error handling
            print(f"Error calling AI service: {e}")
            return {
                "message": {
                    "role": "assistant",
                    "content": f"Sorry, I encountered an error trying to answer your question: {str(e)}"
                },
                "error": True
            }

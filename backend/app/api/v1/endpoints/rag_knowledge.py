from fastapi import APIRouter, HTTPException, Body, Path, Query, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

# Import the new KnowledgeGraphEngine
from backend.app.services.knowledge_graph_engine import KnowledgeGraphEngine
# Assuming settings might be needed for Neo4jRealService if not handled by engine's init
# from backend.app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Initialize KnowledgeGraphEngine ---
# For simplicity, a global instance. For more complex scenarios, consider FastAPI's Depends.
# This instance will live for the duration of the application.
# Ensure Neo4jRealService within KnowledgeGraphEngine handles connections robustly (e.g., driver is long-lived).
try:
    knowledge_engine = KnowledgeGraphEngine()
except Exception as e:
    logger.error(f"Fatal error: Could not initialize KnowledgeGraphEngine: {e}")
    # If the engine can't start, the API is likely non-functional.
    # This could be handled by having endpoints return a 503 Service Unavailable if engine is None.
    knowledge_engine = None # Or raise to prevent app startup

# --- Request Models ---
class BuildGraphRequest(BaseModel):
    text_content: str
    document_name: str

# QueryPathRequest can be removed if the endpoint is removed or significantly changed
# class QueryPathRequest(BaseModel):
#     start_entity_id: str
#     end_entity_id: str
#     max_path_length: Optional[int] = 5

# --- Response Models ---
class GraphStatsResponse(BaseModel):
    total_nodes: int
    total_relationships: int
    node_type_distribution: Dict[str, int]
    relationship_type_distribution: Dict[str, int]
    graph_density: float
    connected_components_count: Optional[str] # As it's a string in the service for now

class BuildGraphResponse(BaseModel):
    status: str
    document_name: str
    entities_found_by_category: Optional[Dict[str, int]] = None
    unique_entities_processed: Optional[int] = None
    relationships_extracted: Optional[int] = None
    relationships_created_in_db: Optional[int] = None
    error: Optional[str] = None


# --- API Endpoints ---

@router.post("/build_graph", response_model=BuildGraphResponse)
async def build_graph_from_text_api(request_data: BuildGraphRequest = Body(...)):
    """
    Builds a knowledge graph from the provided text content and document name.
    """
    if not knowledge_engine:
        raise HTTPException(status_code=503, detail="Knowledge Graph Engine not available.")
    try:
        # Call the KnowledgeGraphEngine method
        result = knowledge_engine.build_graph_from_document(
            text=request_data.text_content,
            document_name=request_data.document_name
        )
        if result.get("status") == "Error during graph construction":
             raise HTTPException(status_code=500, detail=result.get("error", "Unknown error building graph"))
        return BuildGraphResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error building graph for document {request_data.document_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error building graph: {str(e)}")


@router.get("/search", response_model=List[Dict[str, Any]])
async def search_knowledge_graph_api(
    query: str = Query(..., description="Search query string"),
    # entity_types: Optional[str] = Query(None, description="Comma-separated entity types (currently not fully supported by engine's query)")
):
    """
    Searches the knowledge graph based on a query string.
    (Note: entity_types filter from original API is not directly supported by current engine.query_graph_knowledge)
    """
    if not knowledge_engine:
        raise HTTPException(status_code=503, detail="Knowledge Graph Engine not available.")
    try:
        # The engine's query_graph_knowledge takes a single query string.
        # Keyword splitting and type filtering would need to be added to the engine or handled here if desired.
        results = knowledge_engine.query_graph_knowledge(query=query)
        # Check if results indicate an error from the engine
        if results and isinstance(results, list) and len(results) > 0 and "error" in results[0]:
            raise HTTPException(status_code=500, detail=results[0]["error"])
        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error during graph search for query '{query}': {e}")
        raise HTTPException(status_code=500, detail=f"Error during graph search: {str(e)}")


@router.get("/entity/{entity_id}/neighborhood", response_model=Dict[str, Any])
async def get_entity_neighborhood_api(
    entity_id: str = Path(..., description="The Neo4j element ID of the entity"),
    max_depth: int = Query(2, description="The maximum depth of the neighborhood (number of hops)", ge=1, le=5)
):
    """
    Retrieves the neighborhood (nodes and relationships) around a specific entity using its Neo4j element ID.
    """
    if not knowledge_engine:
        raise HTTPException(status_code=503, detail="Knowledge Graph Engine not available.")
    try:
        # Directly use the neo4j_service from the engine instance
        neighborhood = knowledge_engine.neo4j_service.get_entity_neighbors(entity_id=entity_id, max_depth=max_depth)

        # get_entity_neighbors returns {"nodes": [], "relationships": []}
        # Check if the primary node itself was found (e.g. if nodes list is empty after a valid ID query)
        # This check might be too strict if a node exists but has no neighbors within max_depth.
        # A better check might be to see if the start_node is part of the 'nodes' list.
        if not neighborhood or not neighborhood.get("nodes"):
             # Check if the entity itself exists, even if it has no neighbors
             # This would require a separate call like `engine.neo4j_service.get_entity_by_id(entity_id)`
             # For now, if nodes list is empty, assume it's effectively not found or isolated.
             pass # Allow empty results if a node is isolated.

        return neighborhood
    except Exception as e:
        # Catch specific Neo4j client errors if possible, e.g., if ID format is wrong or connection fails
        logger.exception(f"Error retrieving entity neighborhood for ID '{entity_id}': {e}")
        # Check if the error message suggests "not found" vs. other errors
        if "not found" in str(e).lower(): # Very basic check
            raise HTTPException(status_code=404, detail=f"Entity with ID '{entity_id}' not found or error fetching.")
        raise HTTPException(status_code=500, detail=f"Error retrieving entity neighborhood: {str(e)}")


# @router.post("/query_path", response_model=List[List[Dict[str, Any]]])
# async def query_reasoning_path_api(request_data: QueryPathRequest = Body(...)):
#     """
#     Finds and returns reasoning paths between two entities. (Currently Not Implemented)
#     """
#     raise HTTPException(status_code=501, detail="Querying reasoning paths is not implemented yet.")

@router.get("/graph_stats", response_model=GraphStatsResponse)
async def get_graph_statistics_api():
    """
    Provides statistics about the current knowledge graph.
    """
    if not knowledge_engine:
        raise HTTPException(status_code=503, detail="Knowledge Graph Engine not available.")
    try:
        stats = knowledge_engine.neo4j_service.get_graph_statistics()
        # The GraphStatsResponse model should match the keys returned by get_graph_statistics()
        # Original keys: total_nodes, total_relationships, node_type_distribution, relationship_type_distribution, graph_density, connected_components_count
        if stats.get("total_nodes", -1) == -1 : # Indicates an error from the service
            raise HTTPException(status_code=500, detail="Failed to retrieve graph statistics from the service.")
        return GraphStatsResponse(**stats)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error retrieving graph statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving graph statistics: {str(e)}")

# Ensure the main application (e.g., main.py) correctly includes this router
# and handles the lifecycle of the knowledge_engine if needed (e.g., closing connections on shutdown).
# FastAPI events (startup/shutdown) can be used for this.

# Example for main.py:
# from fastapi import FastAPI
# from backend.app.api.v1.endpoints import rag_knowledge
# from contextlib import asynccontextmanager

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Startup: Initialize resources, like the knowledge_engine if not global
#     # For the global `knowledge_engine`, ensure its `close_services` is called on shutdown.
#     yield
#     # Shutdown: Cleanup resources
#     if rag_knowledge.knowledge_engine:
#         rag_knowledge.knowledge_engine.close_services()
#         print("Knowledge engine services closed.")

# app = FastAPI(title="Bridge KG MVP API", lifespan=lifespan)
# app.include_router(rag_knowledge.router, prefix="/api/v1/rag", tags=["RAG Knowledge Graph"])
#
# if __name__ == "__main__":
#     import uvicorn
#     # Ensure logging is configured for Uvicorn if running this way
#     logging.basicConfig(level=logging.INFO)
#     uvicorn.run(app, host="0.0.0.0", port=8000)

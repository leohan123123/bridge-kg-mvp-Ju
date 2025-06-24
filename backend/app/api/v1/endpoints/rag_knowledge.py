from fastapi import APIRouter, HTTPException, Body, Path, Query
from pydantic import BaseModel # Ensure BaseModel is imported
from typing import List, Dict, Any, Optional

# Import service functions (assuming they are in the services directory)
# Adjust path if your structure is different, e.g., app.services
from backend.app.services import knowledge_graph_builder as kgb_service
from backend.app.services import neo4j_rag_service as neo4j_service
# from backend.app.services import knowledge_standardizer as ks_service # Will be used later

router = APIRouter()

# --- Request Models (Pydantic models for request bodies) ---
class BuildGraphRequest(BaseModel):
    text_content: str # Or perhaps a list of texts, or a document ID
    entities: Optional[Dict[str, Any]] = None # Entities already identified, if any

class QueryPathRequest(BaseModel):
    start_entity_id: str
    end_entity_id: str
    max_path_length: Optional[int] = 5

# --- Response Models (Pydantic models for responses) ---
# For simplicity, many responses will be Dicts or Lists, but Pydantic models are good practice.
class GraphStatsResponse(BaseModel):
    node_count: int
    edge_count: int
    graph_density: float
    # Potentially other stats like entity type distribution, etc.

class BuildGraphResponse(BaseModel):
    message: str
    graph_summary: Optional[Dict[str, Any]] = None # e.g., nodes and edges count from create_graph_from_triples

# --- API Endpoints ---

@router.post("/build_graph", response_model=BuildGraphResponse)
async def build_graph_from_text(request_data: BuildGraphRequest = Body(...)):
    """
    Builds a knowledge graph from the provided text content and optional pre-identified entities.
    """
    try:
        current_entities = request_data.entities
        if not current_entities and "bridge" in request_data.text_content.lower(): # Very basic placeholder
             current_entities = {"e_stub_1": {"id": "e_stub_1", "name": "A Bridge From Text", "type": "Bridge"}}

        relations = kgb_service.extract_bridge_relations(text=request_data.text_content, entities=current_entities or {})

        triples = kgb_service.build_knowledge_triples(relations=relations)

        # In a full implementation, this would involve multiple calls to neo4j_service
        # to create nodes and relationships based on the triples.
        # For example:
        # for triple in triples:
        #   # Assuming triple structure like {'head': 'id1', 'relation': 'RELATES_TO', 'tail': 'id2', 'head_type': 'TypeA', ...}
        #   # You'd need to ensure entities are created before linking, or use MERGE.
        #   # This part requires careful design based on how IDs and entity properties are managed.
        #   # head_node_id = neo4j_service.create_indexed_entity(triple['head_type'], triple['head_properties'])
        #   # tail_node_id = neo4j_service.create_indexed_entity(triple['tail_type'], triple['tail_properties'])
        #   # neo4j_service.create_weighted_relationship(head_node_id, tail_node_id, triple['relation'], triple.get('properties', {}))
        # For now, using the stubbed create_graph_from_triples from kgb_service:
        graph_creation_result = kgb_service.create_graph_from_triples(triples=triples)

        return BuildGraphResponse(
            message="Knowledge graph build process initiated (stubbed).",
            graph_summary=graph_creation_result.get("graph_summary")
        )
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=500, detail=f"Error building graph: {str(e)}")


@router.get("/search", response_model=List[Dict[str, Any]])
async def search_knowledge_graph(
    keywords: str = Query(..., description="Comma-separated keywords for search"),
    entity_types: Optional[str] = Query(None, description="Comma-separated entity types to filter by (e.g., Bridge,Material)")
):
    """
    Searches the knowledge graph by keywords, with optional filtering by entity types.
    """
    keyword_list = [kw.strip() for kw in keywords.split(",")]
    type_list = [et.strip() for et in entity_types.split(",")] if entity_types else None

    try:
        results = neo4j_service.search_by_keywords(keywords=keyword_list, entity_types=type_list)
        return results # Returns empty list if no results, which is fine for search.
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=500, detail=f"Error during graph search: {str(e)}")


@router.get("/entity/{entity_id}/neighborhood", response_model=Dict[str, Any])
async def get_entity_neighborhood_api(
    entity_id: str = Path(..., description="The ID of the entity to get the neighborhood for"),
    radius: int = Query(1, description="The radius of the neighborhood (number of hops)", ge=0, le=5) # Added le=5 for safety
):
    """
    Retrieves the neighborhood (nodes and relationships) around a specific entity.
    """
    try:
        neighborhood = neo4j_service.get_entity_neighborhood(entity_id=entity_id, radius=radius)
        if not neighborhood or not neighborhood.get("center_node"):
             raise HTTPException(status_code=404, detail=f"Entity with ID '{entity_id}' not found or has no neighborhood.")
        return neighborhood
    except HTTPException: # Re-raise if it's already an HTTPException (e.g. 404)
        raise
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=500, detail=f"Error retrieving entity neighborhood: {str(e)}")


@router.post("/query_path", response_model=List[List[Dict[str, Any]]])
async def query_reasoning_path(request_data: QueryPathRequest = Body(...)):
    """
    Finds and returns reasoning paths between two entities in the knowledge graph.
    """
    try:
        paths = neo4j_service.get_reasoning_path(
            start_node_id=request_data.start_entity_id,
            end_node_id=request_data.end_entity_id,
            max_path_length=request_data.max_path_length
        )
        return paths # Returns empty list if no paths found.
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=500, detail=f"Error querying reasoning path: {str(e)}")

@router.get("/graph_stats", response_model=GraphStatsResponse)
async def get_graph_statistics():
    """
    Provides statistics about the current knowledge graph (e.g., node count, edge count).
    """
    try:
        # These would typically come from Neo4j queries
        # e.g., result = neo4j_service.run_query("MATCH (n) RETURN count(n) AS node_count")
        # node_count = result[0]["node_count"]
        # result = neo4j_service.run_query("MATCH ()-[r]->() RETURN count(r) AS edge_count")
        # edge_count = result[0]["edge_count"]

        stub_node_count = 150 # Placeholder
        stub_edge_count = 300 # Placeholder

        density = 0.0
        if stub_node_count > 1:
            # For directed graph: E / (V * (V - 1))
            density = stub_edge_count / (stub_node_count * (stub_node_count - 1))
            density = round(density, 4)

        return GraphStatsResponse(
            node_count=stub_node_count,
            edge_count=stub_edge_count,
            graph_density=density
        )
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=500, detail=f"Error retrieving graph statistics: {str(e)}")

# Example of how to integrate this router into a FastAPI app (e.g., in main.py):
#
# from fastapi import FastAPI
# from backend.app.api.v1.endpoints import rag_knowledge
#
# app = FastAPI(title="Bridge KG MVP API")
#
# app.include_router(rag_knowledge.router, prefix="/api/v1/rag", tags=["RAG Knowledge Graph"])
#
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)

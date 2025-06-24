from fastapi import APIRouter, HTTPException, Body, Path, Query
from typing import Dict, List, Any

# Assuming services are structured to be importable like this.
# Adjust paths if your project structure is different.
from app.services.ontology_manager import OntologyManager
from app.services.ontology_version_manager import OntologyVersionManager
from app.services.ontology_auto_updater import OntologyAutoUpdater, BridgeEntityExtractor # BridgeEntityExtractor might be needed for request body models

# Pydantic models for request/response bodies (optional but good practice)
from pydantic import BaseModel, Field

router = APIRouter()

# Initialize services
# In a larger app, these would typically be managed by a dependency injection system.
ontology_manager = OntologyManager()
ontology_version_manager = OntologyVersionManager()
ontology_auto_updater = OntologyAutoUpdater()

# --- Request Body Models ---
class EntityTypeCreate(BaseModel):
    entity_type: str = Field(..., example="检测设备")
    properties: List[str] = Field(..., example=["设备ID", "型号"])
    description: str = Field("", example="Stores information about testing equipment.")

class EntityTypeUpdate(BaseModel):
    new_properties: List[str] = Field(..., example=["设计年限", "总长度"])

class RelationshipTypeCreate(BaseModel):
    rel_type: str = Field(..., example="检测")
    from_types: List[str] = Field(..., example=["检测设备"])
    to_types: List[str] = Field(..., example=["桥梁构件"])
    description: str = Field("", example="Relationship indicating a device tested a component.")

class OntologySnapshotCreate(BaseModel):
    version_name: str = Field(..., example="v1.2.0")
    description: str = Field("", example="Added new sensor types and properties.")

class ExtractedDataInput(BaseModel):
    # This model should match the output of BridgeEntityExtractor
    # or the expected input for suggest_ontology_updates
    entities: List[Dict[str, Any]] = Field(..., example=[
        {"text": "Corrosion Monitor X1", "type_suggestion": "Sensor", "properties": {"model": "CM-X1", "status": "active"}}
    ])
    relationships: List[Dict[str, Any]] = Field(default=[], example=[
        {"from_text": "Corrosion Monitor X1", "to_text": "Bridge B-12", "type_suggestion": "MONITORS"}
    ])


# --- API Endpoints ---

@router.get("/ontology/structure", summary="Get current ontology structure")
async def get_ontology_structure():
    """
    Retrieves the complete current structure of the ontology,
    including entity types, their properties, and relationship types.
    """
    try:
        structure = ontology_manager.get_ontology_structure()
        return structure
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ontology/entity_type", status_code=201, summary="Add a new entity type")
async def add_entity_type_endpoint(payload: EntityTypeCreate):
    """
    Adds a new entity type to the ontology.
    - **entity_type**: Name of the new entity type.
    - **properties**: List of property names for this entity type.
    - **description**: Optional description for the entity type.
    """
    success = ontology_manager.add_entity_type(
        entity_type=payload.entity_type,
        properties=payload.properties,
        description=payload.description
    )
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to add entity type '{payload.entity_type}'. It might already exist or an error occurred.")
    return {"message": f"Entity type '{payload.entity_type}' added successfully."}

@router.put("/ontology/entity_type/{type_name}", summary="Update properties of an entity type")
async def update_entity_type_properties_endpoint(
    type_name: str = Path(..., example="桥梁", description="The name of the entity type to update."),
    payload: EntityTypeUpdate = Body(...)
):
    """
    Updates the properties of an existing entity type.
    Currently, this typically means adding new properties.
    - **type_name**: The name of the entity type to update.
    - **new_properties**: A list of new property names to add to this entity type.
    """
    # Check if entity type exists (optional, depends on manager's behavior)
    # current_ontology = ontology_manager.get_ontology_structure()
    # if type_name not in current_ontology.get("entity_types", {}):
    #     raise HTTPException(status_code=404, detail=f"Entity type '{type_name}' not found.")

    success = ontology_manager.update_entity_properties(
        entity_type=type_name,
        new_properties=payload.new_properties
    )
    if not success:
        # The reason for failure might be more complex, e.g. property already exists and manager disallows, or DB error
        raise HTTPException(status_code=400, detail=f"Failed to update properties for entity type '{type_name}'.")
    return {"message": f"Properties for entity type '{type_name}' updated successfully."}

@router.post("/ontology/relationship_type", status_code=201, summary="Add a new relationship type")
async def add_relationship_type_endpoint(payload: RelationshipTypeCreate):
    """
    Adds a new relationship type to the ontology.
    - **rel_type**: Name of the new relationship type.
    - **from_types**: List of source entity types for this relationship.
    - **to_types**: List of target entity types for this relationship.
    - **description**: Optional description.
    """
    success = ontology_manager.add_relationship_type(
        rel_type=payload.rel_type,
        from_types=payload.from_types,
        to_types=payload.to_types,
        description=payload.description
    )
    if not success: # In current manager, this always returns True.
        raise HTTPException(status_code=400, detail=f"Failed to add relationship type '{payload.rel_type}'.")
    return {"message": f"Relationship type '{payload.rel_type}' added successfully."}

@router.get("/ontology/versions", summary="List all ontology versions")
async def list_ontology_versions_endpoint():
    """
    Retrieves a list of all saved ontology version snapshots,
    including metadata like version name, timestamp, and description.
    """
    try:
        versions = ontology_version_manager.list_ontology_versions()
        return versions
    except Exception as e:
        # This is a general catch-all; specific exceptions from the service could be handled too.
        raise HTTPException(status_code=500, detail=f"Error listing ontology versions: {str(e)}")

@router.post("/ontology/snapshot", status_code=201, summary="Create an ontology version snapshot")
async def create_ontology_snapshot_endpoint(payload: OntologySnapshotCreate):
    """
    Creates a snapshot of the current ontology structure, saving it as a new version.
    - **version_name**: A unique name for this version (e.g., "v1.1", "baseline-202312").
    - **description**: Optional description of the changes or state in this version.
    """
    result = ontology_version_manager.create_ontology_snapshot(
        version_name=payload.version_name,
        description=payload.description
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to create snapshot."))
    return result


@router.post("/ontology/suggest_updates", summary="Get ontology update suggestions from extracted data")
async def suggest_ontology_updates_endpoint(extracted_data: ExtractedDataInput):
    """
    Processes extracted entity and relationship data (e.g., from a document analysis tool)
    and suggests potential updates to the ontology. This can identify new entity types,
    new properties for existing types, or new relationship types.

    The input body should match the structure produced by an entity extraction process.
    """
    try:
        # The input 'extracted_data' is a Pydantic model, convert to dict for the service method
        suggestions = ontology_auto_updater.suggest_ontology_updates(extracted_data.model_dump())
        if not suggestions: # Or check if all lists in suggestions are empty
             return {"message": "No new ontology update suggestions based on the provided data.", "suggestions": suggestions}
        return suggestions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error suggesting ontology updates: {str(e)}")

# Placeholder for other planned endpoints (e.g., rollback, compare versions, auto-expand)
# These would require more complex logic and careful consideration of impacts.

# GET /api/v1/ontology/entity_type/{type_name}/instances - (Not explicitly in list but useful)
@router.get("/ontology/entity_type/{type_name}/instances", summary="Get instances of an entity type")
async def get_entity_instances_endpoint(
    type_name: str = Path(..., description="The entity type to fetch instances for."),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of instances to return.")
):
    """
    Retrieves instances of a specified entity type from the knowledge graph.
    """
    try:
        instances = ontology_manager.get_entity_instances(entity_type=type_name, limit=limit)
        if not instances and instances is not None: # instances could be an empty list which is valid
             # It might be better to always return 200 with an empty list if type exists but has no instances.
             # The service layer should clarify if an empty list means "type not found" or "type found, no instances".
             # For now, assume empty list is a valid response.
             pass
        return {"entity_type": type_name, "instances": instances}
    except Exception as e: # Catch more specific errors if possible
        raise HTTPException(status_code=500, detail=f"Error fetching instances for '{type_name}': {str(e)}")


# Example of how to integrate this router into a main FastAPI app:
# from fastapi import FastAPI
# app = FastAPI()
# app.include_router(router, prefix="/api/v1", tags=["ontology"])
# if __name__ == "__main__":
#     import uvicorn
#     # This is for local testing of the router, not for production.
#     # You would run the main app that includes this router.
#     # To run this file directly for testing:
#     # 1. Ensure OntologyManager, etc., can be imported (e.g., by adjusting PYTHONPATH or project structure).
#     # 2. Run: uvicorn backend.app.api.v1.endpoints.ontology:router --reload --port 8001 --factory
#     # (The --factory flag tells uvicorn that 'router' is an APIRouter instance, not a full FastAPI app)
#     # However, it's better to test by including it in a minimal FastAPI app instance:
#     _test_app = FastAPI()
#     _test_app.include_router(router, prefix="/api/v1/ontology_test") # Use a test prefix
#     # uvicorn.run(_test_app, host="0.0.0.0", port=8001)
#
#     # To make this runnable for demonstration, we'd need to ensure services are importable.
#     # This typically means running from the project root with PYTHONPATH set.
#     # For now, this __main__ block is commented out as it depends on execution context.
#     pass

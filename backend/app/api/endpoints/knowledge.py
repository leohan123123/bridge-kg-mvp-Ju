from fastapi import APIRouter, Depends, HTTPException, status
from ...services.graph_service import GraphDatabaseService, get_graph_service
from ...models.graph_models import NodeModel, BridgeModel, ComponentModel, MaterialModel # Assuming these are defined
import uuid

router = APIRouter()

@router.post("/import-dxf/{file_id}", status_code=status.HTTP_201_CREATED)
async def import_dxf_knowledge(
    file_id: str,
    graph_service: GraphDatabaseService = Depends(get_graph_service)
):
    # Basic check for file_id (though not used yet)
    if not file_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file_id is required")

    # Simulate reading preprocessed DXF data
    # In a real scenario, this would come from reading and processing a file linked by file_id
    mock_dxf_data = {
        "bridge": {"id": f"bridge_{file_id}_{str(uuid.uuid4())[:4]}", "name": f"Bridge-{file_id}"},
        "components": [
            {"id": f"comp_A_{file_id}_{str(uuid.uuid4())[:4]}", "name": "Main Girder", "material_id": f"mat_steel_{file_id}"},
            {"id": f"comp_B_{file_id}_{str(uuid.uuid4())[:4]}", "name": "Deck Slab", "material_id": f"mat_concrete_{file_id}"}
        ],
        "materials": [
            {"id": f"mat_steel_{file_id}", "name": "Structural Steel"},
            {"id": f"mat_concrete_{file_id}", "name": "Reinforced Concrete"}
        ]
    }

    try:
        # Create Bridge node
        bridge_data = mock_dxf_data["bridge"]
        bridge_node = BridgeModel(id=bridge_data["id"], name=bridge_data["name"])
        graph_service.create_node(label="Bridge", node_data=bridge_node)

        # Create Material nodes
        for mat_data in mock_dxf_data["materials"]:
            material_node = MaterialModel(id=mat_data["id"], name=mat_data["name"])
            graph_service.create_node(label="Material", node_data=material_node)

        # Create Component nodes
        for comp_data in mock_dxf_data["components"]:
            # For this PoC, we're not creating relationships yet, just the nodes.
            # The 'material_id' in comp_data is noted but not used to link here to keep it simple.
            component_node = ComponentModel(id=comp_data["id"], name=comp_data["name"])
            graph_service.create_node(label="Component", node_data=component_node)

        return {"status": "success", "file_id": file_id, "message": "Nodes created successfully from DXF data."}

    except Exception as e:
        # Very basic error handling for PoC
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to import DXF data: {str(e)}")


VALID_NODE_TYPES = ["Bridge", "Component", "Material"]

@router.get("/nodes/{node_type}")
async def get_nodes_by_type(
    node_type: str,
    graph_service: GraphDatabaseService = Depends(get_graph_service)
):
    if node_type not in VALID_NODE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid node_type: {node_type}. Allowed types are: {', '.join(VALID_NODE_TYPES)}"
        )
    try:
        nodes_data = graph_service.get_nodes_by_label(label=node_type)
        return {"nodes": nodes_data, "count": len(nodes_data)}
    except Exception as e:
        # Log the exception e for debugging if necessary
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching nodes: {str(e)}"
        )

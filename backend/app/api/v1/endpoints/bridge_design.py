from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any

# Attempt to import services with a fallback mechanism for path issues.
# This is to help the agent run the code in environments where PYTHONPATH might not be pre-configured.
services_initialized_correctly = False
try:
    # Standard import attempts
    from app.services.bridge_design_ontology import BridgeDesignOntologyService, BRIDGE_DESIGN_ONTOLOGY
    from app.services.design_knowledge_extractor import DesignKnowledgeExtractor
    from app.services.design_standards_kb import DesignStandardsKB
    from app.services.design_calculation_engine import (
        DesignCalculationEngine,
        _calculate_beam_bending_moment_simple_point_load,
        _calculate_concrete_compressive_strength_design_value
    )
    services_initialized_correctly = True
except ImportError as e_initial_import:
    print(f"Initial import failed: {e_initial_import}. Attempting sys.path modification for backend services.")
    import sys
    import os
    # Assuming this file is backend/app/api/v1/endpoints/bridge_design.py
    # Adjust path to reach the 'backend' directory, which should contain the 'app' package.
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    # Path to 'backend' directory: current_file_dir -> endpoints -> v1 -> api -> app -> backend
    path_to_project_root_containing_backend = os.path.abspath(os.path.join(current_file_dir, "../../../../.."))
    # Or, more directly, path to 'backend' if it's the top-level of 'app'
    path_to_backend_parent = os.path.abspath(os.path.join(current_file_dir, "../../../..")) # This should be parent of 'app'

    # Add the directory that *contains* the 'app' package to sys.path
    # If 'app' is directly under 'backend', then 'backend' is the one to add.
    # If your structure is 'some_project_root/backend/app', add 'some_project_root/backend'.

    # Let's assume 'path_to_backend_parent' is the directory containing 'app'.
    if path_to_backend_parent not in sys.path:
        sys.path.insert(0, path_to_backend_parent)
        print(f"Added to sys.path: {path_to_backend_parent}")

    try:
        # Retry imports
        from app.services.bridge_design_ontology import BridgeDesignOntologyService, BRIDGE_DESIGN_ONTOLOGY
        from app.services.design_knowledge_extractor import DesignKnowledgeExtractor
        from app.services.design_standards_kb import DesignStandardsKB
        from app.services.design_calculation_engine import (
            DesignCalculationEngine,
            _calculate_beam_bending_moment_simple_point_load,
            _calculate_concrete_compressive_strength_design_value
        )
        print("Service modules imported successfully after path adjustment.")
        services_initialized_correctly = True
    except ImportError as e_fallback_import:
        print(f"Fallback import also failed: {e_fallback_import}. Defining dummy services.")
        # Define dummy/placeholder versions of services and constants if all imports fail
        # This allows the rest of the FastAPI router setup to proceed without NameErrors,
        # though the API endpoints will not function correctly.
        BRIDGE_DESIGN_ONTOLOGY = {}
        class BridgeDesignOntologyService: pass
        class DesignKnowledgeExtractor:
            def __init__(self, *args, **kwargs): self.design_ontology = {}
            def extract_design_principles(self, t): return []
            def extract_calculation_formulas(self, t): return []
            def extract_design_parameters(self, t): return []
            def extract_design_constraints(self, t): return []
            def extract_design_standards(self, t): return []
        class DesignStandardsKB:
            def __init__(self): self.standards_database = {}
            def parse_design_codes(self, d): pass
            def get_standard(self, c): return None
            def build_standards_hierarchy(self, l): return {}
        class DesignCalculationEngine:
            def __init__(self): self.calculation_methods = {}
            def register_calculation_method(self, *args, **kwargs): pass
            def execute_calculation(self, m, p): return {"error": "Engine not initialized"}
        def _calculate_beam_bending_moment_simple_point_load(*args, **kwargs): return {}
        def _calculate_concrete_compressive_strength_design_value(*args, **kwargs): return {}

router = APIRouter()

# Initialize services - these will be the dummy versions if imports failed.
# In a production FastAPI app, use Depends for service instances.
ontology_service = BridgeDesignOntologyService()
knowledge_extractor = DesignKnowledgeExtractor() # Assumes BRIDGE_DESIGN_ONTOLOGY is available
standards_kb = DesignStandardsKB()
calculation_engine = DesignCalculationEngine()

if services_initialized_correctly:
    # Populate some initial data for services only if they were loaded correctly
    sample_standard_doc = """
    《示例规范》 EX 123-2023
    1.0.1 本规范适用于...
    2.1.1 设计荷载应取100kN。
    """
    standards_kb.parse_design_codes([sample_standard_doc])

    calculation_engine.register_calculation_method(
        "beam_bending_moment_SPL",
        {
            "description": "Max bending moment for simply supported beam, central point load.",
            "parameters": ["point_load_P (kN)", "span_L (m)"],
            "outputs": ["max_moment_M (kNm)"],
            "formula_str": "M = P * L / 4"
        },
        _calculate_beam_bending_moment_simple_point_load
    )
    calculation_engine.register_calculation_method(
        "concrete_strength_design",
        {
            "description": "Calculates design compressive strength of concrete.",
            "parameters": ["f_ck (MPa)", "gamma_c"],
            "outputs": ["f_cd (MPa)"],
            "formula_str": "f_cd = f_ck / gamma_c"
        },
        _calculate_concrete_compressive_strength_design_value
    )
else:
    print("Skipping data population due to service import failures.")


@router.get("/ontology", summary="获取设计本体结构")
async def get_design_ontology():
    """
    Retrieves the entire bridge design ontology structure.
    """
    # Check if BRIDGE_DESIGN_ONTOLOGY was actually loaded or is the dummy
    if not BRIDGE_DESIGN_ONTOLOGY and services_initialized_correctly: # Only raise if it should have been loaded
        raise HTTPException(status_code=404, detail="Ontology not loaded or empty.")
    elif not services_initialized_correctly:
         raise HTTPException(status_code=503, detail="Ontology service not available due to import errors.")
    return BRIDGE_DESIGN_ONTOLOGY

# Pydantic models for request bodies (optional but good practice)
from pydantic import BaseModel
class TextForExtraction(BaseModel):
    text: str
    extract_types: List[str] = ["principles", "formulas", "parameters", "constraints", "standards"]

class DesignValidationRequest(BaseModel):
    design_rules: List[Dict[str, str]] # e.g. [{"if": "concept_A", "then": "concept_B_is_related"}]
    # Or more complex structure depending on what validate_design_logic expects
    # For now, using the simple list of dicts from BridgeDesignOntologyService.

class CalculationExecutionRequest(BaseModel):
    method_name: str
    parameters: Dict[str, float]


@router.post("/extract_knowledge", summary="提取设计知识")
async def extract_design_knowledge(payload: TextForExtraction = Body(...)):
    """
    Extracts various types of design knowledge from the provided text.
    Specify `extract_types` in the request body to control what to extract.
    Available types: "principles", "formulas", "parameters", "constraints", "standards".
    """
    text = payload.text
    extract_types = payload.extract_types
    extracted_data: Dict[str, Any] = {"source_text_snippet": text[:200]}

    if "principles" in extract_types:
        extracted_data["principles"] = knowledge_extractor.extract_design_principles(text)
    if "formulas" in extract_types:
        extracted_data["formulas"] = knowledge_extractor.extract_calculation_formulas(text)
    if "parameters" in extract_types:
        extracted_data["parameters"] = knowledge_extractor.extract_design_parameters(text)
    if "constraints" in extract_types:
        extracted_data["constraints"] = knowledge_extractor.extract_design_constraints(text)
    if "standards" in extract_types:
        extracted_data["standards"] = knowledge_extractor.extract_design_standards(text)

    # Optional: Link dependencies if multiple types were extracted
    # This is a conceptual step; link_design_dependencies expects a flat list of all extractions.
    # For a more useful API, one might make dependency linking a separate endpoint or a specific option.
    # all_extractions = []
    # for key in ["principles", "formulas", "parameters", "constraints", "standards"]:
    #     if key in extracted_data:
    #         all_extractions.extend(extracted_data[key])
    # if all_extractions:
    #    extracted_data["dependencies"] = knowledge_extractor.link_design_dependencies(all_extractions)

    if not any(key in extracted_data for key in extract_types):
        return {"message": "No extraction types processed or no data found for specified types.", "extracted_data": extracted_data}

    return extracted_data


@router.get("/standards", summary="获取设计规范")
async def get_design_standards(standard_code: str = None, hierarchy: bool = False):
    """
    Retrieves design standards.
    - If `standard_code` is provided, returns details for that specific standard.
    - If `hierarchy` is true, returns the hierarchical structure of all loaded standards.
    - Otherwise, returns a list of all loaded standard codes.
    """
    if standard_code:
        standard_data = standards_kb.get_standard(standard_code)
        if not standard_data:
            raise HTTPException(status_code=404, detail=f"Standard with code '{standard_code}' not found.")
        return standard_data
    elif hierarchy:
        return standards_kb.build_standards_hierarchy([]) # Uses internal DB
    else:
        return {"loaded_standard_codes": list(standards_kb.standards_database.keys())}


@router.post("/validate_design", summary="验证设计方案")
async def validate_design_scheme(payload: DesignValidationRequest = Body(...)):
    """
    Validates design logic or rules based on the ontology.
    The `design_rules` format is a list of dictionaries, e.g.,
    `[{"if": "梁桥理论", "then": "弯曲理论_is_applicable"}]`.
    This is a placeholder for a more complex design validation.
    """
    # Using the BridgeDesignOntologyService's validate_design_logic for now.
    # This service's method is quite basic.
    validation_result = ontology_service.validate_design_logic(payload.design_rules)
    if not validation_result.get("is_valid"):
        # Return 422 if validation fails, including error details
        raise HTTPException(status_code=422, detail=validation_result)
    return validation_result


@router.get("/calculation_methods", summary="获取计算方法")
async def get_calculation_methods(method_name: str = None):
    """
    Retrieves available calculation methods.
    - If `method_name` is provided, returns details for that specific method.
    - Otherwise, returns a list of all available calculation method names and their descriptions.
    """
    if method_name:
        method_data = calculation_engine.calculation_methods.get(method_name)
        if not method_data:
            raise HTTPException(status_code=404, detail=f"Calculation method '{method_name}' not found.")
        # The calculation_function itself is not serializable to JSON, so exclude it.
        return {k: v for k, v in method_data.items() if k != "calculation_function"}
    else:
        return [
            {"name": name, "description": data.get("description"), "parameters": data.get("parameters"), "outputs": data.get("outputs")}
            for name, data in calculation_engine.calculation_methods.items()
        ]

@router.post("/execute_calculation", summary="执行设计计算")
async def execute_design_calculation(payload: CalculationExecutionRequest = Body(...)):
    """
    Executes a registered design calculation method with the given parameters.
    Request body example:
    `{"method_name": "beam_bending_moment_SPL", "parameters": {"point_load_P": 100.0, "span_L": 5.0}}`
    """
    result = calculation_engine.execute_calculation(payload.method_name, payload.parameters)
    if "error" in result:
        # Determine appropriate status code based on error type
        if "not found" in result["error"].lower() or "missing parameters" in result["error"].lower():
            status_code = 404 # Or 422 for missing params
        else:
            status_code = 500 # Internal server error for calculation failures
        raise HTTPException(status_code=status_code, detail=result["error"])
    return result


# Example of how this router might be included in a main FastAPI app:
# from fastapi import FastAPI
# app = FastAPI()
# app.include_router(router, prefix="/api/v1/bridge_design", tags=["Bridge Design Knowledge Base"])

# To run this file directly for testing with uvicorn ( FastAPI's ASGI server):
# `uvicorn backend.app.api.v1.endpoints.bridge_design:app --reload`
# You'd need to define `app = FastAPI()` here and include the router as above.
# For now, this file only defines the router.
if __name__ == "__main__":
    # This block allows direct execution for simple testing of endpoint logic if needed,
    # but full testing requires a FastAPI app and server.
    print("Bridge Design API Endpoints defined. To run, include this router in a FastAPI application.")

    # Basic check for BRIDGE_DESIGN_ONTOLOGY availability to the extractor
    if knowledge_extractor.design_ontology:
        print("Knowledge extractor has access to design ontology.")
    else:
        print("Warning: Knowledge extractor might not have access to design ontology.")

    print("\nSample available calculation methods:")
    for method in get_calculation_methods.__defaults__[0] if get_calculation_methods.__defaults__ else calculation_engine.calculation_methods.items(): # hacky way to get default
        if isinstance(method, tuple): # if items() was used
             print(f"- {method[0]}: {method[1].get('description')}")
        elif isinstance(method, dict) and "name" in method: # if list comp was used
             print(f"- {method['name']}: {method.get('description')}")


    print("\nSample loaded standards:")
    print(standards_kb.standards_database.keys())

    # Example of how to run with Uvicorn if FastAPI app is created here
    # from fastapi import FastAPI
    # import uvicorn
    # app = FastAPI(title="Bridge Design Knowledge Base API Test")
    # app.include_router(router, prefix="/api/v1/bridge_design", tags=["Bridge Design Knowledge Base"])
    # print("Starting Uvicorn server on http://127.0.0.1:8000")
    # uvicorn.run(app, host="127.0.0.1", port=8000)

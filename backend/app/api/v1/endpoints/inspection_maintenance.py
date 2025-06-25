from fastapi import APIRouter, HTTPException, Body, Query
from typing import List, Dict, Any

# Assuming your services are structured in a way that they can be imported like this:
# If not, adjust the import paths accordingly.
from backend.app.services.inspection_maintenance_ontology import InspectionMaintenanceOntologyService, INSPECTION_MAINTENANCE_ONTOLOGY
from backend.app.services.inspection_knowledge_extractor import InspectionKnowledgeExtractor
from backend.app.services.damage_diagnosis_system import DamageDiagnosisSystem
from backend.app.services.maintenance_decision_support import MaintenanceDecisionSupport

router = APIRouter()

# Initialize services
# In a real application, these might be managed with dependency injection
ontology_service = InspectionMaintenanceOntologyService()
knowledge_extractor = InspectionKnowledgeExtractor()
diagnosis_system = DamageDiagnosisSystem()
maintenance_support_system = MaintenanceDecisionSupport()

@router.get("/ontology", summary="获取检测维护本体")
async def get_inspection_maintenance_ontology() -> Dict:
    """
    Retrieve the entire inspection and maintenance ontology.
    """
    return INSPECTION_MAINTENANCE_ONTOLOGY

@router.post("/extract_knowledge", summary="提取检测维护知识")
async def extract_inspection_maintenance_knowledge(text_content: str = Body(..., embed=True, description="Text content to extract knowledge from")) -> Dict[str, List[Dict]]:
    """
    Extract various types of inspection and maintenance knowledge from text.
    This is a simplified endpoint; a real one might allow specifying entity types.
    """
    try:
        detection_methods = knowledge_extractor.extract_detection_methods(text_content)
        damage_patterns = knowledge_extractor.extract_damage_patterns(text_content)
        maintenance_procedures = knowledge_extractor.extract_maintenance_procedures(text_content)
        repair_techniques = knowledge_extractor.extract_repair_techniques(text_content)
        monitoring_requirements = knowledge_extractor.extract_monitoring_requirements(text_content)
        evaluation_criteria = knowledge_extractor.extract_evaluation_criteria(text_content)

        # Potentially link them (though link_inspection_maintenance_chain is a placeholder)
        # linked_info = knowledge_extractor.link_inspection_maintenance_chain(all_extracted_data)

        return {
            "detection_methods": detection_methods,
            "damage_patterns": damage_patterns,
            "maintenance_procedures": maintenance_procedures,
            "repair_techniques": repair_techniques,
            "monitoring_requirements": monitoring_requirements,
            "evaluation_criteria": evaluation_criteria
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting knowledge: {str(e)}")

@router.post("/diagnose_damage", summary="损伤诊断")
async def diagnose_bridge_damage(inspection_data: Dict = Body(..., description="Data from inspection, e.g., {'description': 'Concrete crack observed', 'crack_width_mm': 0.5}")) -> Dict:
    """
    Perform damage diagnosis based on inspection data.
    Returns identified damage, severity, causes, and predicted development.
    """
    try:
        identified_damages = diagnosis_system.identify_damage_type(inspection_data)
        if not identified_damages or identified_damages[0].get("type") == "未知损伤":
            return {"diagnosis_summary": "Could not identify specific damage type from provided data.", "details": identified_damages}

        # For simplicity, diagnose the first identified damage
        # A real system might handle multiple identified damages
        primary_damage_info = identified_damages[0]
        # The identify_damage_type now returns source_data within each damage item.
        # We need to ensure assess_damage_severity gets what it expects.
        # The identify_damage_type returns a list of dicts, e.g. [{'type': '裂缝', 'source_data': inspection_data}]
        # assess_damage_severity expects a dict like {"type": "裂缝", "source_data": inspection_data}

        severity_assessment = diagnosis_system.assess_damage_severity(primary_damage_info)

        # Example environmental factors (could be part of input or fetched)
        environmental_factors = inspection_data.get("environmental_factors", {})
        damage_causes = diagnosis_system.analyze_damage_causes(primary_damage_info, environmental_factors)

        # Example current state and conditions for prediction
        # The current_state for predict_damage_development needs the assessed severity.
        current_state_for_prediction = {
            "type": primary_damage_info.get("type"),
            "assessed_severity": severity_assessment.get("assessed_severity")
        }
        prediction_conditions = inspection_data.get("prediction_conditions", {"high_humidity": False, "heavy_traffic": False})
        damage_prediction = diagnosis_system.predict_damage_development(current_state_for_prediction, prediction_conditions)

        return {
            "identified_damages": identified_damages,
            "severity_assessment": severity_assessment,
            "potential_causes": damage_causes,
            "damage_prediction": damage_prediction
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during damage diagnosis: {str(e)}")

@router.get("/detection_methods", summary="获取检测方法")
async def get_detection_methods(category: str = Query(None, description="Filter by category, e.g., '常规检测', '特殊检测'")) -> Dict:
    """
    Get available detection methods, optionally filtered by category.
    """
    all_methods = INSPECTION_MAINTENANCE_ONTOLOGY.get("检测技术", {})
    if category:
        if category in all_methods:
            return {category: all_methods[category]}
        else:
            raise HTTPException(status_code=404, detail=f"Category '{category}' not found in detection methods.")
    return all_methods

@router.post("/maintenance/generate_plan", summary="生成维护计划")
async def generate_maintenance_plan_endpoint(
    bridge_condition: Dict = Body(..., description="Current condition of the bridge, e.g., {'overall_assessment': 'fair'}"),
    budget_constraints: Dict = Body(..., description="Budget constraints, e.g., {'max_budget': 10000}")
) -> Dict:
    """
    Generate a maintenance plan based on bridge condition and budget.
    """
    try:
        plan = maintenance_support_system.generate_maintenance_plan(bridge_condition, budget_constraints)
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating maintenance plan: {str(e)}")

@router.get("/maintenance/strategies", summary="获取维护策略")
async def get_maintenance_strategies(type: str = Query(None, description="Filter by strategy type, e.g., '预防性维护'")) -> Dict:
    """
    Get available maintenance strategies, optionally filtered by type.
    """
    all_strategies = INSPECTION_MAINTENANCE_ONTOLOGY.get("维护策略", {})
    if type:
        if type in all_strategies:
            return {type: all_strategies[type]}
        else:
            raise HTTPException(status_code=404, detail=f"Strategy type '{type}' not found.")
    return all_strategies


@router.post("/monitoring/setup_system", summary="设置监测系统 (Placeholder)")
async def setup_monitoring_system(config: Dict = Body(..., description="Configuration for the monitoring system")) -> Dict:
    """
    Placeholder for setting up a monitoring system.
    In a real implementation, this would configure sensors, data streams, etc.
    """
    # This is a placeholder. Real implementation would interact with monitoring hardware/software.
    # For now, just acknowledge the configuration.
    print(f"Received monitoring system configuration: {config}")
    # Example: could use knowledge_extractor.extract_monitoring_requirements if text based config
    # monitoring_reqs = knowledge_extractor.extract_monitoring_requirements(config.get("description",""))
    return {"status": "Monitoring system setup initiated (Placeholder)", "received_config": config}

# To make this runnable for testing, you might need a main.py that includes this router.
# For example, in your main FastAPI app:
# from backend.app.api.v1.endpoints import inspection_maintenance
# app.include_router(inspection_maintenance.router, prefix="/api/v1/inspection", tags=["Inspection & Maintenance"])
# (Adjust prefix and tags as needed)

# Example for running this file directly for quick tests (requires uvicorn, fastapi)
if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/inspection_maintenance", tags=["Inspection & Maintenance"])

    # uvicorn.run(app, host="0.0.0.0", port=8000)
    # Command to run: python backend/app/api/v1/endpoints/inspection_maintenance.py
    # Then access http://localhost:8000/api/v1/inspection_maintenance/docs
    print("To run these endpoints, you would typically include this router in your main FastAPI application.")
    print("For a quick standalone test (if uvicorn and fastapi are installed):")
    print("1. Uncomment the uvicorn.run line above.")
    print("2. Run this script: python backend/app/api/v1/endpoints/inspection_maintenance.py")
    print("3. Access API docs at http://localhost:8000/api/v1/inspection_maintenance/docs")
    print("Ensure service classes are correctly imported.")

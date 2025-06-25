from fastapi import APIRouter
from typing import List, Dict

from backend.app.services.construction_ontology import ConstructionOntologyService, CONSTRUCTION_ONTOLOGY
from backend.app.services.construction_knowledge_extractor import ConstructionKnowledgeExtractor
from backend.app.services.construction_standards_kb import ConstructionStandardsKB
from backend.app.services.construction_workflow_engine import ConstructionWorkflowEngine

router = APIRouter()

ontology_service = ConstructionOntologyService()
knowledge_extractor = ConstructionKnowledgeExtractor()
standards_kb = ConstructionStandardsKB()
workflow_engine = ConstructionWorkflowEngine()

from pydantic import BaseModel, Field

# Pydantic models for request bodies
class TextRequestBody(BaseModel):
    text: str

class SpecDocumentsBody(BaseModel):
    spec_documents: List[str] = Field(default_factory=list, description="List of specification document contents or identifiers.")

class WorkflowRequestBody(BaseModel):
    project_type: str
    construction_method: str

class QualityDocsBody(BaseModel):
    quality_docs: List[str] = Field(default_factory=list, description="List of quality document contents or identifiers.")

class SafetyDocsBody(BaseModel):
    safety_docs: List[str] = Field(default_factory=list, description="List of safety document contents or identifiers.")


# GET /api/v1/construction/ontology - 获取施工本体结构
@router.get("/ontology", response_model=Dict, summary="获取施工本体结构")
async def get_construction_ontology_endpoint():
    """
    Retrieves the entire construction process ontology.
    """
    return ontology_service.build_construction_knowledge_graph(CONSTRUCTION_ONTOLOGY)

# POST /api/v1/construction/extract_processes - 提取施工工艺
@router.post("/extract_processes", response_model=List[Dict], summary="提取施工工艺")
async def extract_construction_processes_endpoint(body: TextRequestBody):
    """
    Extracts construction processes from a given text.
    - **text**: The input string to analyze.
    """
    return knowledge_extractor.extract_construction_processes(body.text)

# POST /api/v1/construction/standards - 获取施工标准 (changed to POST to accept body)
@router.post("/standards", response_model=Dict, summary="解析施工技术规范") # Changed from GET to POST
async def parse_construction_specifications_endpoint(body: SpecDocumentsBody):
    """
    Parses construction technical specifications.
    - **spec_documents**: A list of strings, where each string is the content of a specification document.
    """
    return standards_kb.parse_construction_specifications(body.spec_documents)

# POST /api/v1/construction/workflow - 生成施工流程
@router.post("/workflow", response_model=Dict, summary="定义或生成施工流程")
async def define_construction_workflow_endpoint(body: WorkflowRequestBody):
    """
    Defines a construction workflow based on project type and construction method.
    - **project_type**: Type of the construction project (e.g., "小型混凝土桥梁").
    - **construction_method**: Method of construction (e.g., "现浇").
    """
    return workflow_engine.define_construction_workflow(body.project_type, body.construction_method)

# POST /api/v1/construction/quality_control - 获取质量控制要求 (changed to POST to accept body)
@router.post("/quality_control", response_model=Dict, summary="构建质量控制矩阵") # Changed from GET to POST
async def get_quality_control_requirements_endpoint(body: QualityDocsBody):
    """
    Builds a quality control matrix from quality documents.
    - **quality_docs**: A list of strings, where each string is the content of a quality document.
    """
    return standards_kb.build_quality_control_matrix(body.quality_docs)

# POST /api/v1/construction/safety_protocols - 获取安全规程 (changed to POST to accept body)
@router.post("/safety_protocols", response_model=List[Dict], summary="提取安全操作规程") # Changed from GET to POST
async def get_safety_protocols_endpoint(body: SafetyDocsBody):
    """
    Extracts safety protocols from safety documents.
    - **safety_docs**: A list of strings, where each string is the content of a safety document.
    """
    return standards_kb.extract_safety_protocols(body.safety_docs)


# Example of an endpoint using another service from ConstructionOntologyService
@router.post("/validate_logic", response_model=Dict, summary="验证施工逻辑")
async def validate_construction_logic_endpoint(workflows: List[Dict]):
    """
    Validates the logical consistency of a list of construction workflows/processes.
    - **workflows**: A list of dictionaries, each representing a process with an 'id' and 'name'.
                   Optionally 'predecessors' can be included for dependency checks.
    """
    return ontology_service.validate_construction_logic(workflows)

# Example of an endpoint using another service from ConstructionKnowledgeExtractor
@router.post("/extract_parameters", response_model=List[Dict], summary="提取施工参数")
async def extract_construction_parameters_endpoint(body: TextRequestBody):
    """
    Extracts construction parameters from a given text.
    - **text**: The input string to analyze for parameters.
    """
    return knowledge_extractor.extract_construction_parameters(body.text)

# Example of an endpoint using another service from ConstructionStandardsKB
@router.post("/create_checklists", response_model=List[Dict], summary="创建检查清单")
async def create_inspection_checklists_endpoint(standards: List[Dict]):
    """
    Creates inspection checklists based on a list of standards or control points.
    - **standards**: A list of dictionaries, each representing a standard or control point
                     (e.g., output from quality control matrix or parsed specifications).
    """
    return standards_kb.create_inspection_checklists(standards)

# Example of an endpoint using another service from ConstructionWorkflowEngine
class SequenceActivitiesBody(BaseModel):
    activities: List[Dict]

@router.post("/sequence_activities", response_model=List[Dict], summary="排序施工活动")
async def sequence_construction_activities_endpoint(body: SequenceActivitiesBody):
    """
    Sorts construction activities based on their dependencies.
    - **activities**: A list of activity objects, each must have an 'id' and can have 'depends_on' (list of IDs).
    """
    return workflow_engine.sequence_construction_activities(body.activities)

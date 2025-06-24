from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List

from app.services.entity_service import extract_entities

router = APIRouter()

class TextRequest(BaseModel):
    text: str

class EntityResponse(BaseModel):
    entities: Dict[str, List[str]]
    total_count: int

@router.post("/extract", response_model=EntityResponse)
async def extract_entities_api(request: TextRequest):
    """
    Extracts bridge engineering entities from the provided text.
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    entities_result = extract_entities(request.text)

    total_count = 0
    for entity_list in entities_result.values():
        total_count += len(entity_list)

    return {"entities": entities_result, "total_count": total_count}

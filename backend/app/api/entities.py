# backend/app/api/entities.py
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query
from ..entities.knowledge_base import EntityKnowledgeBase

router = APIRouter(prefix="/entities", tags=["Entities & Knowledge Base"])

@router.get("/search")
def search_entities(
    query: str = Query(..., min_length=2, description="Search term for VASP or address")
):
    kb = EntityKnowledgeBase()
    return kb.search(query)

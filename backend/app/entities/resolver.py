# backend/app/entities/resolver.py
from typing import Dict, Any, Optional
from .knowledge_base import EntityKnowledgeBase

class EntityResolver:
    """
    Resolves blockchain addresses to verified VASP clusters and infrastructure roles.
    """

    def __init__(self, kb: Optional[EntityKnowledgeBase] = None):
        self.kb = kb or EntityKnowledgeBase()

    def resolve(self, address: str) -> Dict[str, Any]:
        match = self.kb.lookup(address)
        if match:
            return {
                "address": address,
                "entity_name": match.get("entity_name"),
                "entity_type": match.get("entity_type", "VASP"),
                "confidence": float(match.get("confidence", 1.0)),
                "label_source": match.get("label_source", "KNOWLEDGE_BASE"),
                "notes": match.get("notes")
            }
        
        return {
            "address": address,
            "entity_name": None,
            "entity_type": "INTERMEDIARY",
            "confidence": 0.0,
            "label_source": "UNRESOLVED",
            "notes": None
        }

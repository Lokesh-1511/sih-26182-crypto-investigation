# backend/app/entities/knowledge_base.py
import os
import json
from typing import Dict, Any, Optional, List

class EntityKnowledgeBase:
    """
    Local knowledge base holding verified VASP labels, deposit wallets,
    omnibus hot wallets, mixers, and bridges.
    """

    def __init__(self, kb_dir: Optional[str] = None):
        if kb_dir is None:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
            self.kb_dir = os.path.join(base_dir, "data", "knowledge_base")
        else:
            self.kb_dir = kb_dir

        self.entities: Dict[str, Dict[str, Any]] = {}
        self._load_knowledge_base()

    def _load_knowledge_base(self):
        if not os.path.exists(self.kb_dir):
            return

        files = ["vasp_labels.json", "deposit_wallets.json", "hot_wallets.json", "bridges.json", "mixers.json"]
        for fname in files:
            fpath = os.path.join(self.kb_dir, fname)
            if os.path.exists(fpath):
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        records = json.load(f)
                        if isinstance(records, list):
                            for r in records:
                                addr = r.get("address", "").lower()
                                if addr:
                                    self.entities[addr] = r
                except Exception as e:
                    print(f"Error loading entity file {fname}: {e}")

    def lookup(self, address: str) -> Optional[Dict[str, Any]]:
        return self.entities.get(address.lower())

    def search(self, query: str) -> List[Dict[str, Any]]:
        q = query.lower()
        return [
            ent for ent in self.entities.values()
            if q in ent.get("entity_name", "").lower() or q in ent.get("address", "").lower()
        ]

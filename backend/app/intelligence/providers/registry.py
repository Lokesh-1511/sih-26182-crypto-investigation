# backend/app/intelligence/providers/registry.py
import os
import json
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from .base import AddressIntelligenceProvider
from ..models import EntityResolution, ResolutionStatus, EntityType, EntityCandidate

class LocalRegistryProvider(AddressIntelligenceProvider):
    """
    Deterministic local address intelligence provider.
    Reads verified and synthetic fixture registry files without making external API calls.
    Normalizes addresses (chain-aware) and detects exact, non-VASP, VASP, and ambiguous entity matches.
    """

    def __init__(self, custom_registry_path: Optional[str] = None):
        self._provider_name = "local_deterministic_registry"
        self._custom_registry_path = custom_registry_path
        # Map (chain, normalized_address) -> list of record dicts
        self._registry: Dict[tuple, List[Dict[str, Any]]] = {}
        self._load_registry()

    @property
    def provider_name(self) -> str:
        return self._provider_name

    def _normalize_chain(self, chain: str) -> str:
        c = str(chain).strip().lower()
        if c in ("eth", "ethereum"):
            return "ethereum"
        if c in ("btc", "bitcoin"):
            return "bitcoin"
        if c in ("trx", "tron"):
            return "tron"
        return c

    def _normalize_address(self, chain: str, address: str) -> str:
        c_norm = self._normalize_chain(chain)
        addr = str(address).strip()
        if c_norm in ("ethereum", "polygon", "arbitrum", "bsc"):
            return addr.lower()
        return addr

    def _load_registry(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))

        paths_to_load = []

        if self._custom_registry_path and os.path.exists(self._custom_registry_path):
            paths_to_load.append(self._custom_registry_path)
        else:
            # 1. Test fixtures registry
            fixture_path = os.path.join(base_dir, "tests", "fixtures", "intelligence", "entities.json")
            if os.path.exists(fixture_path):
                paths_to_load.append(fixture_path)

            # 2. Project knowledge base data files
            kb_dir = os.path.join(base_dir, "data", "knowledge_base")
            for fname in ("hot_wallets.json", "deposit_wallets.json", "bridges.json", "mixers.json"):
                fpath = os.path.join(kb_dir, fname)
                if os.path.exists(fpath):
                    paths_to_load.append(fpath)

        for fpath in paths_to_load:
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            if not isinstance(item, dict):
                                continue
                            raw_addr = item.get("address")
                            if not raw_addr:
                                continue
                            raw_chain = item.get("chain", "ethereum")
                            chain_norm = self._normalize_chain(raw_chain)
                            addr_norm = self._normalize_address(chain_norm, raw_addr)

                            key = (chain_norm, addr_norm)
                            if key not in self._registry:
                                self._registry[key] = []
                            self._registry[key].append(item)
            except Exception as e:
                # Silently ignore missing or unparseable secondary files
                pass

    def add_record(self, record: Dict[str, Any]):
        """Helper method to dynamically register entities during testing."""
        raw_addr = record.get("address", "")
        raw_chain = record.get("chain", "ethereum")
        chain_norm = self._normalize_chain(raw_chain)
        addr_norm = self._normalize_address(chain_norm, raw_addr)
        key = (chain_norm, addr_norm)
        if key not in self._registry:
            self._registry[key] = []
        self._registry[key].append(record)

    def _parse_entity_type(self, raw_type: Optional[str]) -> EntityType:
        if not raw_type:
            return EntityType.UNKNOWN
        t = str(raw_type).strip().upper()
        if "VASP" in t or "EXCHANGE" in t or "CENTRALIZED" in t:
            return EntityType.VASP
        if "CUSTODIAN" in t or "CUSTODY" in t:
            return EntityType.CUSTODIAN
        if "PROTOCOL" in t or "DEX" in t or "DEFI" in t:
            return EntityType.PROTOCOL
        if "BRIDGE" in t:
            return EntityType.BRIDGE
        if "MIXER" in t or "PRIVACY" in t:
            return EntityType.PAYMENT_PROVIDER
        if "MINER" in t or "POOL" in t:
            return EntityType.MINER
        return EntityType.UNKNOWN

    async def resolve_address(self, chain: str, address: str) -> EntityResolution:
        chain_norm = self._normalize_chain(chain)
        addr_norm = self._normalize_address(chain_norm, address)
        key = (chain_norm, addr_norm)

        records = self._registry.get(key, [])

        if not records:
            # Address not found in local registry
            return EntityResolution(
                chain=chain_norm,
                address=addr_norm,
                entity_id=None,
                entity_name=None,
                entity_type=None,
                vasp_status=False,
                source=self._provider_name,
                source_reference="registry://not_found",
                resolution_status=ResolutionStatus.NOT_FOUND,
                resolved_at=datetime.now(timezone.utc),
                candidates=[]
            )

        # Check for multiple distinct candidates (ambiguity)
        distinct_entities = {}
        for r in records:
            e_name = r.get("entity_name") or r.get("name") or "Unknown Entity"
            distinct_entities[e_name] = r

        if len(distinct_entities) > 1:
            candidates: List[EntityCandidate] = []
            for r in records:
                e_type_str = r.get("entity_type", "EXCHANGE")
                e_type = self._parse_entity_type(e_type_str)
                is_vasp = r.get("vasp_status", True if e_type in (EntityType.VASP, EntityType.EXCHANGE, EntityType.CUSTODIAN) else False)
                candidates.append(EntityCandidate(
                    entity_id=r.get("entity_id", f"ent_{addr_norm[:8]}"),
                    entity_name=r.get("entity_name", "Unknown Entity"),
                    entity_type=e_type,
                    vasp_status=is_vasp,
                    source=r.get("source", self._provider_name),
                    source_reference=r.get("source_reference", r.get("label_source", "registry://local")),
                    confidence=r.get("confidence", 0.5),
                    notes=r.get("notes")
                ))

            return EntityResolution(
                chain=chain_norm,
                address=addr_norm,
                entity_id=None,
                entity_name="Multiple candidates",
                entity_type=EntityType.UNKNOWN,
                vasp_status=any(c.vasp_status for c in candidates),
                source=self._provider_name,
                source_reference="registry://ambiguous_match",
                resolution_status=ResolutionStatus.AMBIGUOUS,
                resolved_at=datetime.now(timezone.utc),
                candidates=candidates
            )

        # Single distinct entity match (RESOLVED)
        rec = records[0]
        raw_type = rec.get("entity_type", "VASP")
        ent_type = self._parse_entity_type(raw_type)

        # Explicit vasp_status flag if present, else infer from entity type
        if "vasp_status" in rec:
            vasp_status = bool(rec["vasp_status"])
        else:
            vasp_status = ent_type in (EntityType.VASP, EntityType.EXCHANGE, EntityType.CUSTODIAN)

        entity_id = rec.get("entity_id", f"entity_{addr_norm[:10]}")
        entity_name = rec.get("entity_name") or rec.get("name") or "Identified Entity"
        source = rec.get("source") or self._provider_name
        source_ref = rec.get("source_reference") or rec.get("label_source") or "registry://verified_local"

        return EntityResolution(
            chain=chain_norm,
            address=addr_norm,
            entity_id=entity_id,
            entity_name=entity_name,
            entity_type=ent_type,
            vasp_status=vasp_status,
            source=source,
            source_reference=source_ref,
            resolution_status=ResolutionStatus.RESOLVED,
            resolved_at=datetime.now(timezone.utc),
            candidates=[]
        )

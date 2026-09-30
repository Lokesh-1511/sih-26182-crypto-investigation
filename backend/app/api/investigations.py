# backend/app/api/investigations.py
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from ..schemas.investigation import InvestigationCreateRequest, InvestigationResponse
from ..schemas.evidence import CaseDossier
from ..schemas.snapshot import LawfulActionPacket
from ..blockchain.models.enums import Chain
from ..blockchain.providers.base import BlockchainProvider
from ..blockchain.providers.factory import ProviderFactory
from ..blockchain.exceptions import (
    InvalidAddressError,
    UnsupportedChainError,
    RateLimitError,
    AuthenticationError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    BlockchainProviderError
)
from ..services.investigation_service import InvestigationService
from ..evidence.builder import EvidenceBuilder
from ..reports.pdf_generator import ForensicReportGenerator
from ..reports.action_packet import ActionPacketGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/investigations", tags=["Investigations"])

def get_blockchain_provider() -> BlockchainProvider:
    """FastAPI dependency resolving active blockchain provider."""
    return ProviderFactory.get_provider()

def get_investigation_service(
    provider: BlockchainProvider = Depends(get_blockchain_provider)
) -> InvestigationService:
    """FastAPI dependency injecting InvestigationService."""
    return InvestigationService(provider=provider)

@router.post(
    "",
    response_model=InvestigationResponse,
    status_code=status.HTTP_200_OK,
    summary="Create and execute a wallet investigation",
    description=(
        "Orchestrates multi-hop blockchain transfer collection, builds the fund-flow graph, "
        "resolves known entities, identifies VASP infrastructure, generates canonical evidence items, "
        "and returns a complete, traceable investigation payload with exact Decimal precision."
    ),
    responses={
        200: {"description": "Investigation completed successfully"},
        400: {"description": "Invalid wallet address format or unsupported blockchain"},
        429: {"description": "Upstream intelligence API rate limit exceeded"},
        502: {"description": "Upstream blockchain provider communication/auth failure"},
        503: {"description": "Blockchain provider service currently unavailable"},
        504: {"description": "Upstream blockchain provider query timed out"},
    }
)
async def create_investigation(
    request: InvestigationCreateRequest,
    service: InvestigationService = Depends(get_investigation_service)
) -> InvestigationResponse:
    """
    Thin FastAPI endpoint routing validated requests to InvestigationService.
    """
    try:
        return await service.investigate(request)
    except InvalidAddressError as e:
        logger.warning(f"Address validation rejected: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except UnsupportedChainError as e:
        logger.warning(f"Unsupported chain requested: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RateLimitError as e:
        logger.error(f"Rate limit exceeded: {e}")
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Upstream blockchain provider rate limit exceeded")
    except AuthenticationError as e:
        logger.error("Provider authentication failed")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Blockchain provider authentication failed")
    except ProviderTimeoutError as e:
        logger.error(f"Provider timeout: {e}")
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Upstream blockchain provider query timed out")
    except ProviderUnavailableError as e:
        logger.error(f"Provider unavailable: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Blockchain provider service unavailable")
    except BlockchainProviderError as e:
        logger.error(f"Blockchain provider error: {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Blockchain provider query error")
    except Exception as e:
        logger.exception("Unexpected error during investigation execution")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during investigation")


@router.post(
    "/dossier",
    response_model=CaseDossier,
    status_code=status.HTTP_200_OK,
    summary="Generate canonical Case Dossier with SHA-256 evidence digest",
    description="Transforms an InvestigationResponse into a structured, reproducible CaseDossier with evidence matrix."
)
async def generate_dossier(
    investigation: InvestigationResponse
) -> CaseDossier:
    """
    Generates a canonical forensic Case Dossier with SHA-256 evidence package hash.
    """
    try:
        return EvidenceBuilder.build_case_dossier(investigation)
    except Exception as e:
        logger.exception("Failed to generate case dossier")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Dossier generation failed: {str(e)}")


@router.post(
    "/pdf",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Generate Court-Admissible Forensic Report (HTML/PDF)",
    description="Renders a court-admissible forensic case dossier report with embedded SHA-256 evidence digest."
)
async def generate_pdf_report(
    investigation: InvestigationResponse,
    investigator: str = "Authorized Investigating Officer"
) -> Dict[str, Any]:
    """
    Generates a court-admissible forensic report and returns report path, HTML payload, and evidence SHA-256 digest.
    """
    try:
        dossier = EvidenceBuilder.build_case_dossier(investigation)
        report_meta = ForensicReportGenerator.generate_dossier_report(dossier=dossier, investigator=investigator)
        return report_meta
    except Exception as e:
        logger.exception("Failed to generate report")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Report generation failed: {str(e)}")


@router.post(
    "/action-packet",
    response_model=LawfulActionPacket,
    status_code=status.HTTP_200_OK,
    summary="Generate Lawful Action Packet Draft",
    description="Drafts a Section 91 CrPC / statutory preservation and disclosure notice for primary attributed VASP infrastructure."
)
async def generate_action_packet(
    investigation: InvestigationResponse,
    investigator: str = "Authorized Investigating Officer",
    target_vasp_id: Optional[str] = None
) -> LawfulActionPacket:
    """
    Drafts an authorized review-ready legal requisition packet for attributed VASP infrastructure.
    """
    try:
        return ActionPacketGenerator.generate_from_investigation(
            investigation=investigation,
            investigator=investigator,
            target_vasp_id=target_vasp_id
        )
    except Exception as e:
        logger.exception("Failed to generate action packet")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Action packet generation failed: {str(e)}")

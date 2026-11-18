"""KEEP Phase 4.5 — Research Agents Package."""

from backend.app.agents.research.agent import (
    MAX_CORRECTION_ATTEMPTS,
    KeepResearchAgent,
    build_research_agent_metadata,
)
from backend.app.agents.research.citations import (
    CitationValidationReport,
    validate_evidence_references,
)
from backend.app.agents.research.contracts import (
    REPORT_READY_STATUSES,
    RESEARCH_SCHEMA_VERSION,
    TERMINAL_RESEARCH_STATUSES,
    ClaimType,
    ConfidenceLevel,
    ContradictionRecord,
    EvidenceItem,
    QualityCheckResult,
    RequiredOutputType,
    ResearchEventRecord,
    ResearchFinding,
    ResearchQualityInterface,
    ResearchReport,
    ResearchRepositoryInterface,
    ResearchRequest,
    ResearchRetrievalInterface,
    ResearchRunRecord,
    ResearchStatus,
    ResearchSynthesisInterface,
    RetrievalOutcome,
    SynthesisDraft,
    compute_research_fingerprint,
    generate_research_event_id,
    generate_research_id,
)
from backend.app.agents.research.evidence import (
    normalize_evidence_items,
    sanitize_research_passage,
)
from backend.app.agents.research.graph import (
    build_default_research_agent,
    build_research_graph,
)
from backend.app.agents.research.prompts import (
    RESEARCH_SYSTEM_PROMPT,
    build_citation_correction_prompt,
    build_research_synthesis_prompt,
)
from backend.app.agents.research.quality import (
    ResearchQualityValidator,
    detect_evidence_stance_conflicts,
)
from backend.app.agents.research.repository import (
    InMemoryResearchRepository,
    SQLAlchemyResearchRepository,
)
from backend.app.agents.research.research_service import (
    KeepResearchService,
    caller_can_view_sensitive_evidence,
)
from backend.app.agents.research.retrieval import KeepResearchRetrievalService
from backend.app.agents.research.source_registry import (
    AuthorizedSourceCatalog,
    ResearchSourceDocument,
    build_default_research_corpus,
)
from backend.app.agents.research.synthesis import KeepResearchSynthesisService

__all__ = [
    "MAX_CORRECTION_ATTEMPTS",
    "REPORT_READY_STATUSES",
    "RESEARCH_SCHEMA_VERSION",
    "RESEARCH_SYSTEM_PROMPT",
    "TERMINAL_RESEARCH_STATUSES",
    "AuthorizedSourceCatalog",
    "CitationValidationReport",
    "ClaimType",
    "ConfidenceLevel",
    "ContradictionRecord",
    "EvidenceItem",
    "InMemoryResearchRepository",
    "KeepResearchAgent",
    "KeepResearchRetrievalService",
    "KeepResearchService",
    "KeepResearchSynthesisService",
    "QualityCheckResult",
    "RequiredOutputType",
    "ResearchEventRecord",
    "ResearchFinding",
    "ResearchQualityInterface",
    "ResearchQualityValidator",
    "ResearchReport",
    "ResearchRepositoryInterface",
    "ResearchRequest",
    "ResearchRetrievalInterface",
    "ResearchRunRecord",
    "ResearchSourceDocument",
    "ResearchStatus",
    "ResearchSynthesisInterface",
    "RetrievalOutcome",
    "SQLAlchemyResearchRepository",
    "SynthesisDraft",
    "build_citation_correction_prompt",
    "build_default_research_agent",
    "build_default_research_corpus",
    "build_research_agent_metadata",
    "build_research_graph",
    "build_research_synthesis_prompt",
    "caller_can_view_sensitive_evidence",
    "compute_research_fingerprint",
    "detect_evidence_stance_conflicts",
    "generate_research_event_id",
    "generate_research_id",
    "normalize_evidence_items",
    "sanitize_research_passage",
    "validate_evidence_references",
]

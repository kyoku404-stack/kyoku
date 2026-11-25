"""Phase 4.11 — Proactive Enterprise Intelligence Package."""

from backend.app.agents.intelligence.contracts import (
    DetectionRunRecord,
    EvidenceReference,
    InsightCategory,
    InsightDismissRequest,
    InsightFeedbackRecord,
    InsightFeedbackRequest,
    InsightInvestigateRequest,
    InsightResolveRequest,
    InsightStatus,
    IntelligenceAuditEvent,
    IntelligenceCandidate,
    IntelligenceInsight,
    IntelligenceSecurityContext,
    OperationalMetrics,
    ScanRequest,
    SuppressionRecord,
)
from backend.app.agents.intelligence.deduplication import (
    build_suppression_record,
    compute_dedup_key,
    is_suppressed,
)
from backend.app.agents.intelligence.insight_registry import InsightRegistry
from backend.app.agents.intelligence.prioritization import (
    RANKING_VERSION,
    calculate_priority_score,
    rank_insights,
    score_candidate,
)
from backend.app.agents.intelligence.repository import (
    BaseIntelligenceRepository,
    InMemoryIntelligenceRepository,
)
from backend.app.agents.intelligence.service import IntelligenceService

__all__ = [
    "RANKING_VERSION",
    "BaseIntelligenceRepository",
    "DetectionRunRecord",
    "EvidenceReference",
    "InMemoryIntelligenceRepository",
    "InsightCategory",
    "InsightDismissRequest",
    "InsightFeedbackRecord",
    "InsightFeedbackRequest",
    "InsightInvestigateRequest",
    "InsightRegistry",
    "InsightResolveRequest",
    "InsightStatus",
    "IntelligenceAuditEvent",
    "IntelligenceCandidate",
    "IntelligenceInsight",
    "IntelligenceSecurityContext",
    "IntelligenceService",
    "OperationalMetrics",
    "ScanRequest",
    "SuppressionRecord",
    "build_suppression_record",
    "calculate_priority_score",
    "compute_dedup_key",
    "is_suppressed",
    "rank_insights",
    "score_candidate",
]

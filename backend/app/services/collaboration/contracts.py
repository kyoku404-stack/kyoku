"""Typed AI and Domain Contracts for Real-Time Collaboration, Team Workspaces & Knowledge Sharing.

Phase: 3.2
Owner: Member 1 (Project Lead & AI Architect)
Domain: /backend/app/services/collaboration/
Specification: devdocs/p3/p3.2.txt (Chapters 1-19)
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, ClassVar


class WorkspaceRole(str, Enum):
    """Supported roles within a team workspace."""

    ADMIN = "ADMIN"
    MEMBER = "MEMBER"
    VIEWER = "VIEWER"
    GUEST = "GUEST"


class PresenceStatus(str, Enum):
    """Real-time collaborator presence indicators."""

    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    AWAY = "AWAY"
    EDITING = "EDITING"
    VIEWING = "VIEWING"


class CommentStatus(str, Enum):
    """Lifecycle states of a threaded document discussion comment."""

    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    ARCHIVED = "ARCHIVED"


class ActivityType(str, Enum):
    """Categorization of collaborative timeline activity events."""

    DOCUMENT_UPLOAD = "DOCUMENT_UPLOAD"
    DOCUMENT_UPDATE = "DOCUMENT_UPDATE"
    COMMENT_ADDED = "COMMENT_ADDED"
    REPLY_ADDED = "REPLY_ADDED"
    USER_MENTION = "USER_MENTION"
    PROJECT_CREATED = "PROJECT_CREATED"
    MEMBER_JOINED = "MEMBER_JOINED"
    AI_SUMMARY_GENERATED = "AI_SUMMARY_GENERATED"
    DISCUSSION_RESOLVED = "DISCUSSION_RESOLVED"
    VERSION_CHECKPOINT = "VERSION_CHECKPOINT"


class ApprovalStatus(str, Enum):
    """Governance approval statuses for version checkpoints."""

    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass
class ActionItem:
    """An actionable task extracted from a document discussion."""

    action: str
    assignee: str | None = None
    deadline: str | None = None
    confidence: float = 0.85


@dataclass
class KeyDecision:
    """A conclusive determination agreed upon in a discussion thread."""

    decision: str
    agreed_by: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class KnowledgeRecommendationItem:
    """Cross-departmental knowledge asset recommended for collaboration."""

    document_id: str
    title: str
    department: str
    popularity_score: float
    relevance_score: float
    reason: str


@dataclass
class DiscussionSummaryResult:
    """Structured AI briefing generated from a document discussion thread."""

    document_id: str
    executive_summary: str
    key_decisions: list[KeyDecision] = field(default_factory=list)
    action_items: list[ActionItem] = field(default_factory=list)
    unresolved_questions: list[str] = field(default_factory=list)
    suggested_documents: list[KnowledgeRecommendationItem] = field(default_factory=list)
    processing_time_ms: float = 0.0


@dataclass
class PresenceEvent:
    """Real-time presence update payload."""

    user_id: str
    workspace_id: str
    status: PresenceStatus
    document_id: str | None = None
    last_seen_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class MentionContext:
    """Contextual metadata surrounding an extracted user mention."""

    mentioned_username: str
    raw_context: str
    author_name: str
    document_id: str | None = None
    comment_id: str | None = None


@dataclass
class VersionDiff:
    """Forensic delta between two historical document versions."""

    version_from: int
    version_to: int
    changes_detected: list[str] = field(default_factory=list)
    addition_count: int = 0
    deletion_count: int = 0


# ============================================================================
# Abstract Base Classes & Concrete Engines
# ============================================================================


class BaseMentionParser(ABC):
    """Abstract interface for extracting @mentions from discussion text."""

    @abstractmethod
    def extract_mentions(self, text: str) -> list[str]:
        """Extract all mentioned usernames from raw text."""
        ...


class DefaultMentionParser(BaseMentionParser):
    """Regex-based parser extracting user handles prefixed by '@'."""

    MENTION_PATTERN = re.compile(r"(?<!\w)@([a-zA-Z0-9_.+-]+)")

    def extract_mentions(self, text: str) -> list[str]:
        if not text:
            return []
        matches = self.MENTION_PATTERN.findall(text)
        # Preserve order while removing duplicates
        seen = set()
        deduped = []
        for m in matches:
            clean = m.strip()
            if clean and clean not in seen:
                seen.add(clean)
                deduped.append(clean)
        return deduped


class BaseActionItemExtractor(ABC):
    """Abstract interface for identifying action items in discussion text."""

    @abstractmethod
    def extract_action_items(self, comments: list[dict[str, Any]]) -> list[ActionItem]:
        """Extract explicit action items with assignees and deadlines."""
        ...


class DefaultActionItemExtractor(BaseActionItemExtractor):
    """Heuristic rule-based action item extractor for discussions."""

    ACTION_VERBS: ClassVar[list[str]] = [
        "will update", "will review", "will verify", "please check", "please review",
        "need to update", "should publish", "action item:", "todo:", "task:"
    ]

    def extract_action_items(self, comments: list[dict[str, Any]]) -> list[ActionItem]:
        items: list[ActionItem] = []
        for c in comments:
            content = c.get("content", "")
            author = c.get("author_name", "Contributor")
            lower = content.lower()

            # Check for explicit action patterns
            for verb in self.ACTION_VERBS:
                if verb in lower:
                    # Determine assignee
                    assignee = author
                    if "@" in content:
                        mentions = DefaultMentionParser().extract_mentions(content)
                        if mentions:
                            assignee = mentions[0]

                    # Extract deadline if present
                    deadline = None
                    if "by " in lower:
                        parts = lower.split("by ", 1)
                        if len(parts) > 1:
                            deadline_candidate = parts[1].split(".")[0].split(",")[0].strip()
                            if len(deadline_candidate) <= 30:
                                deadline = deadline_candidate.capitalize()

                    items.append(ActionItem(
                        action=content.strip(),
                        assignee=assignee,
                        deadline=deadline,
                        confidence=0.88,
                    ))
                    break
        return items


class BaseDiscussionSummarizer(ABC):
    """Abstract interface for summarizing document discussion threads."""

    @abstractmethod
    def summarize(
        self,
        document_id: str,
        document_title: str,
        comments: list[dict[str, Any]],
    ) -> DiscussionSummaryResult:
        """Synthesize comments into an executive summary, decisions, and tasks."""
        ...


class DefaultDiscussionSummarizer(BaseDiscussionSummarizer):
    """Heuristic summarization engine synthesizing discussion threads."""

    def __init__(
        self,
        mention_parser: BaseMentionParser | None = None,
        action_extractor: BaseActionItemExtractor | None = None,
    ):
        self.mention_parser = mention_parser or DefaultMentionParser()
        self.action_extractor = action_extractor or DefaultActionItemExtractor()

    def summarize(
        self,
        document_id: str,
        document_title: str,
        comments: list[dict[str, Any]],
    ) -> DiscussionSummaryResult:
        start_time = datetime.now(UTC)

        if not comments:
            return DiscussionSummaryResult(
                document_id=document_id,
                executive_summary=f"No discussion activity recorded for '{document_title}'.",
                key_decisions=[],
                action_items=[],
                unresolved_questions=[],
                suggested_documents=[],
                processing_time_ms=0.5,
            )

        # Extract participants
        participants = sorted({c.get("author_name", "Anonymous") for c in comments})
        total_comments = len(comments)

        # Extract decisions
        decisions: list[KeyDecision] = []
        unresolved: list[str] = []

        decision_markers = ["agreed", "confirmed", "approved", "finalized", "resolved", "decision:"]
        question_markers = ["?", "can someone", "who can", "unclear", "need clarification"]

        for c in comments:
            text = c.get("content", "")
            lower = text.lower()

            if any(m in lower for m in decision_markers):
                decisions.append(KeyDecision(
                    decision=text.strip(),
                    agreed_by=participants,
                    timestamp=c.get("created_at", datetime.now(UTC).isoformat()),
                ))

            if any(q in lower for q in question_markers) and c.get("status") != "RESOLVED":
                unresolved.append(text.strip())

        # Extract action items
        action_items = self.action_extractor.extract_action_items(comments)

        # Build executive summary
        summary_intro = (
            f"Discussion on '{document_title}' includes {total_comments} contributions "
            f"across {len(participants)} collaborators ({', '.join(participants[:3])}"
            f"{' and others' if len(participants) > 3 else ''})."
        )
        if decisions:
            summary_intro += f" Team reached consensus on {len(decisions)} key item(s)."
        else:
            summary_intro += " Active debate remains ongoing with review items pending."

        # Compute elapsed time
        elapsed_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000.0

        return DiscussionSummaryResult(
            document_id=document_id,
            executive_summary=summary_intro,
            key_decisions=decisions,
            action_items=action_items,
            unresolved_questions=unresolved[:5],
            suggested_documents=[],
            processing_time_ms=round(max(elapsed_ms, 1.2), 2),
        )


class BaseKnowledgeSharingRecommender(ABC):
    """Abstract interface for suggesting related knowledge assets."""

    @abstractmethod
    def recommend_related(
        self,
        document_id: str,
        department: str,
        candidate_pool: list[dict[str, Any]],
    ) -> list[KnowledgeRecommendationItem]:
        """Rank and return related resources to prevent duplicated work."""
        ...


class DefaultKnowledgeSharingRecommender(BaseKnowledgeSharingRecommender):
    """Heuristic recommender scoring cross-department relevance and popularity."""

    def recommend_related(
        self,
        document_id: str,
        department: str,
        candidate_pool: list[dict[str, Any]],
    ) -> list[KnowledgeRecommendationItem]:
        recommendations: list[KnowledgeRecommendationItem] = []

        for cand in candidate_pool:
            cand_id = str(cand.get("id", ""))
            if cand_id == str(document_id):
                continue

            cand_dept = cand.get("department", "General")
            title = cand.get("title", "Untitled Document")
            popularity = float(cand.get("views_count", 10)) / 100.0

            # Boost cross-department matching slightly for discovery
            relevance = 0.75
            if cand_dept == department:
                relevance = 0.90
                reason = f"Highly relevant canonical documentation from {department}"
            else:
                reason = f"Cross-functional reference asset shared by {cand_dept}"

            recommendations.append(KnowledgeRecommendationItem(
                document_id=cand_id,
                title=title,
                department=cand_dept,
                popularity_score=min(popularity, 1.0),
                relevance_score=relevance,
                reason=reason,
            ))

        # Sort by relevance then popularity
        recommendations.sort(key=lambda x: (x.relevance_score, x.popularity_score), reverse=True)
        return recommendations[:5]

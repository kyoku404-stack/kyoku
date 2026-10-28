"""Unit tests for Phase 3.2 Real-Time Collaboration & Knowledge Sharing contracts.

Owner: Member 1 (Project Lead & AI Architect)
Domain: /backend/app/services/collaboration
"""

from datetime import UTC, datetime

from backend.app.services.collaboration.contracts import (
    ActivityType,
    ApprovalStatus,
    CommentStatus,
    DefaultActionItemExtractor,
    DefaultDiscussionSummarizer,
    DefaultKnowledgeSharingRecommender,
    DefaultMentionParser,
    DiscussionSummaryResult,
    PresenceStatus,
    WorkspaceRole,
)


class TestCollaborationContracts:
    """Validate enums, dataclasses, and AI engines for collaboration."""

    def test_enums_integrity(self):
        """Ensure all required roles and states exist."""
        assert WorkspaceRole.ADMIN.value == "ADMIN"
        assert WorkspaceRole.MEMBER.value == "MEMBER"
        assert WorkspaceRole.VIEWER.value == "VIEWER"
        assert WorkspaceRole.GUEST.value == "GUEST"

        assert PresenceStatus.ONLINE.value == "ONLINE"
        assert PresenceStatus.AWAY.value == "AWAY"
        assert PresenceStatus.EDITING.value == "EDITING"

        assert CommentStatus.OPEN.value == "OPEN"
        assert CommentStatus.RESOLVED.value == "RESOLVED"
        assert CommentStatus.ARCHIVED.value == "ARCHIVED"

        assert ActivityType.DOCUMENT_UPLOAD.value == "DOCUMENT_UPLOAD"
        assert ActivityType.COMMENT_ADDED.value == "COMMENT_ADDED"
        assert ActivityType.USER_MENTION.value == "USER_MENTION"
        assert ActivityType.AI_SUMMARY_GENERATED.value == "AI_SUMMARY_GENERATED"

        assert ApprovalStatus.APPROVED.value == "APPROVED"
        assert ApprovalStatus.PENDING_REVIEW.value == "PENDING_REVIEW"

    def test_mention_parser_extraction(self):
        """Verify regex mention parser extracts usernames properly."""
        parser = DefaultMentionParser()

        text = "Hello @alice and @bob.smith! Can you ask @carol_12 to review this?"
        mentions = parser.extract_mentions(text)
        assert mentions == ["alice", "bob.smith", "carol_12"]

        # Duplicate mention handling
        dup_text = "@alice please check with @alice"
        assert parser.extract_mentions(dup_text) == ["alice"]

        # Empty string handling
        assert parser.extract_mentions("") == []

    def test_action_item_extractor(self):
        """Verify extraction of action items and deadline detection."""
        extractor = DefaultActionItemExtractor()

        comments = [
            {
                "author_name": "Alice",
                "content": "@bob please review the security policy by Friday.",
                "created_at": datetime.now(UTC).isoformat(),
            },
            {
                "author_name": "Charlie",
                "content": "Just a general comment about formatting.",
                "created_at": datetime.now(UTC).isoformat(),
            },
            {
                "author_name": "Dave",
                "content": "I will update the diagrams by tomorrow afternoon.",
                "created_at": datetime.now(UTC).isoformat(),
            },
        ]

        items = extractor.extract_action_items(comments)
        assert len(items) == 2

        assert items[0].assignee == "bob"
        assert items[0].deadline == "Friday"
        assert "please review" in items[0].action

        assert items[1].assignee == "Dave"
        assert items[1].deadline == "Tomorrow afternoon"

    def test_discussion_summarizer_empty(self):
        """Verify summarizer handles empty comment threads gracefully."""
        summarizer = DefaultDiscussionSummarizer()
        result = summarizer.summarize("doc-1", "Security Architecture", [])

        assert isinstance(result, DiscussionSummaryResult)
        assert "No discussion activity recorded" in result.executive_summary
        assert result.key_decisions == []
        assert result.action_items == []

    def test_discussion_summarizer_with_thread(self):
        """Verify full thread summarization with decisions and action items."""
        summarizer = DefaultDiscussionSummarizer()

        comments = [
            {
                "author_name": "Alice",
                "content": "Should we increase retention from 30 to 90 days?",
                "status": "OPEN",
                "created_at": "2026-10-28T10:00:00Z",
            },
            {
                "author_name": "Bob",
                "content": "@alice We confirmed and approved 90 days retention for enterprise tier.",
                "status": "OPEN",
                "created_at": "2026-10-28T10:05:00Z",
            },
            {
                "author_name": "Alice",
                "content": "Great, I will update the documentation by Thursday.",
                "status": "OPEN",
                "created_at": "2026-10-28T10:10:00Z",
            },
        ]

        result = summarizer.summarize("doc-123", "Data Retention Policy", comments)
        assert "Security" not in result.executive_summary
        assert "Data Retention Policy" in result.executive_summary
        assert len(result.key_decisions) >= 1
        assert "approved" in result.key_decisions[0].decision
        assert len(result.action_items) >= 1
        assert result.action_items[0].deadline == "Thursday"
        assert result.processing_time_ms > 0

    def test_knowledge_sharing_recommender(self):
        """Verify cross-department knowledge recommendations."""
        recommender = DefaultKnowledgeSharingRecommender()

        candidates = [
            {"id": "doc-1", "title": "Self doc", "department": "Engineering", "views_count": 50},
            {"id": "doc-2", "title": "API RFC", "department": "Engineering", "views_count": 80},
            {"id": "doc-3", "title": "Company Handbook", "department": "HR", "views_count": 95},
        ]

        recs = recommender.recommend_related("doc-1", "Engineering", candidates)
        # Should exclude self doc-1
        assert all(r.document_id != "doc-1" for r in recs)
        assert len(recs) == 2
        # doc-2 should have higher relevance due to matching department
        assert recs[0].document_id == "doc-2"
        assert recs[0].relevance_score > recs[1].relevance_score

"""Phase 4.1 Member 2 — Agent Contracts, Communication Envelopes & Errors Unit Tests.

Verifies:
- AgentRequest, AgentContext, EvidenceReference, AgentResult schema validation & JSON round-trip.
- Contract schema versioning enforcement (accepts 1.0, rejects unsupported versions).
- Secret/token redaction in AgentErrorDetail and AgentLayerError messages.
- Status consistency checks on succeeded vs failed AgentResult.
- Inter-agent AgentMessageEnvelope creation, validation, serialization, and reply lineage.

Specification: devdocs/p4/p4.1.txt (Sections 3, 4.3, 9)
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.app.agents.contracts import (
    AGENT_CONTRACT_SCHEMA_VERSION,
    EXAMPLE_AGENT_REQUEST,
    EXAMPLE_AGENT_RESULT,
    AgentContext,
    AgentRequest,
    AgentResult,
    EvidenceReference,
)
from backend.app.agents.errors import (
    AgentErrorCode,
    AgentErrorDetail,
    AgentLayerError,
    sanitize_error_message,
)
from backend.app.agents.messages import (
    AgentHandoffPayload,
    AgentMessageEnvelope,
    AgentParticipant,
    MessagePriority,
    MessageType,
)


class TestAgentContracts:
    def test_example_payloads_validate_and_round_trip(self) -> None:
        req = AgentRequest.model_validate(EXAMPLE_AGENT_REQUEST)
        assert req.schema_version == AGENT_CONTRACT_SCHEMA_VERSION
        req_json = req.model_dump_json()
        assert AgentRequest.model_validate_json(req_json) == req

        res = AgentResult.model_validate(EXAMPLE_AGENT_RESULT)
        assert res.status == "succeeded"
        assert len(res.evidence) == 1
        assert res.evidence[0].source_id == "doc_phase4_arch"
        res_json = res.model_dump_json()
        assert AgentResult.model_validate_json(res_json) == res

    def test_unsupported_schema_version_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Unsupported agent contract schema_version"):
            AgentRequest(
                request_id="req-1",
                task_id="task-1",
                goal="Test",
                schema_version="2.0",
            )

        with pytest.raises(ValidationError, match="Unsupported agent contract schema_version"):
            AgentResult(status="succeeded", schema_version="9.9")

    def test_blank_goal_or_identifiers_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AgentRequest(request_id="req-1", task_id="task-1", goal="   ")

        with pytest.raises(ValidationError):
            AgentContext(user_id="  ", tenant_id="org-1", correlation_id="corr-1")

    def test_succeeded_result_cannot_carry_error_code(self) -> None:
        with pytest.raises(ValidationError, match="must not include error_code"):
            AgentResult(status="succeeded", error_code="AGENT_EXECUTION_FAILED")

    def test_failed_result_factory_populates_sanitized_error(self) -> None:
        res = AgentResult.failure(
            code=AgentErrorCode.AGENT_EXECUTION_FAILED,
            message="Upstream failure using Bearer supersecrettoken12345 and sk-abcdefghijklmnopqrstuv",
            warnings=["Retry advised"],
            retryable=True,
        )
        assert res.status == "failed"
        assert res.error_code == AgentErrorCode.AGENT_EXECUTION_FAILED.value
        assert res.error is not None
        assert "supersecrettoken12345" not in (res.error_message or "")
        assert "sk-abcdefghijklmnopqrstuv" not in res.error.message
        assert "[REDACTED]" in res.error.message
        assert res.error.retryable is True

    def test_evidence_reference_score_bounds(self) -> None:
        ev = EvidenceReference(source_id="chunk-42", source_type="chunk", score=0.88, chunk_index=3)
        assert ev.score == 0.88

        with pytest.raises(ValidationError):
            EvidenceReference(source_id="chunk-42", score=1.5)


class TestAgentErrorsAndSanitization:
    def test_sanitize_error_message_redacts_secrets_and_truncates(self) -> None:
        jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abcDEF1234567890"
        raw = f"Auth failed for token={jwt} password=my_secret_pw"
        cleaned = sanitize_error_message(raw)
        assert jwt not in cleaned
        assert "my_secret_pw" not in cleaned
        assert "[REDACTED]" in cleaned

        long_msg = "x" * 1000
        assert len(sanitize_error_message(long_msg)) <= 512

    def test_agent_layer_error_converts_to_detail(self) -> None:
        err = AgentLayerError(
            "Database failed with api_key=secret_key_999",
            code=AgentErrorCode.AGENT_EXECUTION_FAILED,
            http_status=500,
            retryable=True,
        )
        detail = err.to_error_detail()
        assert isinstance(detail, AgentErrorDetail)
        assert "secret_key_999" not in detail.message
        assert detail.code == AgentErrorCode.AGENT_EXECUTION_FAILED


class TestAgentMessageEnvelopes:
    def test_message_envelope_serialization_and_reply_lineage(self) -> None:
        handoff = AgentHandoffPayload(
            summary="Extracted 4 policy clauses.",
            artifacts={"clause_count": 4},
            next_goal="Validate compliance alignment.",
            required_capabilities=["compliance.check"],
        )
        envelope = AgentMessageEnvelope(
            correlation_id="corr-xyz-001",
            task_id="task-xyz-001",
            tenant_id="org-acme",
            sender=AgentParticipant(agent_id="Research", role="researcher", version="1.0.0"),
            recipient=AgentParticipant(agent_id="Compliance", role="reviewer", version="1.0.0"),
            message_type=MessageType.HANDOFF,
            priority=MessagePriority.HIGH,
            payload=handoff.model_dump(),
            evidence=[EvidenceReference(source_id="doc-1", title="Policy PDF")],
        )

        assert envelope.sender.agent_id == "research"
        assert envelope.recipient.agent_id == "compliance"
        assert envelope.message_id.startswith("msg_")

        # Round-trip JSON serialization
        raw_json = envelope.model_dump_json()
        restored = AgentMessageEnvelope.model_validate_json(raw_json)
        assert restored.message_id == envelope.message_id
        assert restored.correlation_id == "corr-xyz-001"
        assert restored.tenant_id == "org-acme"

        # Reply preserves lineage and swaps sender/recipient
        reply = envelope.create_reply(
            message_type=MessageType.TASK_RESPONSE,
            payload={"compliant": True},
        )
        assert reply.causation_id == envelope.message_id
        assert reply.correlation_id == envelope.correlation_id
        assert reply.task_id == envelope.task_id
        assert reply.tenant_id == envelope.tenant_id
        assert reply.sender.agent_id == "compliance"
        assert reply.recipient.agent_id == "research"

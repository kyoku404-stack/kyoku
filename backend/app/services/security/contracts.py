"""Typed AI and Domain Contracts for Enterprise Security, Compliance, Governance & Data Protection.

Phase: 3.3
Owner: Member 1 (Project Lead & AI Architect)
Domain: /backend/app/services/security/
Specification: devdocs/p3/p3.3.txt (Chapters 1-20)
"""

import base64
import binascii
import hashlib
import hmac
import re
import secrets
import struct
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, ClassVar


class ClassificationLevel(str, Enum):
    """Enterprise document data sensitivity tiers."""

    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


class AuditStatus(str, Enum):
    """Status outcomes for immutable enterprise audit logging."""

    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    DENIED = "DENIED"


class ComplianceStandard(str, Enum):
    """Supported regulatory and compliance governance standards."""

    GDPR = "GDPR"
    ISO_27001 = "ISO_27001"
    SOC_2 = "SOC_2"
    HIPAA = "HIPAA"


class ComplianceStatus(str, Enum):
    """Compliance control evaluation states."""

    COMPLIANT = "COMPLIANT"
    PARTIAL = "PARTIAL"
    NON_COMPLIANT = "NON_COMPLIANT"


class AlertSeverity(str, Enum):
    """Severity ratings for security threat monitoring."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SecurityAlertType(str, Enum):
    """Categorization of security alerts and anomalies."""

    FAILED_LOGIN_SPIKE = "FAILED_LOGIN_SPIKE"
    PROMPT_INJECTION_ATTEMPT = "PROMPT_INJECTION_ATTEMPT"
    SUSPICIOUS_EXPORT = "SUSPICIOUS_EXPORT"
    BRUTE_FORCE = "BRUTE_FORCE"
    PRIVILEGE_ESCALATION = "PRIVILEGE_ESCALATION"


class PIIEntityType(str, Enum):
    """Categories of detected personally identifiable or confidential entities."""

    EMAIL = "EMAIL"
    PHONE = "PHONE"
    SSN = "SSN"
    CREDIT_CARD = "CREDIT_CARD"
    API_KEY = "API_KEY"
    CONFIDENTIAL_CODENAME = "CONFIDENTIAL_CODENAME"


class GuardrailStatus(str, Enum):
    """AI safety guardrail verification status."""

    PASSED = "PASSED"
    FLAGGED = "FLAGGED"
    BLOCKED = "BLOCKED"


@dataclass
class DetectedPIIEntity:
    """An individual sensitive entity detected during a scan."""

    entity_type: PIIEntityType
    count: int
    masked_sample: str
    confidence: float = 1.0


@dataclass
class ClassificationResult:
    """Classification analysis for an enterprise document or text payload."""

    document_id: str | None
    classification_level: ClassificationLevel
    detected_entities: list[DetectedPIIEntity] = field(default_factory=list)
    pii_count: int = 0
    confidence_score: float = 1.0
    redacted_preview: str = ""
    scanned_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class TOTPSetupData:
    """Secret configuration and recovery backup codes for Multi-Factor Authentication."""

    secret_key: str
    otpauth_uri: str
    backup_codes: list[str] = field(default_factory=list)


@dataclass
class AIGovernanceRecord:
    """Audit and safety telemetry for an AI model interaction."""

    prompt_snippet: str
    model_name: str
    guardrail_status: GuardrailStatus
    guardrail_flags: list[str] = field(default_factory=list)
    token_usage: int = 0
    latency_ms: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ComplianceControlResult:
    """Evaluation result for an individual regulatory compliance standard."""

    standard: ComplianceStandard
    score: int
    status: ComplianceStatus
    controls_passed: int
    controls_total: int
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ComplianceOverview:
    """Executive compliance posture covering all regulatory frameworks."""

    overall_score: int
    standards: list[ComplianceControlResult] = field(default_factory=list)
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


# ==============================================================================
# Abstract Engine Interfaces & Reference Implementations
# ==============================================================================


class BaseTOTPEngine(ABC):
    """Abstract interface for RFC 6238 Time-based One-Time Password generation and verification."""

    @abstractmethod
    def generate_secret(self) -> str:
        """Generates a Base32-encoded random shared secret."""
        ...

    @abstractmethod
    def generate_otpauth_uri(self, secret: str, email: str, issuer: str = "KEEP") -> str:
        """Generates an RFC-compliant otpauth:// URI for authenticator apps."""
        ...

    @abstractmethod
    def generate_backup_codes(self, count: int = 4) -> list[str]:
        """Generates single-use backup recovery codes."""
        ...

    @abstractmethod
    def verify_code(self, secret: str, code: str, window: int = 1) -> bool:
        """Verifies a 6-digit TOTP passcode within time-step drift tolerance."""
        ...

    @abstractmethod
    def generate_code(self, secret: str, timestamp: int | None = None) -> str:
        """Generates a 6-digit TOTP passcode for the current or specified timestamp."""
        ...


class RFC6238TOTPEngine(BaseTOTPEngine):
    """Standard RFC 6238 TOTP Engine implementation using HMAC-SHA1."""

    TIME_STEP: int = 30
    DIGITS: int = 6

    def generate_secret(self) -> str:
        random_bytes = secrets.token_bytes(20)
        return base64.b32encode(random_bytes).decode("utf-8").replace("=", "")

    def generate_otpauth_uri(self, secret: str, email: str, issuer: str = "KEEP") -> str:
        clean_email = email.strip()
        return f"otpauth://totp/{issuer}:{clean_email}?secret={secret}&issuer={issuer}&algorithm=SHA1&digits=6&period=30"

    def generate_backup_codes(self, count: int = 4) -> list[str]:
        return [secrets.token_hex(4).upper() for _ in range(count)]

    def _compute_totp(self, key_bytes: bytes, time_counter: int) -> str:
        msg = struct.pack(">Q", time_counter)
        h = hmac.new(key_bytes, msg, hashlib.sha1).digest()
        offset = h[-1] & 0x0F
        truncated_hash = struct.unpack(">I", h[offset : offset + 4])[0] & 0x7FFFFFFF
        code = str(truncated_hash % (10**self.DIGITS)).zfill(self.DIGITS)
        return code

    def generate_code(self, secret: str, timestamp: int | None = None) -> str:
        padding = "=" * ((8 - len(secret) % 8) % 8)
        key_bytes = base64.b32decode(secret.upper() + padding)
        t = timestamp if timestamp is not None else int(time.time())
        counter = t // self.TIME_STEP
        return self._compute_totp(key_bytes, counter)

    def verify_code(self, secret: str, code: str, window: int = 1) -> bool:
        if not secret or not code:
            return False
        clean_code = code.strip().replace(" ", "")
        if len(clean_code) != self.DIGITS or not clean_code.isdigit():
            return False

        try:
            # Add padding if missing
            padding = "=" * ((8 - len(secret) % 8) % 8)
            key_bytes = base64.b32decode(secret.upper() + padding)
        except (binascii.Error, ValueError, TypeError):
            return False

        current_time = int(time.time())
        current_counter = current_time // self.TIME_STEP

        for offset in range(-window, window + 1):
            expected = self._compute_totp(key_bytes, current_counter + offset)
            if hmac.compare_digest(expected, clean_code):
                return True
        return False


class BasePIIScanner(ABC):
    """Abstract interface for scanning content and classifying data sensitivity."""

    @abstractmethod
    def scan_content(self, content: str, document_id: str | None = None) -> ClassificationResult:
        """Scans text for sensitive entities, returns classification tier and redacted preview."""
        ...


class DefaultDeterministicPIIScanner(BasePIIScanner):
    """Deterministic regex and heuristic PII / Secret scanner."""

    EMAIL_PATTERN: ClassVar[re.Pattern] = re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    )
    PHONE_PATTERN: ClassVar[re.Pattern] = re.compile(
        r"(?<![a-zA-Z0-9_-])(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
    )
    SSN_PATTERN: ClassVar[re.Pattern] = re.compile(
        r"\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b"
    )
    CREDIT_CARD_PATTERN: ClassVar[re.Pattern] = re.compile(
        r"\b(?:\d{4}[-\s]?){3}\d{4}\b"
    )
    API_KEY_PATTERN: ClassVar[re.Pattern] = re.compile(
        r"\b(?:sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{20,}|AKIA[0-9A-Z]{16}|(?:ak|sk|pk)_(?:live|test)_[a-zA-Z0-9]{16,})\b"
    )
    CODENAME_PATTERN: ClassVar[re.Pattern] = re.compile(
        r"\bProject\s+[A-Z][a-zA-Z0-9_-]{2,}\b"
    )

    def _luhn_check(self, card_str: str) -> bool:
        digits = [int(c) for c in card_str if c.isdigit()]
        if len(digits) != 16:
            return False
        total = 0
        for i, val in enumerate(reversed(digits)):
            if i % 2 == 1:
                doubled = val * 2
                total += doubled - 9 if doubled > 9 else doubled
            else:
                total += val
        return total % 10 == 0

    def scan_content(self, content: str, document_id: str | None = None) -> ClassificationResult:
        if not content:
            return ClassificationResult(
                document_id=document_id,
                classification_level=ClassificationLevel.PUBLIC,
                detected_entities=[],
                pii_count=0,
                confidence_score=1.0,
                redacted_preview="",
            )

        entities: list[DetectedPIIEntity] = []
        redacted = content

        # API Keys & Secrets first
        api_keys = self.API_KEY_PATTERN.findall(content)
        if api_keys:
            sample = api_keys[0]
            masked = sample[:4] + "***"
            entities.append(DetectedPIIEntity(PIIEntityType.API_KEY, len(api_keys), masked))
            redacted = self.API_KEY_PATTERN.sub("[REDACTED_API_KEY]", redacted)

        # Confidential Project Codenames
        codenames = self.CODENAME_PATTERN.findall(content)
        if codenames:
            sample = codenames[0]
            entities.append(DetectedPIIEntity(PIIEntityType.CONFIDENTIAL_CODENAME, len(codenames), sample))
            redacted = self.CODENAME_PATTERN.sub("[REDACTED_CODENAME]", redacted)

        # Credit Cards
        raw_cards = self.CREDIT_CARD_PATTERN.findall(content)
        valid_cards = [c for c in raw_cards if self._luhn_check(c)]
        if valid_cards:
            sample = valid_cards[0].replace("-", "").replace(" ", "")
            masked = "****-****-****-" + sample[-4:]
            entities.append(DetectedPIIEntity(PIIEntityType.CREDIT_CARD, len(valid_cards), masked))
            for c in valid_cards:
                redacted = redacted.replace(c, "[REDACTED_CREDIT_CARD]")

        # SSN
        ssns = self.SSN_PATTERN.findall(content)
        if ssns:
            sample = ssns[0]
            masked = "***-**-" + sample[-4:]
            entities.append(DetectedPIIEntity(PIIEntityType.SSN, len(ssns), masked))
            redacted = self.SSN_PATTERN.sub("[REDACTED_SSN]", redacted)

        # Emails
        emails = self.EMAIL_PATTERN.findall(content)
        if emails:
            sample = emails[0]
            masked = sample[0] + "***" + sample[sample.find("@") - 1 :] if len(sample) > 3 else "***"
            entities.append(DetectedPIIEntity(PIIEntityType.EMAIL, len(emails), masked))
            redacted = self.EMAIL_PATTERN.sub("[REDACTED_EMAIL]", redacted)

        # Phone numbers
        phones = self.PHONE_PATTERN.findall(content)
        if phones:
            sample = phones[0]
            masked = "***-***-" + sample[-4:] if len(sample) >= 4 else "***"
            entities.append(DetectedPIIEntity(PIIEntityType.PHONE, len(phones), masked))
            redacted = self.PHONE_PATTERN.sub("[REDACTED_PHONE]", redacted)

        # Confidential Project Codenames
        codenames = self.CODENAME_PATTERN.findall(content)
        if codenames:
            sample = codenames[0]
            entities.append(DetectedPIIEntity(PIIEntityType.CONFIDENTIAL_CODENAME, len(codenames), sample))
            redacted = self.CODENAME_PATTERN.sub("[REDACTED_CODENAME]", redacted)

        total_pii = sum(e.count for e in entities)

        # Classification level determination
        has_critical = any(
            e.entity_type in (PIIEntityType.SSN, PIIEntityType.CREDIT_CARD, PIIEntityType.API_KEY)
            for e in entities
        )
        has_internal = any(
            e.entity_type in (PIIEntityType.EMAIL, PIIEntityType.PHONE, PIIEntityType.CONFIDENTIAL_CODENAME)
            for e in entities
        )

        if has_critical or total_pii >= 5:
            level = ClassificationLevel.RESTRICTED
        elif has_internal or total_pii > 0:
            level = ClassificationLevel.CONFIDENTIAL
        elif len(content.strip()) > 100:
            level = ClassificationLevel.INTERNAL
        else:
            level = ClassificationLevel.PUBLIC

        return ClassificationResult(
            document_id=document_id,
            classification_level=level,
            detected_entities=entities,
            pii_count=total_pii,
            confidence_score=0.98 if total_pii > 0 else 1.0,
            redacted_preview=redacted[:500],
        )


class BaseAIGuardrailEngine(ABC):
    """Abstract interface for inspecting AI prompts and outputs for safety."""

    @abstractmethod
    def evaluate_prompt(self, prompt: str) -> tuple[GuardrailStatus, list[str]]:
        """Inspects prompt for injection, jailbreak, or system override attempts."""
        ...


class DefaultAIGuardrailEngine(BaseAIGuardrailEngine):
    """Rule-based AI safety and prompt injection guardrail engine."""

    INJECTION_SIGNATURES: ClassVar[list[tuple[str, re.Pattern]]] = [
        ("INSTRUCTION_OVERRIDE", re.compile(r"(?:ignore|disregard|forget)\s+(?:all\s+)?(?:previous|prior)\s+(?:instructions|rules|prompts)", re.IGNORECASE)),
        ("SYSTEM_PROMPT_LEAK", re.compile(r"(?:reveal|print|leak|show|output)\s+(?:the\s+)?system\s+(?:prompt|instructions)", re.IGNORECASE)),
        ("JAILBREAK_ROLEPLAY", re.compile(r"\b(?:DAN|Do\s+Anything\s+Now|jailbreak|jailbroken)\b", re.IGNORECASE)),
        ("PRIVILEGE_BYPASS", re.compile(r"bypass\s+(?:security|safety|filter|rbac)", re.IGNORECASE)),
        ("DELIMITER_ESCAPE", re.compile(r"(?:###|```)\s*(?:system|override)", re.IGNORECASE)),
    ]

    def evaluate_prompt(self, prompt: str) -> tuple[GuardrailStatus, list[str]]:
        if not prompt:
            return GuardrailStatus.PASSED, []

        flags: list[str] = []
        for name, pattern in self.INJECTION_SIGNATURES:
            if pattern.search(prompt):
                flags.append(name)

        if flags:
            return GuardrailStatus.BLOCKED, flags
        return GuardrailStatus.PASSED, []


class BaseComplianceEvaluator(ABC):
    """Abstract interface for scoring enterprise regulatory compliance."""

    @abstractmethod
    def evaluate_organization_compliance(
        self, organization_id: str, context: dict[str, Any] | None = None
    ) -> ComplianceOverview:
        """Evaluates readiness and control compliance across GDPR, ISO 27001, SOC 2, HIPAA."""
        ...


class DefaultComplianceEvaluator(BaseComplianceEvaluator):
    """Deterministic compliance evaluation engine based on enterprise control checks."""

    def evaluate_organization_compliance(
        self, organization_id: str, context: dict[str, Any] | None = None
    ) -> ComplianceOverview:
        ctx = context or {}
        has_mfa = ctx.get("has_mfa", True)
        has_audit_logs = ctx.get("has_audit_logs", True)
        has_encryption = ctx.get("has_encryption", True)
        has_retention_rules = ctx.get("has_retention_rules", True)

        # GDPR Evaluation
        gdpr_passed = 10
        if has_retention_rules:
            gdpr_passed += 1
        if has_audit_logs:
            gdpr_passed += 1
        gdpr_total = 12
        gdpr_score = int((gdpr_passed / gdpr_total) * 100)
        gdpr_result = ComplianceControlResult(
            standard=ComplianceStandard.GDPR,
            score=gdpr_score,
            status=ComplianceStatus.COMPLIANT if gdpr_score >= 90 else ComplianceStatus.PARTIAL,
            controls_passed=gdpr_passed,
            controls_total=gdpr_total,
            details={"right_to_erasure": True, "retention_policies": has_retention_rules},
        )

        # ISO 27001 Evaluation
        iso_passed = 17
        if has_mfa:
            iso_passed += 1
        if has_encryption:
            iso_passed += 2
        iso_total = 20
        iso_score = int((iso_passed / iso_total) * 100)
        iso_result = ComplianceControlResult(
            standard=ComplianceStandard.ISO_27001,
            score=iso_score,
            status=ComplianceStatus.COMPLIANT if iso_score >= 90 else ComplianceStatus.PARTIAL,
            controls_passed=iso_passed,
            controls_total=iso_total,
            details={"cryptography": has_encryption, "access_control": has_mfa},
        )

        # SOC 2 Evaluation
        soc_passed = 14
        if has_mfa:
            soc_passed += 1
        if has_audit_logs:
            soc_passed += 1
        soc_total = 16
        soc_score = int((soc_passed / soc_total) * 100)
        soc_result = ComplianceControlResult(
            standard=ComplianceStandard.SOC_2,
            score=soc_score,
            status=ComplianceStatus.COMPLIANT if soc_score >= 90 else ComplianceStatus.PARTIAL,
            controls_passed=soc_passed,
            controls_total=soc_total,
            details={"trust_criteria": ["Security", "Confidentiality"], "audit_readiness": True},
        )

        # HIPAA Evaluation
        hipaa_passed = 13
        if has_encryption:
            hipaa_passed += 1
        if has_audit_logs:
            hipaa_passed += 1
        hipaa_total = 15
        hipaa_score = int((hipaa_passed / hipaa_total) * 100)
        hipaa_result = ComplianceControlResult(
            standard=ComplianceStandard.HIPAA,
            score=hipaa_score,
            status=ComplianceStatus.COMPLIANT if hipaa_score >= 90 else ComplianceStatus.PARTIAL,
            controls_passed=hipaa_passed,
            controls_total=hipaa_total,
            details={"safeguards_phi": True, "emergency_access": True},
        )

        standards = [gdpr_result, iso_result, soc_result, hipaa_result]
        overall = int(sum(s.score for s in standards) / len(standards))

        return ComplianceOverview(
            overall_score=overall,
            standards=standards,
        )

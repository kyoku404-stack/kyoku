"""KEEP Enterprise Platform — Enterprise Integrations & Connector Framework Domain Contracts.

Specification: devdocs/p3/p3.1.txt & docs/Architecture/enterprise-integrations-connector-framework.md
Author: Member 1 (Project Lead & AI Architect)
"""

import hashlib
import html
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

# ==============================================================================
# Enumerations
# ==============================================================================

class PlatformType(str, Enum):
    """Supported external enterprise platforms."""
    GOOGLE_DRIVE = "GOOGLE_DRIVE"
    ONEDRIVE = "ONEDRIVE"
    SHAREPOINT = "SHAREPOINT"
    DROPBOX = "DROPBOX"
    S3 = "S3"
    CONFLUENCE = "CONFLUENCE"
    NOTION = "NOTION"
    SLACK = "SLACK"
    TEAMS = "TEAMS"
    GITHUB = "GITHUB"
    GITLAB = "GITLAB"
    JIRA = "JIRA"
    SALESFORCE = "SALESFORCE"
    HUBSPOT = "HUBSPOT"


class PlatformCategory(str, Enum):
    """Categorical taxonomy for enterprise integrations."""
    CLOUD_STORAGE = "CLOUD_STORAGE"
    DOCUMENTATION = "DOCUMENTATION"
    COMMUNICATION = "COMMUNICATION"
    DEVELOPMENT = "DEVELOPMENT"
    PROJECT_MANAGEMENT = "PROJECT_MANAGEMENT"
    CRM = "CRM"


class AuthType(str, Enum):
    """Authentication and credential protocols."""
    OAUTH2 = "OAUTH2"
    OPENID_CONNECT = "OPENID_CONNECT"
    PERSONAL_ACCESS_TOKEN = "PERSONAL_ACCESS_TOKEN"
    API_KEY = "API_KEY"
    SERVICE_ACCOUNT = "SERVICE_ACCOUNT"


class ConnectorStatus(str, Enum):
    """Deterministic lifecycle states for connector instances."""
    CONFIGURED = "CONFIGURED"
    AUTHENTICATING = "AUTHENTICATING"
    CONNECTED = "CONNECTED"
    SYNCING = "SYNCING"
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"
    DISCONNECTED = "DISCONNECTED"


class SyncMode(str, Enum):
    """Synchronization modes for ingestion."""
    FULL = "FULL"
    INCREMENTAL = "INCREMENTAL"
    SCHEDULED = "SCHEDULED"
    REAL_TIME = "REAL_TIME"


class SyncJobStatus(str, Enum):
    """Lifecycle states for synchronization batches."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class SyncAction(str, Enum):
    """Action taken on a single synchronized resource."""
    ADDED = "ADDED"
    UPDATED = "UPDATED"
    DELETED = "DELETED"
    SKIPPED = "SKIPPED"
    FAILED = "FAILED"


class NormalizedPermissionLevel(str, Enum):
    """Standardized access control levels mapped to KEEP RBAC."""
    PUBLIC = "PUBLIC"
    VIEWER = "VIEWER"
    READ = "READ"
    EDITOR = "EDITOR"
    WRITE = "WRITE"
    ADMIN = "ADMIN"
    OWNER = "OWNER"


# ==============================================================================
# Domain Dataclasses
# ==============================================================================

@dataclass
class AuthCredentials:
    """Encrypted credential envelope for authenticating connectors."""
    auth_type: AuthType
    access_token: str | None = None
    refresh_token: str | None = None
    api_key: str | None = None
    service_account_key: str | None = None
    expires_in: int | None = 3600
    token_type: str = "Bearer"
    authenticated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    extra_params: dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Determines if the token has expired based on expires_in."""
        if not self.expires_in:
            return False
        expiry_time = self.authenticated_at + timedelta(seconds=self.expires_in)
        return datetime.now(UTC) >= expiry_time


@dataclass
class ConnectorConfig:
    """Configuration settings for a registered connector."""
    sync_interval_minutes: int = 60
    sync_folders: list[str] = field(default_factory=lambda: ["root"])
    file_extensions: list[str] = field(default_factory=lambda: [".pdf", ".docx", ".md", ".txt"])
    rate_limit_per_minute: int = 120
    max_batch_size: int = 100
    custom_settings: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExternalResourceItem:
    """Raw resource fetched from an external SaaS platform."""
    external_id: str
    name: str
    mime_type: str = "text/plain"
    content_bytes: bytes | None = None
    content_text: str | None = None
    source_url: str | None = None
    author: str | None = None
    department: str | None = None
    created_at: datetime | None = None
    modified_at: datetime | None = None
    version: str | None = "1"
    raw_metadata: dict[str, Any] = field(default_factory=dict)
    external_permissions: list[str] = field(default_factory=lambda: ["reader"])


@dataclass
class NormalizedDocument:
    """Unified KEEP document format produced by the data transformation layer."""
    external_id: str
    source_platform: PlatformType
    platform_category: PlatformCategory
    source_url: str
    title: str
    raw_content: str
    mime_type: str
    author: str
    department: str | None = None
    tags: list[str] = field(default_factory=list)
    external_created_at: datetime | None = None
    external_modified_at: datetime | None = None
    permission_level: NormalizedPermissionLevel = NormalizedPermissionLevel.READ
    allowed_roles: list[str] = field(default_factory=lambda: ["OrgAdmin", "Manager", "Member"])
    checksum: str = ""
    version: str = "1"
    metadata_json: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChangeDetectionItem:
    """Individual delta assessment for an external resource."""
    external_id: str
    action: SyncAction
    reason: str
    checksum: str
    modified_at: datetime | None = None


@dataclass
class ChangeDetectionResult:
    """Summary of incremental change detection analysis."""
    total_detected: int
    items: list[ChangeDetectionItem]
    added_count: int
    updated_count: int
    deleted_count: int
    unchanged_count: int


@dataclass
class SyncMetrics:
    """Throughput and performance counters for synchronization runs."""
    discovered: int = 0
    added: int = 0
    updated: int = 0
    deleted: int = 0
    skipped: int = 0
    failed: int = 0
    duration_ms: int = 0
    api_latency_ms: float = 0.0


# ==============================================================================
# Abstract Base Classes (Contracts)
# ==============================================================================

class BaseConnectorAdapter(ABC):
    """Abstract connector adapter contract isolating external vendor SDKs."""

    @abstractmethod
    def connect(self, credentials: AuthCredentials) -> bool:
        """Establish connection with credentials."""

    @abstractmethod
    def authenticate(self, credentials: AuthCredentials) -> dict[str, Any]:
        """Perform authentication / OAuth token validation."""

    @abstractmethod
    def test_connection(self) -> bool:
        """Verify API health and accessibility."""

    @abstractmethod
    def discover_resources(self, since: datetime | None = None) -> list[ExternalResourceItem]:
        """Query platform for accessible resources, optionally filtered since last sync."""

    @abstractmethod
    def fetch_resource_content(self, external_id: str) -> ExternalResourceItem:
        """Retrieve full text/binary payload for a specific external resource."""

    @abstractmethod
    def disconnect(self) -> None:
        """Gracefully release client sessions and tokens."""


class BaseDocumentNormalizer(ABC):
    """Abstract data transformation contract standardizing diverse SaaS payloads."""

    @abstractmethod
    def normalize(
        self,
        item: ExternalResourceItem,
        platform: PlatformType,
        category: PlatformCategory,
    ) -> NormalizedDocument:
        """Convert raw external resource into canonical NormalizedDocument."""

    @abstractmethod
    def map_permissions(
        self,
        raw_permissions: list[str],
    ) -> tuple[NormalizedPermissionLevel, list[str]]:
        """Map platform-specific permissions to NormalizedPermissionLevel and KEEP RBAC roles."""


class BaseChangeDetector(ABC):
    """Abstract delta calculation engine for incremental synchronization."""

    @abstractmethod
    def compute_checksum(self, content: str, mime_type: str = "") -> str:
        """Calculate cryptographic SHA-256 fingerprint of resource."""

    @abstractmethod
    def detect_changes(
        self,
        external_items: list[ExternalResourceItem],
        known_checksums: dict[str, str],
    ) -> ChangeDetectionResult:
        """Determine resources that are NEW, UPDATED, DELETED, or UNCHANGED."""


class BaseSyncScheduler(ABC):
    """Abstract scheduling orchestrator for automated connector runs."""

    @abstractmethod
    def calculate_next_sync(self, last_sync_at: datetime, interval_minutes: int) -> datetime:
        """Compute the next scheduled run timestamp."""

    @abstractmethod
    def is_sync_due(self, last_sync_at: datetime | None, interval_minutes: int) -> bool:
        """Check if synchronization is due."""


# ==============================================================================
# Concrete Reference Implementations
# ==============================================================================

class DefaultDocumentNormalizer(BaseDocumentNormalizer):
    """Standard document normalizer for enterprise SaaS ingestion."""

    _HTML_TAG_RE = re.compile(r"<[^>]+>")
    _WHITESPACE_RE = re.compile(r"\s+")

    def clean_text(self, text: str | None) -> str:
        """Strips HTML tags, decodes entities, and normalizes excess whitespace."""
        if not text:
            return ""
        # Strip HTML if present
        cleaned = self._HTML_TAG_RE.sub(" ", text)
        cleaned = html.unescape(cleaned)
        cleaned = self._WHITESPACE_RE.sub(" ", cleaned).strip()
        return cleaned

    def map_permissions(
        self,
        raw_permissions: list[str],
    ) -> tuple[NormalizedPermissionLevel, list[str]]:
        """Maps platform ACLs to standard KEEP RBAC roles."""
        perms_lower = [p.lower() for p in raw_permissions]
        
        if any(p in perms_lower for p in ["owner", "admin", "full_control"]):
            return NormalizedPermissionLevel.ADMIN, ["SuperAdmin", "OrgAdmin"]
        elif any(p in perms_lower for p in ["write", "editor", "contributor"]):
            return NormalizedPermissionLevel.EDITOR, ["OrgAdmin", "Manager"]
        elif any(p in perms_lower for p in ["public", "domain_shared"]):
            return NormalizedPermissionLevel.PUBLIC, ["SuperAdmin", "OrgAdmin", "Manager", "Member", "Guest"]
        else:
            # Default to VIEWER / READ
            return NormalizedPermissionLevel.READ, ["OrgAdmin", "Manager", "Member"]

    def normalize(
        self,
        item: ExternalResourceItem,
        platform: PlatformType,
        category: PlatformCategory,
    ) -> NormalizedDocument:
        """Converts raw external item to standard NormalizedDocument."""
        content = item.content_text or ""
        if not content and item.content_bytes:
            try:
                content = item.content_bytes.decode("utf-8", errors="replace")
            except (UnicodeDecodeError, ValueError):
                content = ""

        cleaned_content = self.clean_text(content)
        level, roles = self.map_permissions(item.external_permissions)

        # Derive checksum
        hasher = hashlib.sha256()
        hasher.update(f"{item.mime_type}:{cleaned_content}".encode())
        checksum = hasher.hexdigest()

        # Extract title and tags
        title = self.clean_text(item.name) or f"Untitled_{item.external_id}"
        tags = [platform.value.lower(), category.value.lower()]
        if item.department:
            tags.append(item.department.lower())

        return NormalizedDocument(
            external_id=item.external_id,
            source_platform=platform,
            platform_category=category,
            source_url=item.source_url or f"https://{platform.value.lower()}.internal/{item.external_id}",
            title=title,
            raw_content=cleaned_content,
            mime_type=item.mime_type,
            author=item.author or "External User",
            department=item.department,
            tags=tags,
            external_created_at=item.created_at,
            external_modified_at=item.modified_at,
            permission_level=level,
            allowed_roles=roles,
            checksum=checksum,
            version=item.version or "1",
            metadata_json={
                "external_id": item.external_id,
                "platform": platform.value,
                "category": category.value,
                "raw_metadata": item.raw_metadata,
            },
        )


class DefaultChangeDetector(BaseChangeDetector):
    """Cryptographic SHA-256 change detector for incremental updates."""

    def compute_checksum(self, content: str, mime_type: str = "") -> str:
        """Computes SHA-256 fingerprint for document content."""
        hasher = hashlib.sha256()
        hasher.update(f"{mime_type}:{content.strip()}".encode())
        return hasher.hexdigest()

    def detect_changes(
        self,
        external_items: list[ExternalResourceItem],
        known_checksums: dict[str, str],
    ) -> ChangeDetectionResult:
        """Categorizes external items into ADDED, UPDATED, DELETED, or SKIPPED."""
        items: list[ChangeDetectionItem] = []
        added = 0
        updated = 0
        unchanged = 0

        current_external_ids = set()

        for item in external_items:
            current_external_ids.add(item.external_id)
            content = item.content_text or ""
            cs = self.compute_checksum(content, item.mime_type)

            if item.external_id not in known_checksums:
                items.append(ChangeDetectionItem(
                    external_id=item.external_id,
                    action=SyncAction.ADDED,
                    reason="New external resource discovered",
                    checksum=cs,
                    modified_at=item.modified_at,
                ))
                added += 1
            elif known_checksums[item.external_id] != cs:
                items.append(ChangeDetectionItem(
                    external_id=item.external_id,
                    action=SyncAction.UPDATED,
                    reason="Content checksum mismatch",
                    checksum=cs,
                    modified_at=item.modified_at,
                ))
                updated += 1
            else:
                items.append(ChangeDetectionItem(
                    external_id=item.external_id,
                    action=SyncAction.SKIPPED,
                    reason="Content unchanged",
                    checksum=cs,
                    modified_at=item.modified_at,
                ))
                unchanged += 1

        # Check for deleted items
        deleted = 0
        for known_id, known_cs in known_checksums.items():
            if known_id not in current_external_ids:
                items.append(ChangeDetectionItem(
                    external_id=known_id,
                    action=SyncAction.DELETED,
                    reason="Resource removed on external platform",
                    checksum=known_cs,
                    modified_at=datetime.now(UTC),
                ))
                deleted += 1

        return ChangeDetectionResult(
            total_detected=len(items),
            items=items,
            added_count=added,
            updated_count=updated,
            deleted_count=deleted,
            unchanged_count=unchanged,
        )


class DefaultSyncScheduler(BaseSyncScheduler):
    """Synchronization scheduling calculator."""

    def calculate_next_sync(self, last_sync_at: datetime, interval_minutes: int) -> datetime:
        """Returns next scheduled timestamp."""
        return last_sync_at + timedelta(minutes=max(1, interval_minutes))

    def is_sync_due(self, last_sync_at: datetime | None, interval_minutes: int) -> bool:
        """Evaluates whether current time has passed the sync interval."""
        if last_sync_at is None:
            return True
        next_sync = self.calculate_next_sync(last_sync_at, interval_minutes)
        return datetime.now(UTC) >= next_sync


class MockExternalPlatformAdapter(BaseConnectorAdapter):
    """Reference mock adapter for testing multi-platform connector synchronization."""

    def __init__(self, platform: PlatformType = PlatformType.GOOGLE_DRIVE) -> None:
        self.platform = platform
        self.connected = False
        self.credentials: AuthCredentials | None = None
        self._sample_store: dict[str, ExternalResourceItem] = {}
        self._init_mock_data()

    def _init_mock_data(self) -> None:
        """Seed realistic external documents for testing."""
        now = datetime.now(UTC)
        prefix = self.platform.value.lower()

        self._sample_store = {
            f"{prefix}-doc-1": ExternalResourceItem(
                external_id=f"{prefix}-doc-1",
                name=f"{self.platform.value} Architecture Whitepaper",
                mime_type="text/markdown",
                content_text=f"# {self.platform.value} System Design\n\nScalable enterprise data infrastructure and security protocols.",
                source_url=f"https://{prefix}.enterprise.local/docs/1",
                author="alex.chen@enterprise.com",
                department="Engineering",
                created_at=now - timedelta(days=10),
                modified_at=now - timedelta(hours=2),
                version="2",
                external_permissions=["editor", "reader"],
            ),
            f"{prefix}-doc-2": ExternalResourceItem(
                external_id=f"{prefix}-doc-2",
                name=f"{self.platform.value} Operations Playbook",
                mime_type="text/plain",
                content_text="Incident response checklists, on-call schedules, and disaster recovery SLA targets.",
                source_url=f"https://{prefix}.enterprise.local/docs/2",
                author="sam.taylor@enterprise.com",
                department="Operations",
                created_at=now - timedelta(days=30),
                modified_at=now - timedelta(days=5),
                version="1",
                external_permissions=["reader"],
            ),
            f"{prefix}-doc-3": ExternalResourceItem(
                external_id=f"{prefix}-doc-3",
                name=f"{self.platform.value} Executive Strategy Memo",
                mime_type="text/markdown",
                content_text="Confidential board presentation detailing multi-year R&D expansion and market targets.",
                source_url=f"https://{prefix}.enterprise.local/docs/3",
                author="elena.rostova@enterprise.com",
                department="Executive",
                created_at=now - timedelta(days=60),
                modified_at=now - timedelta(days=15),
                version="4",
                external_permissions=["owner", "admin"],
            ),
        }

    def connect(self, credentials: AuthCredentials) -> bool:
        if credentials.is_expired():
            self.connected = False
            return False
        self.credentials = credentials
        self.connected = True
        return True

    def authenticate(self, credentials: AuthCredentials) -> dict[str, Any]:
        if not credentials.access_token and not credentials.api_key and not credentials.service_account_key:
            return {"authenticated": False, "error": "Missing token or key"}
        self.credentials = credentials
        self.connected = True
        return {
            "authenticated": True,
            "platform": self.platform.value,
            "token_type": credentials.token_type,
            "expires_in": credentials.expires_in,
        }

    def test_connection(self) -> bool:
        return self.connected

    def discover_resources(self, since: datetime | None = None) -> list[ExternalResourceItem]:
        if not self.connected:
            raise ConnectionError("Adapter is not connected to external platform.")
        if since is None:
            return list(self._sample_store.values())
        return [
            item for item in self._sample_store.values()
            if item.modified_at and item.modified_at >= since
        ]

    def fetch_resource_content(self, external_id: str) -> ExternalResourceItem:
        if not self.connected:
            raise ConnectionError("Adapter is not connected to external platform.")
        if external_id not in self._sample_store:
            raise KeyError(f"Resource {external_id} not found on {self.platform.value}")
        return self._sample_store[external_id]

    def disconnect(self) -> None:
        self.connected = False
        self.credentials = None

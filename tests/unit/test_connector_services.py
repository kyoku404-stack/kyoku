"""Unit tests for Phase 3.1 Enterprise Connector Service.

Owner: Member 2 (Backend & Database Lead)
Domain: /tests/unit
Specification: devdocs/p3/p3.1.txt & docs/Architecture/enterprise-integrations-connector-framework.md
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from backend.app.models.connector import Connector
from backend.app.schemas.connector import (
    ConnectorAuthenticateRequest,
    ConnectorRegisterRequest,
    ConnectorSyncRequest,
)
from backend.app.services.connectors.contracts import ConnectorStatus
from backend.app.services.connectors.service import (
    EnterpriseConnectorService,
    _decrypt_payload,
    _encrypt_payload,
)


@pytest.fixture
def mock_db() -> AsyncMock:
    db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None
    mock_res.scalar.return_value = 5
    mock_res.scalar_one.return_value = 10
    mock_res.scalars.return_value.all.return_value = []
    mock_res.scalars.return_value.first.return_value = None
    db.execute.return_value = mock_res
    return db


class TestEnterpriseConnectorServiceUnit:
    """Unit test suite for EnterpriseConnectorService."""

    def test_credential_encryption_and_decryption(self) -> None:
        """Verifies symmetric authenticated encryption of credentials."""
        creds = {"access_token": "ya29.sample_token_value", "refresh_token": "1//sample_refresh"}
        encrypted = _encrypt_payload(creds)
        assert isinstance(encrypted, str)
        assert "." in encrypted
        assert "sample_token_value" not in encrypted

        decrypted = _decrypt_payload(encrypted)
        assert decrypted == creds

        # Tampered signature returns empty dict
        tampered = encrypted + "bad_sig"
        assert _decrypt_payload(tampered) == {}

    @pytest.mark.asyncio
    async def test_register_connector_success(self, mock_db: AsyncMock) -> None:
        """Verifies successful connector registration."""
        service = EnterpriseConnectorService()
        org_id = uuid4()
        req = ConnectorRegisterRequest(
            name="Engineering Drive",
            platform_type="GOOGLE_DRIVE",
            platform_category="CLOUD_STORAGE",
            auth_type="OAUTH2",
            config={"sync_interval_minutes": 30},
        )

        res = await service.register_connector(db=mock_db, organization_id=org_id, req=req)

        assert res.name == "Engineering Drive"
        assert res.platform_type == "GOOGLE_DRIVE"
        assert res.status == ConnectorStatus.CONFIGURED.value
        assert res.total_documents_synced == 0
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_register_connector_duplicate_name_conflict(self, mock_db: AsyncMock) -> None:
        """Verifies 409 Conflict when connector name already exists in organization."""
        service = EnterpriseConnectorService()
        org_id = uuid4()
        existing_connector = Connector(id=uuid4(), organization_id=org_id, name="Duplicate Name")

        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = existing_connector
        mock_db.execute.return_value = mock_res

        req = ConnectorRegisterRequest(
            name="Duplicate Name",
            platform_type="GITHUB",
            platform_category="DEVELOPMENT",
            auth_type="PERSONAL_ACCESS_TOKEN",
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.register_connector(db=mock_db, organization_id=org_id, req=req)
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_authenticate_connector_success(self, mock_db: AsyncMock) -> None:
        """Verifies authentication handshake, credential encryption, and status update."""
        service = EnterpriseConnectorService()
        org_id = uuid4()
        conn_id = uuid4()

        mock_conn = Connector(
            id=conn_id,
            organization_id=org_id,
            name="GitHub Repo Connector",
            platform_type="GITHUB",
            platform_category="DEVELOPMENT",
            auth_type="PERSONAL_ACCESS_TOKEN",
            status=ConnectorStatus.CONFIGURED.value,
        )
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = mock_conn
        mock_db.execute.return_value = mock_res

        req = ConnectorAuthenticateRequest(
            connector_id=conn_id,
            auth_type="PERSONAL_ACCESS_TOKEN",
            credentials={"api_key": "ghp_valid_mock_token_123"},
        )

        res = await service.authenticate_connector(db=mock_db, organization_id=org_id, req=req)

        assert res.connector_id == conn_id
        assert res.status == ConnectorStatus.CONNECTED.value
        assert mock_conn.encrypted_credentials is not None
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_connectors(self, mock_db: AsyncMock) -> None:
        """Verifies listing connectors with filters."""
        service = EnterpriseConnectorService()
        org_id = uuid4()

        conn1 = Connector(
            id=uuid4(),
            organization_id=org_id,
            name="Slack Org",
            platform_type="SLACK",
            platform_category="COMMUNICATION",
            auth_type="OAUTH2",
            status="CONNECTED",
            total_documents_synced=15,
            created_at=datetime.now(UTC),
        )
        mock_res = MagicMock()
        mock_res.scalars.return_value.all.return_value = [conn1]
        mock_db.execute.return_value = mock_res

        res = await service.list_connectors(db=mock_db, organization_id=org_id)

        assert res.total_connectors == 1
        assert res.connectors[0].name == "Slack Org"
        assert res.connectors[0].platform_type == "SLACK"

    @pytest.mark.asyncio
    async def test_start_sync_pipeline(self, mock_db: AsyncMock) -> None:
        """Verifies running the sync job, creating logs, and marking connector healthy."""
        service = EnterpriseConnectorService()
        org_id = uuid4()
        conn_id = uuid4()

        mock_conn = Connector(
            id=conn_id,
            organization_id=org_id,
            name="Google Drive Prod",
            platform_type="GOOGLE_DRIVE",
            platform_category="CLOUD_STORAGE",
            auth_type="OAUTH2",
            status="CONNECTED",
            total_documents_synced=0,
            created_at=datetime.now(UTC),
        )

        mock_res_conn = MagicMock()
        mock_res_conn.scalar_one_or_none.return_value = mock_conn

        mock_res_past_logs = MagicMock()
        mock_res_past_logs.scalars.return_value.all.return_value = []

        # Return mock_conn on first query, then past logs
        mock_db.execute.side_effect = [mock_res_conn, mock_res_past_logs]

        req = ConnectorSyncRequest(
            connector_id=conn_id,
            sync_mode="INCREMENTAL",
        )

        res = await service.start_sync(db=mock_db, organization_id=org_id, req=req)

        assert res.connector_id == conn_id
        assert res.status == "COMPLETED"
        assert mock_conn.status == ConnectorStatus.HEALTHY.value
        assert mock_conn.total_documents_synced >= 3

    @pytest.mark.asyncio
    async def test_get_connector_status_telemetry(self, mock_db: AsyncMock) -> None:
        """Verifies real-time status and health metrics calculation."""
        service = EnterpriseConnectorService()
        org_id = uuid4()
        conn_id = uuid4()

        mock_conn = Connector(
            id=conn_id,
            organization_id=org_id,
            name="Notion Team Docs",
            platform_type="NOTION",
            platform_category="DOCUMENTATION",
            auth_type="OAUTH2",
            status="HEALTHY",
            total_documents_synced=50,
            last_sync_at=datetime.now(UTC),
            last_sync_status="COMPLETED",
        )

        mock_res_conn = MagicMock()
        mock_res_conn.scalar_one_or_none.return_value = mock_conn

        mock_res_job = MagicMock()
        mock_res_job.scalars.return_value.first.return_value = None

        mock_res_total_logs = MagicMock()
        mock_res_total_logs.scalar_one.return_value = 50

        mock_res_failed_logs = MagicMock()
        mock_res_failed_logs.scalar_one.return_value = 1

        mock_db.execute.side_effect = [
            mock_res_conn,
            mock_res_job,
            mock_res_total_logs,
            mock_res_failed_logs,
        ]

        status_res = await service.get_connector_status(
            db=mock_db,
            organization_id=org_id,
            connector_id=conn_id,
        )

        assert status_res.id == conn_id
        assert status_res.status == "HEALTHY"
        assert status_res.health_metrics.api_latency_ms > 0
        assert status_res.health_metrics.success_rate_pct == 98.0

    @pytest.mark.asyncio
    async def test_remove_connector(self, mock_db: AsyncMock) -> None:
        """Verifies removing a connector."""
        service = EnterpriseConnectorService()
        org_id = uuid4()
        conn_id = uuid4()

        mock_conn = Connector(
            id=conn_id,
            organization_id=org_id,
            name="Obsolete Connector",
            platform_type="JIRA",
            status="CONNECTED",
        )
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = mock_conn
        mock_db.execute.return_value = mock_res

        res = await service.remove_connector(db=mock_db, organization_id=org_id, connector_id=conn_id)

        assert res.id == conn_id
        assert res.status == ConnectorStatus.DISCONNECTED.value
        mock_db.delete.assert_called_once_with(mock_conn)
        mock_db.commit.assert_awaited_once()

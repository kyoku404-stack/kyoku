"""KEEP Enterprise Platform — Organization Management Service."""

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from backend.app.core.constants import ErrorCode
from backend.app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from backend.app.models.organization import Organization
from backend.app.repositories.org_repo import OrganizationRepository
from backend.app.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)
from backend.app.services.activity_service import ActivityService
from backend.app.services.base import BaseService
from sqlalchemy.ext.asyncio import AsyncSession


class OrganizationService(BaseService[OrganizationRepository]):
    """Service handling tenant organization operations."""

    def __init__(self, repository: OrganizationRepository | None = None) -> None:
        super().__init__(repository or OrganizationRepository())

    def _to_response(self, org: Organization) -> OrganizationResponse:
        """Converts an Organization ORM entity to typed response DTO."""
        settings_dict: dict[str, Any] | None = None
        if org.settings_json:
            try:
                settings_dict = json.loads(org.settings_json)
            except (json.JSONDecodeError, TypeError):
                settings_dict = None

        return OrganizationResponse(
            id=org.id,
            name=org.name,
            domain=org.domain,
            industry=org.industry,
            company_size=org.company_size,
            time_zone=org.time_zone or "UTC",
            default_language=org.default_language or "en-US",
            logo_url=org.logo_url,
            description=org.description,
            is_active=org.is_active,
            settings=settings_dict,
            created_at=org.created_at,
            updated_at=org.updated_at,
        )

    async def create_organization(
        self,
        db: AsyncSession,
        payload: OrganizationCreate,
        creator_user_id: UUID | None = None,
    ) -> OrganizationResponse:
        """Creates and persists a new enterprise tenant organization."""
        existing_domain = await self.repository.get_by_domain(db, payload.domain)
        if existing_domain:
            raise ConflictException(
                message=f"Organization with domain '{payload.domain}' already exists.",
                code=ErrorCode.ORG_DOMAIN_EXISTS,
            )

        existing_name = await self.repository.get_by_name(db, payload.name)
        if existing_name:
            raise ConflictException(
                message=f"Organization with name '{payload.name}' already exists.",
                code=ErrorCode.ORG_NAME_EXISTS,
            )

        initial_settings = {
            "max_upload_size_mb": 50,
            "default_llm": "gpt-4o",
            "embedding_model": "text-embedding-3-small",
            "citation_preferences": "in-text-brackets",
        }

        org = Organization(
            name=payload.name,
            domain=payload.domain,
            industry=payload.industry,
            company_size=payload.company_size,
            time_zone=payload.time_zone or "UTC",
            default_language=payload.default_language or "en-US",
            logo_url=payload.logo_url,
            description=payload.description,
            settings_json=json.dumps(initial_settings),
            is_active=True,
        )
        db.add(org)
        await db.flush()
        await db.refresh(org)

        await ActivityService.record_activity(
            db,
            organization_id=org.id,
            user_id=creator_user_id,
            action="ORGANIZATION_CREATED",
            resource_type="organization",
            resource_id=org.id,
            details=f"Created organization '{org.name}' ({org.domain})",
        )
        await db.commit()
        await db.refresh(org)
        return self._to_response(org)

    async def get_current_organization(
        self,
        db: AsyncSession,
        org_id: UUID,
    ) -> OrganizationResponse:
        """Returns details for the active tenant organization."""
        org = await self.repository.get_active_by_id(db, org_id)
        if not org:
            raise NotFoundException(
                message="Organization not found or inactive.",
                code=ErrorCode.ORG_NOT_FOUND,
            )
        return self._to_response(org)

    async def get_organization_by_id(
        self,
        db: AsyncSession,
        org_id: UUID,
        caller_org_id: UUID,
        is_super_admin: bool = False,
    ) -> OrganizationResponse:
        """Retrieves organization details enforcing multi-tenant isolation."""
        if not is_super_admin and org_id != caller_org_id:
            raise ForbiddenException(
                message="Cross-tenant access forbidden.",
                code=ErrorCode.TENANT_ACCESS_DENIED,
            )

        org = await self.repository.get_active_by_id(db, org_id)
        if not org:
            raise NotFoundException(
                message="Organization not found or inactive.",
                code=ErrorCode.ORG_NOT_FOUND,
            )
        return self._to_response(org)

    async def update_organization(
        self,
        db: AsyncSession,
        org_id: UUID,
        payload: OrganizationUpdate,
        caller_user_id: UUID,
    ) -> OrganizationResponse:
        """Updates organization settings and metadata."""
        org = await self.repository.get_active_by_id(db, org_id)
        if not org:
            raise NotFoundException(
                message="Organization not found.",
                code=ErrorCode.ORG_NOT_FOUND,
            )

        if payload.name and payload.name != org.name:
            existing_name = await self.repository.get_by_name(db, payload.name)
            if existing_name and existing_name.id != org.id:
                raise ConflictException(
                    message=f"Organization name '{payload.name}' is already in use.",
                    code=ErrorCode.ORG_NAME_EXISTS,
                )
            org.name = payload.name

        if payload.time_zone is not None:
            org.time_zone = payload.time_zone
        if payload.default_language is not None:
            org.default_language = payload.default_language
        if payload.logo_url is not None:
            org.logo_url = payload.logo_url
        if payload.description is not None:
            org.description = payload.description
        if payload.is_active is not None:
            org.is_active = payload.is_active

        if payload.settings is not None:
            current_settings = {}
            if org.settings_json:
                try:
                    current_settings = json.loads(org.settings_json)
                except (json.JSONDecodeError, TypeError):
                    current_settings = {}
            current_settings.update(payload.settings)
            org.settings_json = json.dumps(current_settings)

        db.add(org)
        await db.flush()

        await ActivityService.record_activity(
            db,
            organization_id=org.id,
            user_id=caller_user_id,
            action="ORGANIZATION_UPDATED",
            resource_type="organization",
            resource_id=org.id,
            details=f"Updated settings for '{org.name}'",
        )
        await db.commit()
        await db.refresh(org)
        return self._to_response(org)

    async def delete_organization(
        self,
        db: AsyncSession,
        org_id: UUID,
        caller_user_id: UUID,
    ) -> bool:
        """Soft-deletes / archives an enterprise organization."""
        org = await self.repository.get_active_by_id(db, org_id)
        if not org:
            raise NotFoundException(
                message="Organization not found.",
                code=ErrorCode.ORG_NOT_FOUND,
            )

        org.is_deleted = True
        org.is_active = False
        org.deleted_at = datetime.now(UTC)
        db.add(org)
        await db.flush()

        await ActivityService.record_activity(
            db,
            organization_id=org.id,
            user_id=caller_user_id,
            action="ORGANIZATION_ARCHIVED",
            resource_type="organization",
            resource_id=org.id,
            details=f"Archived organization '{org.name}'",
        )
        await db.commit()
        return True

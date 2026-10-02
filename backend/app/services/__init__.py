"""KEEP Backend Domain Services Package.

Contains business logic, RAG engine, AI integrations, document processing,
and cross-component workflow orchestration.
"""

try:
    from backend.app.services.auth_service import AuthService
    from backend.app.services.base import BaseService
    from backend.app.services.chat_service import ChatService
    from backend.app.services.document_service import DocumentService
    from backend.app.services.health_service import HealthService
    from backend.app.services.org_service import OrganizationService
    from backend.app.services.search_service import SearchService
    from backend.app.services.user_service import UserService

    __all__ = [
        "AuthService",
        "BaseService",
        "ChatService",
        "DocumentService",
        "HealthService",
        "OrganizationService",
        "SearchService",
        "UserService",
    ]
except ImportError:
    __all__ = []

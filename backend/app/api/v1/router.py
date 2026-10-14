"""KEEP Enterprise Platform — API v1 Master Router.

Mounts and registers all v1 modular sub-routers.
"""

from backend.app.api.v1.activity import router as activity_router
from backend.app.api.v1.ai import router as ai_router
from backend.app.api.v1.analytics import router as analytics_router
from backend.app.api.v1.audit import router as audit_router
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.chat import router as chat_router
from backend.app.api.v1.dashboard import router as dashboard_router
from backend.app.api.v1.departments import router as departments_router
from backend.app.api.v1.documents import router as documents_router
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.invitations import router as invitations_router
from backend.app.api.v1.members import router as members_router
from backend.app.api.v1.notifications import router as notifications_router
from backend.app.api.v1.organizations import router as organizations_router
from backend.app.api.v1.projects import router as projects_router
from backend.app.api.v1.search import router as search_router
from backend.app.api.v1.teams import router as teams_router
from backend.app.api.v1.users import router as users_router
from fastapi import APIRouter

api_v1_router = APIRouter()

api_v1_router.include_router(auth_router)
api_v1_router.include_router(audit_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(organizations_router)
api_v1_router.include_router(departments_router)
api_v1_router.include_router(teams_router)
api_v1_router.include_router(projects_router)
api_v1_router.include_router(invitations_router)
api_v1_router.include_router(members_router)
api_v1_router.include_router(documents_router)
api_v1_router.include_router(dashboard_router)
api_v1_router.include_router(activity_router)
api_v1_router.include_router(notifications_router)
api_v1_router.include_router(search_router)
api_v1_router.include_router(chat_router)
api_v1_router.include_router(ai_router)
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(health_router)

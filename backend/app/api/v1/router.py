"""KEEP Enterprise Platform — API v1 Master Router.

Mounts and registers all v1 modular sub-routers.
"""

from backend.app.api.v1.analytics import router as analytics_router
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.chat import router as chat_router
from backend.app.api.v1.documents import router as documents_router
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.organizations import router as organizations_router
from backend.app.api.v1.search import router as search_router
from backend.app.api.v1.users import router as users_router
from fastapi import APIRouter

api_v1_router = APIRouter()

api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(organizations_router)
api_v1_router.include_router(documents_router)
api_v1_router.include_router(search_router)
api_v1_router.include_router(chat_router)
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(health_router)

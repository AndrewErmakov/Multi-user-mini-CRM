from .activities import router as activities_router
from .analytics import router as analytics_router
from .auth import router as auth_router
from .contacts import router as contacts_router
from .deals import router as deals_router
from .organizations import router as organizations_router
from .tasks import router as tasks_router

__all__ = [
    "auth_router",
    "organizations_router",
    "contacts_router",
    "deals_router",
    "tasks_router",
    "activities_router",
    "analytics_router",
]

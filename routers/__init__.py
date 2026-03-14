from .auth import router as auth_router
from .users import router as users_router
from .poems import router as poems_router
from .admin import router as admin_router
from .ai import router as ai_router

__all__ = ["auth_router", "users_router", "poems_router", "admin_router", "ai_router"]

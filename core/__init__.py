# core/__init__.py
from .config import settings
from .database import get_db, supabase

__all__ = ["settings", "get_db", "supabase"]

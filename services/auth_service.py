import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from passlib.context import CryptContext
from supabase import Client
from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory storage for virtual admins
virtual_admin_read_poems: Dict[str, List[str]] = {}
virtual_admin_pinned_poems: Dict[str, Optional[str]] = {}

class AuthService:
    @staticmethod
    def create_access_token(data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    @staticmethod
    def get_password_hash(password):
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password, hashed_password):
        try:
            safe_password = plain_password[:72] if plain_password else ""
            return pwd_context.verify(safe_password, hashed_password)
        except Exception as e:
            print(f"Ошибка при проверке пароля: {e}")
            return False

    @staticmethod
    def is_virtual_admin(username: str) -> bool:
        return username in settings.ADMINS_DICT

    @staticmethod
    def check_virtual_admin(username: str, password: str) -> bool:
        return settings.ADMINS_DICT.get(username) == password

    @staticmethod
    def get_virtual_admin_data(username: str) -> Dict[str, Any]:
        if username not in virtual_admin_read_poems:
            virtual_admin_read_poems[username] = []
        if username not in virtual_admin_pinned_poems:
            virtual_admin_pinned_poems[username] = None
            
        return {
            'username': username,
            'is_admin': True,
            'read_poems_json': virtual_admin_read_poems[username],
            'pinned_poem_title': virtual_admin_pinned_poems[username],
            'show_all_tab': False,
            'user_data': ''
        }

    @staticmethod
    def toggle_virtual_admin_read_status(username: str, title: str) -> str:
        """Переключает статус прочтения стиха для виртуального админа."""
        reads = virtual_admin_read_poems.get(username, [])
        if title in reads:
            reads.remove(title)
            action = 'unmarked'
        else:
            reads.append(title)
            action = 'marked'
        virtual_admin_read_poems[username] = reads
        return action
        
    @staticmethod
    def toggle_virtual_admin_pinned_poem(username: str, title: str) -> tuple[str, str]:
        """Переключает статус изучаемого стиха для виртуального админа."""
        current_pinned = virtual_admin_pinned_poems.get(username)
        if current_pinned == title:
            new_pinned = None
            action = 'unpinned'
        else:
            new_pinned = title
            action = 'pinned'
        virtual_admin_pinned_poems[username] = new_pinned
        return action, new_pinned

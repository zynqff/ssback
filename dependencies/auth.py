from fastapi import Depends, HTTPException, status, Request
import jwt
from core.config import settings
from core.database import get_db, get_user
from supabase import Client
from services.auth_service import AuthService

def get_current_user(request: Request, db: Client = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            detail="Not authenticated",
            headers={"Location": "/login"},
        )
    
    try:
        if token.startswith("Bearer "):
            token = token.split(" ")[1]
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # Проверяем виртуальных админов
        if AuthService.is_virtual_admin(username):
            return AuthService.get_virtual_admin_data(username)
        
        user = get_user(username)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
        
    except (jwt.PyJWTError, IndexError, jwt.exceptions.DecodeError) as e:
        print(f"JWT Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login"},
            detail="Could not validate credentials"
        ) from None

def get_current_user_optional(request: Request, db: Client = Depends(get_db)):
    try:
        return get_current_user(request, db)
    except HTTPException:
        return None

def get_admin_user(current_user = Depends(get_current_user)):
    if not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Доступ запрещен. Требуются права администратора.")
    return current_user

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from typing import Optional

from core.database import get_db
from services.auth_service import AuthService
from services.user_service import UserService
from services.poem_service import PoemService
from dependencies.auth import get_current_user, get_current_user_optional

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/poems")
async def get_poems_api(db: Client = Depends(get_db)):
    """Отдаёт все стихи в JSON — используется мобильным приложением."""
    poems_resp = db.table('poem').select("*").execute()
    poems = PoemService.process_poems_data(poems_resp.data or [])
    return {"success": True, "poems": poems}


@router.get("/me")
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: Client = Depends(get_db)
):
    """Возвращает данные текущего пользователя для мобильного приложения."""
    username = current_user.get("username")

    # Для виртуальных админов — отдаём их данные напрямую
    if AuthService.is_virtual_admin(username):
        admin_data = AuthService.get_virtual_admin_data(username)
        return {
            "username": username,
            "is_admin": True,
            "read_poems": admin_data.get("read_poems_json", []),
            "pinned_poem_title": admin_data.get("pinned_poem_title"),
            "show_all_tab": False,
            "user_data": "",
        }

    try:
        user_res = db.table('user').select("*").eq("username", username).single().execute()
        user = user_res.data
    except Exception:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    read_poems = UserService.parse_read_poems_json(user.get("read_poems_json", []))

    return {
        "username": username,
        "is_admin": user.get("is_admin", False),
        "read_poems": read_poems,
        "pinned_poem_title": user.get("pinned_poem_title"),
        "show_all_tab": user.get("show_all_tab", False),
        "user_data": user.get("user_data", ""),
    }


@router.post("/login_json")
async def login_json(
    body: dict,
    db: Client = Depends(get_db)
):
    """JSON-логин для мобильного приложения — возвращает JWT токен."""
    username = body.get("username", "").strip()
    password = body.get("password", "")

    if not username or not password:
        raise HTTPException(status_code=400, detail="Заполните все поля")

    # Виртуальные админы
    if AuthService.is_virtual_admin(username):
        if AuthService.check_virtual_admin(username, password):
            token = AuthService.create_access_token(data={"sub": username, "is_admin": True})
            return {"access_token": token, "is_admin": True, "username": username}
        raise HTTPException(status_code=401, detail="Неверный пароль администратора")

    # Обычные пользователи
    try:
        user_res = db.table('user').select("*").eq("username", username).execute()
        if user_res.data:
            user = user_res.data[0]
            if AuthService.verify_password(password, user["password_hash"]):
                token = AuthService.create_access_token(data={
                    "sub": username,
                    "is_admin": user.get("is_admin", False)
                })
                return {
                    "access_token": token,
                    "is_admin": user.get("is_admin", False),
                    "username": username
                }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {e}")

    raise HTTPException(status_code=401, detail="Неверный логин или пароль")


@router.post("/register_json")
async def register_json(body: dict, db: Client = Depends(get_db)):
    """JSON-регистрация для мобильного приложения."""
    username = body.get("username", "").strip()
    password = body.get("password", "")

    if not username or not password:
        raise HTTPException(status_code=400, detail="Заполните все поля")
    if len(password) < 4:
        raise HTTPException(status_code=400, detail="Пароль не менее 4 символов")

    existing = db.table('user').select('username').eq('username', username).execute()
    if existing.data:
        raise HTTPException(status_code=409, detail="Пользователь уже существует")

    hashed = AuthService.get_password_hash(password)
    db.table('user').insert({"username": username, "password_hash": hashed}).execute()
    return {"success": True}

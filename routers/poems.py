from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from supabase import Client
from typing import Optional
import json

from core.database import get_db
from schemas import ToggleModel
from services.auth_service import AuthService
from services.user_service import UserService
from services.poem_service import PoemService
from dependencies.auth import get_current_user, get_current_user_optional

router = APIRouter(prefix="", tags=["poems"])

@router.get("/", response_class=HTMLResponse)
async def read_root(
    request: Request, 
    db: Client = Depends(get_db), 
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")
    
    poems_response = db.table('poem').select("*").execute()
    poems = PoemService.process_poems_data(poems_response.data or [])

    read_poems = []
    if current_user:
        read_poems_json = current_user.get('read_poems_json')
        read_poems = UserService.parse_read_poems_json(read_poems_json)

    context = {
        "request": request,
        "poems": poems,
        "read_poems": read_poems,
        "pinned_title": current_user.get('pinned_poem_title') if current_user else None,
        "is_admin": current_user.get('is_admin', False) if current_user else False,
        "show_all_tab": current_user.get('show_all_tab', False) if current_user else False,
        "current_user": current_user,
    }
    return templates.TemplateResponse("index.html", context)

@router.post("/toggle_read")
async def toggle_read(
    toggle_data: ToggleModel,
    db: Client = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    username = current_user.get('username')
    
    # Проверяем, является ли пользователь виртуальным админом
    if AuthService.is_virtual_admin(username):
        action = AuthService.toggle_virtual_admin_read_status(username, toggle_data.title)
        return {"success": True, "action": action}
    
    poem_resp = db.table('poem').select('title').eq('title', toggle_data.title).execute()
    if not poem_resp.data:
        raise HTTPException(status_code=404, detail="Стих не найден")

    try:
        read_list = UserService.parse_read_poems_json(current_user.get('read_poems_json', []))
        action, new_read_list = UserService.toggle_poem_read_status(db, current_user['username'], toggle_data.title, read_list)
        return {"success": True, "action": action}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении БД: {str(e)}")

@router.post("/toggle_pin")
async def toggle_pin(
    toggle_data: ToggleModel,
    db: Client = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    username = current_user.get('username')

    # Проверяем, является ли пользователь виртуальным админом
    if AuthService.is_virtual_admin(username):
        action, new_pinned = AuthService.toggle_virtual_admin_pinned_poem(username, toggle_data.title)
        return {
            "success": True, 
            "action": action, 
            "pinned_title": new_pinned
        }
    
    poem_resp = db.table('poem').select('title').eq('title', toggle_data.title).execute()
    if not poem_resp.data:
        raise HTTPException(status_code=404, detail="Стих не найден")

    try:
        current_pinned = current_user.get('pinned_poem_title')
        action, new_pinned = UserService.toggle_pinned_poem(db, current_user['username'], toggle_data.title, current_pinned)
        return {
            "success": True, 
            "action": action, 
            "pinned_title": new_pinned
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении БД: {str(e)}")

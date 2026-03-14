from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse
from supabase import Client
from typing import Optional

from core.database import get_db
from services.auth_service import AuthService
from services.user_service import UserService
from dependencies.auth import get_current_user

router = APIRouter(prefix="", tags=["users"])

@router.get("/profile", response_class=HTMLResponse)
async def profile_get(request: Request, current_user: dict = Depends(get_current_user)):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")
    
    return templates.TemplateResponse("profile.html", {
        "request": request, 
        "current_user": current_user, 
        "user_data": current_user.get('user_data', ''), 
        "show_all_tab": current_user.get('show_all_tab', False)
    })

@router.post("/profile", response_class=HTMLResponse)
async def profile_post(
    request: Request,
    db: Client = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    new_password: Optional[str] = Form(None),
    user_data: Optional[str] = Form(None),
    show_all_tab: Optional[str] = Form(None)
):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")
    
    # Проверяем, является ли пользователь виртуальным админом
    if AuthService.is_virtual_admin(current_user.get('username')):
        return templates.TemplateResponse("profile.html", {
            "request": request, 
            "current_user": current_user,
            "user_data": current_user.get('user_data', ''),
            "show_all_tab": current_user.get('show_all_tab', False),
            "error": "Настройки профиля недоступны для виртуальных администраторов"
        })
    
    update_data = {}
    
    if new_password:
        if len(new_password) < 4:
            return templates.TemplateResponse("profile.html", {
                "request": request, 
                "current_user": current_user, 
                "user_data": current_user.get('user_data', ''),
                "show_all_tab": current_user.get('show_all_tab', False),
                "error": "Новый пароль должен быть не менее 4 символов."
            })
        update_data['password_hash'] = AuthService.get_password_hash(new_password)

    if user_data is not None:
        update_data['user_data'] = user_data
    
    update_data['show_all_tab'] = show_all_tab == 'on'

    if update_data:
        try:
            db.table('user').update(update_data).eq('username', current_user['username']).execute()
            # Обновляем данные пользователя для отображения
            current_user.update(update_data)

        except Exception as e:
            return templates.TemplateResponse("profile.html", {
                "request": request, 
                "current_user": current_user, 
                "error": f"Ошибка обновления: {e}"
            })

    return templates.TemplateResponse("profile.html", {
        "request": request, 
        "current_user": current_user, 
        "user_data": current_user.get('user_data', ''),
        "show_all_tab": current_user.get('show_all_tab', False), 
        "success": "Настройки профиля обновлены!"
    })

from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from supabase import Client
from typing import Optional

from core.database import get_db, get_user
from core.config import settings
from schemas import Token
from services.auth_service import AuthService
from dependencies.auth import get_current_user_optional

router = APIRouter(prefix="", tags=["auth"])
templates = Jinja2Templates(directory="templates")

@router.get("/login", response_class=HTMLResponse)
async def login_get(request: Request, current_user: Optional[dict] = Depends(get_current_user_optional)):
    if current_user:
        return RedirectResponse(url="/profile", status_code=status.HTTP_302_FOUND)
    
    context = {"request": request}
    if request.query_params.get("msg") == "reg_success":
        context["success"] = "Регистрация прошла успешно! Вы можете войти."
        
    return templates.TemplateResponse("login.html", context)

@router.post("/login")
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Client = Depends(get_db)
):
    # 1. Проверка виртуальных админов
    if AuthService.is_virtual_admin(username):
        if AuthService.check_virtual_admin(username, password):
            access_token = AuthService.create_access_token(data={"sub": username, "is_admin": True})
            resp = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
            resp.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True, max_age=60*60*24)
            return resp
        else:
            return templates.TemplateResponse("login.html", {"request": request, "error": "Неверный пароль администратора"})

    # 2. Проверка обычных пользователей
    try:
        user_res = db.table('user').select("*").eq("username", username).execute()
        if user_res.data:
            user = user_res.data[0]
            if AuthService.verify_password(password, user['password_hash']):
                access_token = AuthService.create_access_token(data={
                    "sub": username, 
                    "is_admin": user.get('is_admin', False)
                })
                resp = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
                resp.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True, max_age=60*60*24)
                return resp
    except Exception as e:
        print(f"Ошибка входа: {e}")

    return templates.TemplateResponse("login.html", {"request": request, "error": "Неверное имя пользователя или пароль"})

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response

@router.get("/register", response_class=HTMLResponse)
async def register_get(request: Request, current_user: Optional[dict] = Depends(get_current_user_optional)):
    if current_user:
        return RedirectResponse(url="/profile", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register", response_class=HTMLResponse)
async def register_post(
    request: Request,
    db: Client = Depends(get_db),
    username: str = Form(...),
    password: str = Form(...)
):
    if len(password) < 4:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Пароль должен быть не менее 4 символов."
        })

    if get_user(username):
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Пользователь с таким именем уже существует!"
        })

    hashed_password = AuthService.get_password_hash(password)
    
    try:
        db.table('user').insert({
            "username": username,
            "password_hash": hashed_password
        }).execute()
    except Exception as e:
        return templates.TemplateResponse("register.html", {
            "request": request, "error": f"Ошибка регистрации: {e}"
        })

    return RedirectResponse(url="/login?msg=reg_success", status_code=status.HTTP_303_SEE_OTHER)

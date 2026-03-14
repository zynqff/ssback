from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from supabase import Client

from core.config import settings
from core.database import get_db
from services.auth_service import AuthService

router = APIRouter(prefix="/google", tags=["google_auth"])

# Проверка наличия ключей в конфигурации
if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
    # Можно либо вызывать исключение, либо просто не регистрировать роутер,
    # но для ясности лучше вызовем исключение при запуске, если переменные не заданы.
    raise RuntimeError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in the .env file")

oauth = OAuth()
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    client_kwargs={
        'scope': 'openid email profile'
    }
)

@router.get('/login', name='google_login')
async def google_login(request: Request):
    """
    Перенаправляет пользователя на страницу аутентификации Google.
    """
    redirect_uri = request.url_for('google_auth_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get('/auth', name='google_auth_callback')
async def google_auth_callback(request: Request, db: Client = Depends(get_db)):
    """
    Обрабатывает коллбэк от Google после аутентификации.
    """
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')
        
        if not user_info or not user_info.get('email'):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not retrieve user info from Google")

        email = user_info['email']
        
        # Пытаемся найти пользователя по email (который мы будем использовать как username)
        existing_user_res = db.table('user').select("*").eq("username", email).execute()
        
        if not existing_user_res.data:
            # Если пользователя нет, создаем нового
            # Для OAuth пользователей пароль не нужен, но поле в БД может быть обязательным.
            # Мы можем использовать "not_set" или сгенерированную строку.
            hashed_password = AuthService.get_password_hash(f"oauth_user_{email}")
            db.table('user').insert({
                "username": email,
                "password_hash": hashed_password
            }).execute()

        # Создаем JWT токен для сессии
        access_token = AuthService.create_access_token(data={"sub": email, "is_admin": False})
        
        # Устанавливаем токен в куки и редиректим на главную
        response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(
            key="access_token", 
            value=f"Bearer {access_token}", 
            httponly=True, 
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        return response

    except Exception as e:
        print(f"Ошибка аутентификации Google: {e}")
        # В случае ошибки перенаправляем на страницу входа с сообщением
        return RedirectResponse(url="/login?error=google_auth_failed", status_code=status.HTTP_303_SEE_OTHER)

import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

# Загружаем .env
load_dotenv()

# Импортируем роутеры
from routers import auth, users, poems, admin, ai, google_auth, mobile_api
from core.database import get_db, supabase
from core.config import settings

app = FastAPI(title="Сборник Стихов")

# Добавляем middleware для сессий, необходимо для Authlib
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# Настройка статических файлов и шаблонов
# app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Подключаем роутеры
app.include_router(mobile_api.router, tags=["mobile_api"])
app.include_router(auth.router, tags=["auth"])
app.include_router(google_auth.router, tags=["google_auth"])
app.include_router(users.router, tags=["users"])
app.include_router(poems.router, tags=["poems"])
app.include_router(admin.router, tags=["admin"])
app.include_router(ai.router, tags=["ai"])

@app.get("/")
async def root():
    return {"message": "Сборник Стихов API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

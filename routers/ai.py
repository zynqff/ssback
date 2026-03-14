from fastapi import APIRouter, Depends, HTTPException, Request
from services.ai_service import AIService
from dependencies.auth import get_current_user, get_admin_user
from datetime import datetime, timedelta
from pydantic import BaseModel
from supabase import Client
from core.database import get_db

router = APIRouter(prefix="/ai", tags=["ai"])

class KeyModel(BaseModel):
    key: str

@router.post("/verify_key")
def verify_key(key_model: KeyModel, current_user: dict = Depends(get_current_user), db: Client = Depends(get_db)):
    if AIService.validate_key(db, key_model.key):
        try:
            db.table('user').update({"user_gemini_key": key_model.key}).eq("username", current_user['username']).execute()
            return {"success": True}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка при сохранении ключа: {e}")
    raise HTTPException(status_code=403, detail="Неверный или просроченный ключ.")

@router.post("/generate_key")
def generate_key(
    request: Request,
    current_user: dict = Depends(get_admin_user),
    db: Client = Depends(get_db),
    expires_in_hours: int = 0,
    daily_limit: int = 0
):
    expires_at = None
    if expires_in_hours > 0:
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
    
    limit = None
    if daily_limit > 0:
        limit = daily_limit
        
    key = AIService.generate_api_key(db, current_user["username"], expires_at, limit)
    if not key:
        raise HTTPException(status_code=500, detail="Не удалось сгенерировать ключ.")
    return {"key": key}

@router.get("/get_keys")
def get_keys(current_user: dict = Depends(get_admin_user), db: Client = Depends(get_db)):
    return AIService.get_keys_for_admin(db, current_user["username"])

@router.post("/disable_key/{key}")
def disable_key(key: str, current_user: dict = Depends(get_admin_user), db: Client = Depends(get_db)):
    if AIService.disable_key(db, key):
        return {"success": True, "message": "Key disabled"}
    raise HTTPException(status_code=404, detail="Key not found or could not be disabled")

@router.post("/chat")
def chat_with_ai(request: Request, prompt: str, current_user: dict = Depends(get_current_user), db: Client = Depends(get_db)):
    has_access = False
    username = current_user.get("username")

    # Админы имеют доступ по умолчанию
    if current_user.get("is_admin"):
        has_access = True
    
    # Проверяем личный ключ пользователя
    if not has_access:
        user_key = current_user.get('user_gemini_key')
        if user_key and AIService.validate_key(db, user_key):
            has_access = True

    if not has_access:
        raise HTTPException(status_code=403, detail="У вас нет доступа к AI-функции. Пожалуйста, введите действующий ключ в профиле.")
    
    # Загружаем историю чата
    history = AIService.get_chat_history(db, username)
    
    # Получаем ответ от модели
    response_text = AIService.get_groq_response(prompt, history)
    
    # Сохраняем и вопрос, и ответ в историю
    AIService.save_chat_message(db, username, 'user', prompt)
    AIService.save_chat_message(db, username, 'assistant', response_text)
    
    return {"response": response_text}

from supabase import create_client, Client
from core.config import settings

# Проверка наличия переменных окружения
if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
    raise RuntimeError("Supabase URL and Key must be set in the .env file")

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def get_db() -> Client:
    """Возвращает экземпляр клиента Supabase."""
    return supabase

def get_user(username: str):
    """Получает пользователя из Supabase по имени."""
    try:
        response = supabase.table('user').select("*").eq('username', username).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error getting user: {e}")
        return None

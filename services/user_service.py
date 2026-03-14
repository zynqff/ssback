import json
from typing import List, Dict, Any
from supabase import Client

class UserService:
    @staticmethod
    def get_read_poems_titles(user: Dict[str, Any]) -> List[str]:
        """Возвращает список заголовков прочитанных стихов."""
        return user.get('read_poems_json', [])

    @staticmethod
    def is_poem_read(user: Dict[str, Any], title: str) -> bool:
        """Проверяет, прочитан ли стих."""
        return title in UserService.get_read_poems_titles(user)

    @staticmethod
    def toggle_poem_read_status(db: Client, username: str, title: str, current_reads: List[str]) -> tuple[str, List[str]]:
        """Переключает статус прочтения стиха."""
        if title in current_reads:
            current_reads.remove(title)
            action = 'unmarked'
        else:
            current_reads.append(title)
            action = 'marked'
        
        # Сохраняем в БД
        db.table('user').update({"read_poems_json": current_reads}).eq("username", username).execute()
        return action, current_reads

    @staticmethod
    def toggle_pinned_poem(db: Client, username: str, title: str, current_pinned: str) -> tuple[str, str]:
        """Переключает статус изучаемого стиха."""
        if current_pinned == title:
            new_pinned = None
            action = 'unpinned'
        else:
            new_pinned = title
            action = 'pinned'
        
        # Сохраняем в БД
        db.table('user').update({'pinned_poem_title': new_pinned}).eq('username', username).execute()
        return action, new_pinned

    @staticmethod
    def parse_read_poems_json(read_poems_json) -> List[str]:
        """Парсит JSON прочитанных стихов."""
        if isinstance(read_poems_json, str):
            try:
                return json.loads(read_poems_json)
            except json.JSONDecodeError:
                return []
        elif isinstance(read_poems_json, list):
            return read_poems_json
        return []

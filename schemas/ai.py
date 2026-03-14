from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class AIAccessKey(BaseModel):
    key: str
    generated_by: str
    assigned_to: Optional[str] = None
    expires_at: Optional[datetime] = None
    daily_limit: Optional[int] = None
    is_active: bool = True
    created_at: datetime

class AIChatMessage(BaseModel):
    session_id: str
    username: str
    message: str
    response: str
    timestamp: datetime

class ChatMessage(BaseModel):
    role: str
    content: str

class AIChatSession(BaseModel):
    session_id: str
    username: str
    start_time: datetime
    history: List[ChatMessage]

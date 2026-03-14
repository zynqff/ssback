from pydantic import BaseModel
from typing import Optional, List

class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    username: str
    is_admin: bool = False
    read_poems_json: List[str] = []
    pinned_poem_title: Optional[str] = None
    show_all_tab: bool = False
    user_data: Optional[str] = None

class UserUpdate(BaseModel):
    new_password: Optional[str] = None
    user_data: Optional[str] = None
    show_all_tab: Optional[bool] = None

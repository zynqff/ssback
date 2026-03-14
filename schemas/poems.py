from pydantic import BaseModel

class PoemCreate(BaseModel):
    title: str
    author: str
    text: str

class PoemResponse(BaseModel):
    title: str
    author: str
    text: str
    line_count: int

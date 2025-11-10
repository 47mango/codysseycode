# model.py
from typing import Optional
from pydantic import BaseModel

class TodoItem(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    done: Optional[bool] = None

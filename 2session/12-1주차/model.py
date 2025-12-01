# model.py
from typing import List
from pydantic import BaseModel

class QuestionCreate(BaseModel):
    title: str
    content: str

class Question(BaseModel):
    id: int
    title: str
    content: str

class QuestionListResponse(BaseModel):
    items: List[Question]
    count: int

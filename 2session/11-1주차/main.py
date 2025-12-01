# domain/question/question_router.py

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import SessionLocal
from models import Question

# --- DB 세션 의존성 ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- 응답용 Pydantic 스키마 ---
class QuestionList(BaseModel):
    id: int
    subject: str
    content: str
    create_date: datetime

    class Config:
        orm_mode = True  # ORM 객체 -> Pydantic 모델 변환 허용


# --- 라우터 정의 ---
router = APIRouter(
    prefix="/api/question",
    tags=["question"],
)


# 목록 조회 라우트
@router.get("/", response_model=List[QuestionList])
def question_list(db: Session = Depends(get_db)):
    """
    질문 목록을 모두 가져오는 API
    - 메소드: GET
    - 경로: /api/question/
    - SQLite 데이터는 SQLAlchemy ORM으로 조회
    """
    questions = db.query(Question).order_by(Question.id.desc()).all()
    return questions

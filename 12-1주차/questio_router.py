# question_router.py
from typing import List
import sqlite3

from fastapi import APIRouter, Depends, HTTPException
from database import get_db_dep  # get_db() 컨텍스트를 감싼 의존성
from model import Question, QuestionCreate, QuestionListResponse

router = APIRouter(prefix="/api", tags=["questions"])


@router.get("/questions", response_model=QuestionListResponse)
def question_list(db: sqlite3.Connection = Depends(get_db_dep)):
    """
    질문 목록 조회 (GET)
    - 매 호출마다 DB OPEN/CLOSE 로그로 확인 가능
    """
    rows = db.execute(
        "SELECT id, title, content FROM questions ORDER BY id DESC"
    ).fetchall()

    items: List[Question] = [
        Question(id=row["id"], title=row["title"], content=row["content"])
        for row in rows
    ]
    return QuestionListResponse(items=items, count=len(items))


# (옵션) 목록만으론 테스트가 어려우니, 생성/단건조회도 포함하면 DB 연결 확인에 유용합니다.

@router.post("/questions", response_model=Question, status_code=201)
def create_question(payload: QuestionCreate, db: sqlite3.Connection = Depends(get_db_dep)):
    cur = db.execute(
        "INSERT INTO questions (title, content) VALUES (?, ?)",
        (payload.title, payload.content),
    )
    db.commit()
    qid = cur.lastrowid
    return Question(id=qid, title=payload.title, content=payload.content)


@router.get("/questions/{qid}", response_model=Question)
def get_question(qid: int, db: sqlite3.Connection = Depends(get_db_dep)):
    row = db.execute(
        "SELECT id, title, content FROM questions WHERE id = ?", (qid,)
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Question not found")
    return Question(id=row["id"], title=row["title"], content=row["content"])

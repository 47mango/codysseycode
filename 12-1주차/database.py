# database.py
import sqlite3
from contextlib import contextmanager
from typing import Iterator

DB_PATH = "app.db"

@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
    """
    contextlib.contextmanager 데코레이터를 사용한 DB 연결 컨텍스트.
    - 진입 시 DB 연결
    - 테이블 초기화
    - 종료 시 자동 close
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    print(f"[DB] OPEN connection id={id(conn)}")

    # 필요 시 테이블 생성
    conn.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL
        )
    """)
    conn.commit()

    try:
        yield conn
    finally:
        conn.close()
        print(f"[DB] CLOSE connection id={id(conn)}")


# FastAPI Depends에서 직접 contextmanager를 쓸 수 없으므로
# contextmanager(get_db)를 한 번 감싼 의존성 함수
def get_db_dep():
    with get_db() as db:
        yield db

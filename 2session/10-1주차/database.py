# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite 데이터베이스 파일 경로 (현재 폴더에 app.db 생성)
SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"

# SQLite에서만 필요한 옵션: 스레드 체크 비활성화
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# autocommit=False, autoflush=False 조건
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# 모든 모델이 상속할 Base 클래스
Base = declarative_base()

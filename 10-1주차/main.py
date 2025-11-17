# main.py
from database import engine
from models import Base

def init_db():
    # Alembic을 쓰지 않을 때는 이렇게 create_all 로도 생성 가능
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("DB 초기화 완료 (테이블 생성 완료)")

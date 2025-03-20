from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite 데이터베이스 URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./paper_review.db"

# 데이터베이스 엔진 생성 (SQLite의 경우 check_same_thread 옵션 필요)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 세션 로컬 클래스 생성: autocommit, autoflush 비활성화
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 베이스 클래스 선언 (모든 모델의 기본 클래스)
Base = declarative_base()

# 의존성 주입 함수: 요청마다 데이터베이스 세션 생성 및 종료 처리
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

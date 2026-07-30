from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:%40Dangerouz11@localhost/Medical_app"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# FastAPI dependency to manage DB sessions per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
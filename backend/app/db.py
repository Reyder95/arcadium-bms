from fastapi import Depends
from typing import Annotated
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    with SessionLocal() as session:
        yield session

DbSession = Annotated[Session, Depends(get_db)]
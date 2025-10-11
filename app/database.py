from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=True)


def get_session():
    return Session(engine)

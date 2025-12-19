import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def make_engine():
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://olympics:olympics@olympics:5432/olympics",
    )
    return create_engine(db_url, echo=False, future=True)

engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

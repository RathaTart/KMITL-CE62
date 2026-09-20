from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker , declarative_base

sqlclhemy_database_url = "sqlite:///./test.db"

engine = create_engine(
    sqlclhemy_database_url, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
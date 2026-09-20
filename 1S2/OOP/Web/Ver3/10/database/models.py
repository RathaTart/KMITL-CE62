from database.database import Base
from sqlalchemy import Column, Integer, String
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=str(uuid.uuid4()))
    username = Column(String, unique=True)
    hashed_password = Column(String)

    